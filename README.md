# 사내 Codex용 Python 오프라인 설치 키트

**Windows 10/11 64비트(x86-64) · Python 3.13.16 · 주요 패키지 52개 + 하위 의존성 · 인터넷 없이 설치와 검증**

Python이 없는 PC에서 시작할 수 있습니다. 설치 파일과 Windows용 wheel **182개**가 실제로 이 저장소에 들어 있습니다. GitHub의 **Code → Download ZIP**으로 내려받으면 모두 포함됩니다. Git LFS나 별도 다운로드 링크를 따라갈 필요가 없습니다.

준비일: 2026-10-14. 설치 원본 약 **373 MiB**이며, 압축 해제와 설치·임시 파일을 고려해 여유 공간 **3 GB 이상**을 권장합니다. 정확한 버전은 [PACKAGES.md](PACKAGES.md), 출처·해시는 [packages.json](packages.json)과 [bundle-manifest.json](bundle-manifest.json)에 있습니다.

## 1. 사내로 가져오기

1. 개인 PC에서 이 비공개 저장소에 로그인하고 **Code → Download ZIP**을 누릅니다.
2. ZIP을 회사의 파일 반입 절차에 따라 사내 PC로 옮깁니다.
3. 쓰기 가능한 로컬 폴더에 **전부 압축 해제**합니다. 예: `C:\AXKit`. ZIP 내부나 네트워크 공유 폴더에서 실행하지 마세요.
4. `README.md`, `setup.cmd`, `installers`, `wheels`가 같은 폴더에 있는지 확인합니다.

설치가 끝난 폴더는 그 위치에서 사용합니다. 다른 위치나 다른 PC로 옮길 때는 원본 ZIP을 새 위치에 풀고 다시 설치하세요. `.venv`에는 절대 경로가 기록됩니다.

## 2. 사내 Codex에게 맡기기

이 폴더를 작업 폴더로 열고 다음 문장을 전달하세요.

> 이 폴더의 AGENTS.md와 README.md를 읽고, 동봉된 파일만 사용해 Python 오프라인 환경을 설치하고 검증해줘. setup.cmd --no-pause를 실행하고, verification-output/verification.json에서 모든 검증이 통과했는지 확인해줘. 이후 코드 실행에 사용할 Python 절대 경로와 검증 결과를 알려줘.

[AGENTS.md](AGENTS.md)에 설치·오류 처리·실행 경로 선택 규칙을 적어 두었습니다. 기존 Python, pip, Git, C/C++ 컴파일러가 없어도 기본 설치가 가능합니다.

## 3. 직접 설치하기

**`setup.cmd`를 더블클릭**합니다. 또는 이 폴더의 PowerShell에서 실행합니다.

```powershell
.\setup.cmd --no-pause
```

설치기는 다음 작업을 순서대로 수행합니다.

1. 동봉된 파일들의 SHA-256을 확인합니다.
2. 공식 Python NuGet 배포본을 `.runtime\python-3.13.16`에 압축 해제합니다.
3. 이 폴더에 `.venv` 가상환경을 만듭니다.
4. `wheels`에서 버전·해시가 고정된 전체 의존성을 설치합니다.
5. `pip check`와 **24개 기능 검증**을 실행합니다.

기본 설치는 **관리자 권한이 필요 없으며**, 생성 파일은 이 폴더 안에 있습니다. 설치에는 인터넷을 사용하지 않습니다. pip 설정을 초기화하고 `--no-index`, `--only-binary`, `--require-hashes`를 사용하며, 설치용 pip 프로세스의 네트워크 연결도 차단합니다. 실패하면 종료 코드 1을 반환합니다.

완료 시 `SUCCESS`가 표시되고 다음 파일이 생성됩니다.

| 파일/폴더 | 용도 |
| --- | --- |
| `.runtime\python-3.13.16\python.exe` | 이 키트 전용 Python 원본 |
| `.venv\Scripts\python.exe` | **실제 코드 실행에 사용할 Python** |
| `.runtime-info.json` | 설치한 Python 절대 경로와 검증 완료 시각 |
| `verification-output\verification.json` | 항목별 PASS/FAIL 결과 |
| `verification-output` | 엑셀·Word·PPT·PDF·차트 등 검증 산출물 |
| `logs` | 설치 로그 |

재실행하면 이 키트가 만든 환경을 재사용하고 검증을 다시 수행합니다. 다른 용도로 만든 `.venv`가 이미 있으면 덮어쓰지 않고 중단합니다.

## 4. 코드 실행하기

가장 확실한 방법은 이 환경의 Python을 직접 지정하는 것입니다.

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import pandas; print(pandas.__version__)"
.\.venv\Scripts\python.exe 내스크립트.py
```

현재 PowerShell에서 `python` 명령으로 사용하려면 다음을 실행합니다. 맨 앞의 점과 공백이 필요합니다.

```powershell
. .\activate.ps1
python --version
python 내스크립트.py
```

이 활성화 스크립트는 현재 터미널에 UTF-8 및 로컬 wheel 경로를 설정합니다. 새 터미널에서는 다시 활성화하거나 Python 절대 경로를 사용하세요. 편집기에서도 `이폴더\.venv\Scripts\python.exe`를 인터프리터로 선택합니다.

검증만 다시 하려면 다음을 실행합니다.

```powershell
.\verify.cmd --no-pause
```

JupyterLab은 다음 명령으로 로컬에서 실행할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m jupyterlab --ip=127.0.0.1
```

## 5. 포함된 주요 모듈

| 용도 | 주요 패키지 |
| --- | --- |
| 데이터·통계·머신러닝 | NumPy, pandas, Polars, PyArrow, SciPy, scikit-learn, statsmodels |
| 차트 | Matplotlib, seaborn, Plotly |
| 엑셀 | openpyxl, XlsxWriter, xlrd |
| 문서·PDF·이미지 | python-docx, python-pptx, pypdf, pdfplumber, ReportLab, Pillow |
| DB | DuckDB, SQLAlchemy, pyodbc |
| HTTP·HTML·웹 앱 | requests, httpx, Beautiful Soup, lxml, FastAPI, Uvicorn, Streamlit, Jinja2 |
| 설정·자동화 | PyYAML, python-dotenv, Pydantic, cryptography, pywin32, psutil, Rich, tqdm, Typer, Tenacity, RapidFuzz |
| 노트북 | JupyterLab, ipykernel, ipywidgets, nbconvert |
| 개발 | pytest, pytest-cov, Ruff, Black, mypy, build |

모든 하위 의존성과 pip·setuptools·wheel·packaging도 함께 들어 있습니다. [PACKAGES.md](PACKAGES.md)에서 182개 전체 목록을 확인할 수 있습니다.

검증은 전체 패키지 버전과 직접 선택한 52개 모듈의 import를 확인하고, 한글 엑셀 왕복 저장, Word/PPT 저장·읽기, PDF 생성·텍스트 추출·렌더링, PNG/독립 HTML 차트, Parquet/DB 쿼리, 회귀 모델, 노트북 HTML 변환, Windows COM, 개발 도구 실행을 실제로 수행합니다. 외부 API나 실제 업무 DB에 접속하지 않습니다.

## 6. 설치 범위와 문제 해결

| 증상/필요 기능 | 처리 |
| --- | --- |
| SHA256 mismatch / Missing bundle file | ZIP을 다시 받아 전부 압축 해제합니다. 손상된 파일을 건너뛰지 않습니다. |
| PowerShell 실행이 정책으로 차단됨 | 회사에서 허용한 스크립트 실행 방식이나 서명 절차를 적용합니다. `setup.cmd`의 실행 정책 옵션은 해당 프로세스에만 적용되고 조직의 그룹 정책을 변경하지 않습니다. |
| 실행 파일 자체가 차단됨 | AX/IT 담당자에게 `installers`, `.runtime`의 Python 및 `.venv` 실행 파일 허용을 요청합니다. |
| 경로가 너무 길거나 파일을 만들지 못함 | 쓰기 가능한 짧은 로컬 경로에 새로 풀고 설치합니다. 예: `C:\AXKit`. |
| 설치된 폴더를 옮긴 뒤 실행 실패 | 원본 ZIP을 최종 위치에 새로 풀고 설치합니다. |
| DLL load failed | `logs`와 실패한 모듈명을 확인합니다. PC의 Microsoft Visual C++ x64 런타임 상태를 AX/IT 담당자에게 확인합니다. |
| 사내 DB 연결 | pyodbc는 포함되지만 해당 DB의 ODBC 드라이버·접속 정보는 회사 환경에 맞게 별도 준비해야 합니다. |
| Excel/Word COM 자동화 | pywin32는 포함됩니다. 실제 Office 앱 자동화에는 해당 PC에 Office가 설치되어 있어야 합니다. 일반 파일 생성은 Office 없이 가능합니다. |
| OCR·스캔 PDF | OCR 실행 파일과 언어 모델은 별도입니다. 현재 PDF 검증은 텍스트 PDF 기준입니다. |
| 대형 AI·브라우저 자동화 | PyTorch/TensorFlow, 모델 가중치, Playwright 브라우저, CUDA는 이 기본 묶음에 포함하지 않았습니다. |
| 한글 PDF 또는 차트 글꼴 | Windows의 맑은 고딕 등 사용할 글꼴을 코드에서 지정하세요. 차트 검증은 맑은 고딕이 있으면 사용합니다. |

기본 런타임은 Python의 **공식 NuGet 배포본**이며 pip·venv·표준 라이브러리를 제공합니다. IDLE/Tkinter는 이 배포본에 없습니다. GUI 개발용 Tkinter나 Windows에 등록되는 일반 Python 설치가 필요하면 `installers\python-3.13.16-amd64.exe`를 사용할 수 있습니다. 이 EXE는 기본 설치기가 자동 실행하지 않으며, 별도로 설치한 Python은 기본 키트 환경과 구분해서 사용하세요. 디버그 심볼·free-threaded 등 추가 다운로드가 필요한 선택 항목은 오프라인 기본 설치 범위에 넣지 않았습니다.

## 7. 다른 프로젝트에 별도 가상환경 만들기

아래 예제의 경로를 실제 위치로 바꿉니다. 폴더를 이동할 때의 재설치 규칙은 동일합니다.

```powershell
$kit = 'C:\AXKit'
$project = 'C:\MyProject'
& "$kit\.runtime\python-3.13.16\python.exe" -m venv "$project\.venv"
& "$project\.venv\Scripts\python.exe" -I "$kit\tools\offline_pip.py" --isolated --disable-pip-version-check install --no-index --find-links "$kit\wheels" --only-binary=:all: --require-hashes --no-cache-dir -r "$kit\requirements.lock"
& "$project\.venv\Scripts\python.exe" -I "$kit\tools\offline_pip.py" --isolated --disable-pip-version-check check
```

## 8. 출처·라이선스·유지보수

- Python EXE: [공식 Python 3.13.16 배포 페이지](https://www.python.org/downloads/release/python-31316/). 게시된 SHA-256 및 Python Software Foundation의 유효한 Authenticode 서명을 준비 PC에서 확인했습니다.
- 폴더형 런타임: [Python 공식 Windows 문서의 NuGet 배포 방식](https://docs.python.org/3.13/using/windows.html#the-nuget-org-packages), [python 3.13.16 NuGet 패키지](https://www.nuget.org/packages/python/3.13.16).
- 모듈: PyPI에서 받은 원본 wheel이며 각 SHA-256을 해당 버전의 PyPI 메타데이터와 대조했습니다. 버전·원본 URL·해시·라이선스 메타데이터는 [packages.json](packages.json)에 있습니다.
- [SHA256SUMS](SHA256SUMS)는 반입 중 손상·누락 검사용입니다. 목록과 파일이 함께 바뀌는 경우까지 인증하는 전자서명은 아닙니다.
- 원본 wheel 내부의 라이선스·NOTICE를 유지하고 [licenses](licenses)에도 추출했습니다. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)를 참고하세요.
- 준비 PC의 실제 검증 결과와 범위는 [VALIDATION.md](VALIDATION.md)에 기록합니다. 사내 PC에서는 설치 중 검증을 다시 수행합니다.

인터넷이 되는 유지보수 PC에서만 다음 명령을 사용합니다. 일반 사내 사용자는 실행할 필요가 없습니다.

```powershell
# Windows x64 Python 3.13.16로, 고정된 버전의 설치 원본 다시 받기
python tools/build_bundle.py --download

# 준비된 파일의 PyPI 출처를 다시 검증하고 목록·lock·해시 생성
python tools/build_bundle.py --freeze

# 문서/스크립트 변경 뒤 네트워크 없이 체크섬만 갱신
python tools/build_bundle.py --checksums

# 저장소의 배포 파일만 담은 ZIP 만들기 (.venv/로그/Git 이력 제외)
python tools/build_bundle.py --zip dist/python-offline-kit.zip
```

버전 업데이트는 인터넷이 되는 새 작업 폴더에서 `requirements.in`을 기준으로 다시 수집하고 설치·검증까지 마친 새 묶음으로 반입합니다. 사내 설치기는 패키지의 최신 버전을 검색하거나 내려받지 않습니다.
