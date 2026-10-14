"""ONLINE MAINTAINER TOOL: fetch Windows wheels, freeze versions and record provenance.

Never run this tool on the offline/corporate PC. The normal installer needs no
existing Python and never invokes this file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "3.13.16"
INSTALLERS = {
    "python-3.13.16-amd64.exe": (
        "https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.exe",
        "fb4f9f5d438b2396da0086dc70b935c530cb578e37adc6d354f7ad2037fee83b",
    ),
    "python.3.13.16.nupkg": (
        "https://api.nuget.org/v3-flatcontainer/python/3.13.16/python.3.13.16.nupkg",
        "95fad176338f1d6a799e45946488063f4aa61764e6cff2f132ddeffbf7a04c34",
    ),
}
BOOTSTRAP = {"pip", "setuptools", "wheel", "packaging"}
SKIP_DIRS = {
    ".git",
    ".venv",
    ".runtime",
    ".work",
    "dist",
    "logs",
    "verification-output",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


def download(url: str, path: Path, expected: str) -> None:
    if path.exists():
        if digest(path) != expected:
            raise ValueError(f"Existing artifact has a different hash: {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    if digest(temporary) != expected:
        raise ValueError(f"Upstream hash mismatch: {path.name}")
    temporary.replace(path)


def fetch_wheels() -> None:
    if sys.platform != "win32" or tuple(sys.version_info[:3]) != (3, 13, 16):
        raise RuntimeError("Run --download with standard Windows x64 Python 3.13.16")
    import sysconfig

    if sysconfig.get_platform() != "win-amd64" or sysconfig.get_config_var("Py_GIL_DISABLED"):
        raise RuntimeError("Standard GIL Windows x64 CPython is required")
    for name, (url, expected) in INSTALLERS.items():
        download(url, ROOT / "installers" / name, expected)
    destination = ROOT / "wheels"
    destination.mkdir(exist_ok=True)
    command = [
        sys.executable,
        "-I",
        "-m",
        "pip",
        "--isolated",
        "download",
        "--index-url",
        "https://pypi.org/simple",
        "--only-binary=:all:",
        "--disable-pip-version-check",
        "--no-cache-dir",
        "--dest",
        str(destination),
    ]
    if (ROOT / "requirements.lock").exists():
        command += ["--require-hashes", "-r", str(ROOT / "requirements.lock")]
    else:
        if any(destination.iterdir()):
            raise RuntimeError("For a new resolution use an empty wheels/ folder")
        command += ["-r", str(ROOT / "requirements.in"), *sorted(BOOTSTRAP)]
    subprocess.run(command, check=True, cwd=ROOT)


def read_wheel(path: Path) -> dict:
    if path.stat().st_size >= 100 * 1024 * 1024:
        raise ValueError(f"File exceeds GitHub's regular Git limit: {path.name}")
    with zipfile.ZipFile(path) as archive:
        metadata_names = [
            n for n in archive.namelist() if n.count("/") == 1 and n.endswith(".dist-info/METADATA")
        ]
        if len(metadata_names) != 1:
            raise ValueError(f"Invalid wheel metadata: {path.name}")
        metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))
        name, version = metadata["Name"], metadata["Version"]
        license_id = (
            metadata.get("License-Expression") or metadata.get("License") or "See bundled notices"
        )
        license_id = " ".join(str(license_id).split())[:240]
        license_folder = ROOT / "licenses" / f"{canonical(name)}-{version}"
        dist_prefix = metadata_names[0].rsplit("/", 1)[0] + "/"
        for member in archive.namelist():
            if not member.startswith(dist_prefix) or member.endswith("/"):
                continue
            relative = member[len(dist_prefix) :]
            if not any(word in relative.lower() for word in ("license", "copying", "notice")):
                continue
            target = (license_folder / relative).resolve()
            if not target.is_relative_to(license_folder.resolve()):
                raise ValueError(f"Unsafe license path: {member}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    return {
        "name": name,
        "canonical_name": canonical(name),
        "version": version,
        "filename": path.name,
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
        "license": license_id,
        "requires_python": metadata.get("Requires-Python", ""),
        "requires_dist": metadata.get_all("Requires-Dist", []),
    }


def verify_pypi(record: dict) -> dict:
    metadata_url = f"https://pypi.org/pypi/{record['name']}/{record['version']}/json"
    with urllib.request.urlopen(metadata_url, timeout=60) as response:
        metadata = json.load(response)
    artifacts = [x for x in metadata["urls"] if x["filename"] == record["filename"]]
    if len(artifacts) != 1:
        raise ValueError(f"Wheel not found on PyPI: {record['filename']}")
    artifact = artifacts[0]
    if artifact["digests"]["sha256"] != record["sha256"]:
        raise ValueError(f"PyPI SHA-256 mismatch: {record['filename']}")
    if artifact.get("yanked"):
        raise ValueError(f"Yanked release: {record['filename']}")
    record["source_url"] = artifact["url"]
    record["metadata_url"] = metadata_url
    return record


def freeze(online: bool) -> None:
    wheels = sorted((ROOT / "wheels").glob("*.whl"))
    if not wheels:
        raise RuntimeError("No wheels found. Run --download on the online machine first")
    records = [read_wheel(path) for path in wheels]
    if len({p["canonical_name"] for p in records}) != len(records):
        raise RuntimeError("Multiple versions of a package are present; use a clean wheelhouse")
    if online:
        with ThreadPoolExecutor(max_workers=8) as executor:
            records = list(executor.map(verify_pypi, records))
    else:
        previous = json.loads((ROOT / "packages.json").read_text(encoding="utf-8"))
        known = {p["filename"]: p for p in previous}
        for record in records:
            old = known.get(record["filename"], {})
            if old.get("sha256") != record["sha256"]:
                raise ValueError(f"No verified provenance for {record['filename']}")
            record["source_url"] = old["source_url"]
            record["metadata_url"] = old["metadata_url"]
    records.sort(key=lambda p: p["canonical_name"])
    direct = {
        canonical(line.strip())
        for line in (ROOT / "requirements.in").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    names = {p["canonical_name"] for p in records}
    if not (direct | BOOTSTRAP) <= names:
        raise ValueError(f"Missing direct packages: {(direct | BOOTSTRAP) - names}")
    header = "# Windows x64 / CPython 3.13.16. Generated; all dependencies pinned and hashed.\n"
    for lock_name, selected in (
        ("requirements.lock", records),
        ("bootstrap.lock", [r for r in records if r["canonical_name"] in BOOTSTRAP]),
    ):
        lines = [f"{r['name']}=={r['version']} --hash=sha256:{r['sha256']}" for r in selected]
        (ROOT / lock_name).write_text(
            header + "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
        )
    write_json(ROOT / "packages.json", records)
    table = [
        "# 패키지 목록",
        "",
        "실제 동봉한 버전입니다. 전체 의존성은 requirements.lock에 고정되어 있습니다.",
        "",
        "| 패키지 | 버전 | 구분 | wheel 크기 (MiB) |",
        "| --- | --- | --- | ---: |",
    ]
    for r in records:
        kind = (
            "직접 선택"
            if r["canonical_name"] in direct
            else "설치 도구" if r["canonical_name"] in BOOTSTRAP else "하위 의존성"
        )
        table.append(f"| {r['name']} | {r['version']} | {kind} | {r['bytes']/1048576:.2f} |")
    (ROOT / "PACKAGES.md").write_text("\n".join(table) + "\n", encoding="utf-8", newline="\n")
    license_root = ROOT / "licenses"
    license_root.mkdir(exist_ok=True)
    with zipfile.ZipFile(ROOT / "installers" / "python.3.13.16.nupkg") as z:
        license_names = [
            n for n in z.namelist() if n.lower() in {"tools/license.txt", "license.txt"}
        ]
        for member in license_names:
            (license_root / "PYTHON-LICENSE.txt").write_bytes(z.read(member))
    payload = []
    for path in [
        *(ROOT / "installers").glob("*"),
        *wheels,
        ROOT / "requirements.lock",
        ROOT / "bootstrap.lock",
    ]:
        if not path.is_file() or path.suffix == ".partial":
            continue
        entry = {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        }
        if path.name in INSTALLERS:
            entry["source_url"] = INSTALLERS[path.name][0]
            if entry["sha256"] != INSTALLERS[path.name][1]:
                raise ValueError(f"Installer hash mismatch: {path.name}")
        payload.append(entry)
    runtime_name = f"python.{VERSION}.nupkg"
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target": "Windows 10/11 x86-64; standard GIL CPython",
        "python": {
            "version": VERSION,
            "runtime_path": f"installers/{runtime_name}",
            "runtime_sha256": INSTALLERS[runtime_name][1],
            "full_installer_path": f"installers/python-{VERSION}-amd64.exe",
            "release_page": "https://www.python.org/downloads/release/python-31316/",
        },
        "direct_packages": len(direct),
        "wheel_count": len(records),
        "payload_bytes": sum(p["bytes"] for p in payload),
        "payload": payload,
    }
    write_json(ROOT / "bundle-manifest.json", manifest)
    checksums()
    print(
        json.dumps(
            {
                "wheels": len(records),
                "direct": len(direct),
                "payload_mib": round(manifest["payload_bytes"] / 1048576, 2),
            }
        )
    )


def delivery_files() -> list[Path]:
    return sorted(
        (
            p
            for p in ROOT.rglob("*")
            if p.is_file()
            and not set(p.relative_to(ROOT).parts) & SKIP_DIRS
            and p.name not in {"SHA256SUMS", ".runtime-info.json"}
            and p.suffix not in {".partial", ".pyc", ".pyo"}
        ),
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )


def checksums() -> None:
    paths = delivery_files()
    content = "".join(f"{digest(p)}  {p.relative_to(ROOT).as_posix()}\n" for p in paths)
    (ROOT / "SHA256SUMS").write_text(content, encoding="utf-8", newline="\n")
    print(f"SHA256SUMS: {len(paths)} files")


def make_zip(destination: Path) -> None:
    destination = destination.resolve()
    if destination.is_relative_to(ROOT) and destination.parts[len(ROOT.parts)] != "dist":
        raise ValueError("Place the generated ZIP in dist/ or outside the repository")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1
    ) as archive:
        for path in [*delivery_files(), ROOT / "SHA256SUMS"]:
            archive.write(path, "python-offline-kit/" + path.relative_to(ROOT).as_posix())
    print(
        json.dumps(
            {
                "zip": str(destination),
                "bytes": destination.stat().st_size,
                "sha256": digest(destination),
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Verify every wheel against PyPI and generate manifests",
    )
    parser.add_argument(
        "--refresh-local",
        action="store_true",
        help="Regenerate using previously verified provenance; no network",
    )
    parser.add_argument("--checksums", action="store_true")
    parser.add_argument("--zip", type=Path)
    args = parser.parse_args()
    if args.download:
        fetch_wheels()
    if args.freeze or args.download:
        freeze(online=True)
    elif args.refresh_local:
        freeze(online=False)
    elif args.checksums:
        checksums()
    if args.zip:
        make_zip(args.zip)
    if not any(vars(args).values()):
        parser.print_help()


if __name__ == "__main__":
    main()
