"""Focused regression checks for offline enforcement and extraction integrity.

Run with Python on the preparation PC: python -m unittest discover -s tests -v
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".work" / "safety-tests"


def ps_quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


class BundleSafety(unittest.TestCase):
    def setUp(self):
        WORK.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=WORK)
        self.folder = Path(self.temp.name).resolve()
        assert self.folder.is_relative_to(WORK.resolve())
        self.addCleanup(self.temp.cleanup)

    def powershell(self, action: str):
        command = f". {ps_quote(ROOT / 'tools/common.ps1')}; try {{ {action} }} catch {{ Write-Output $_.Exception.Message; exit 7 }}"
        return subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )

    def fixture(self):
        lines = []
        payload = []
        for index in range(5):
            name = f"payload-{index}.txt"
            content = f"payload {index}\n".encode()
            (self.folder / name).write_bytes(content)
            digest = hashlib.sha256(content).hexdigest()
            lines.append(f"{digest}  {name}\n")
            payload.append({"path": name, "sha256": digest})
        manifest = json.dumps({"payload": payload}).encode()
        (self.folder / "bundle-manifest.json").write_bytes(manifest)
        lines.append(f"{hashlib.sha256(manifest).hexdigest()}  bundle-manifest.json\n")
        (self.folder / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")

    def test_valid_checksums_accept_exact_bytes(self):
        self.fixture()
        result = self.powershell(f"Test-KitIntegrity -KitRoot {ps_quote(self.folder)}")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Integrity OK", result.stdout)

    def test_corrupted_file_is_rejected(self):
        self.fixture()
        (self.folder / "payload-0.txt").write_bytes(b"modified")
        result = self.powershell(f"Test-KitIntegrity -KitRoot {ps_quote(self.folder)}")
        self.assertEqual(result.returncode, 7)
        self.assertIn("SHA256 mismatch", result.stdout)

    def test_missing_file_is_rejected(self):
        self.fixture()
        (self.folder / "payload-1.txt").unlink()
        result = self.powershell(f"Test-KitIntegrity -KitRoot {ps_quote(self.folder)}")
        self.assertEqual(result.returncode, 7)
        self.assertIn("Missing bundle file", result.stdout)

    def test_checksum_path_escape_is_rejected(self):
        (self.folder / "SHA256SUMS").write_text("0" * 64 + "  ../outside.txt\n", encoding="utf-8")
        result = self.powershell(f"Test-KitIntegrity -KitRoot {ps_quote(self.folder)}")
        self.assertEqual(result.returncode, 7)
        self.assertIn("Checksum path leaves the kit", result.stdout)

    def test_archive_path_escape_is_rejected(self):
        archive = self.folder / "unsafe.nupkg"
        destination = self.folder / "runtime"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("tools/../escape.txt", "do not extract")
        result = self.powershell(
            f"Expand-KitPython -Archive {ps_quote(archive)} -Destination {ps_quote(destination)}"
        )
        self.assertEqual(result.returncode, 7)
        self.assertIn("Unsafe archive entry", result.stdout)
        self.assertFalse((self.folder / "escape.txt").exists())

    def test_offline_pip_blocks_network_even_without_no_index_flag(self):
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                str(ROOT / "tools/offline_pip.py"),
                "--isolated",
                "--disable-pip-version-check",
                "-vv",
                "--retries",
                "0",
                "--timeout",
                "1",
                "install",
                "--dry-run",
                "--no-deps",
                "--ignore-installed",
                "--index-url",
                "https://example.invalid/simple",
                "ax-offline-nonexistent-20261014",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Network access is disabled", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
