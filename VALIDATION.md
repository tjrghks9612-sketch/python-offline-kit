# 준비 PC 검증 기록

검증일: 2026-10-14. 회사 PC에서는 `setup.cmd`가 동일한 검증을 다시 수행합니다.

## 확인한 결과

| 항목 | 결과 |
| --- | --- |
| 공식 Python 3.13.16 Windows x64 EXE | Python.org 게시 SHA-256과 일치, Authenticode 상태 Valid, 서명자 Python Software Foundation |
| 공식 NuGet Python 런타임 | 3.13.16 / win-amd64 / 표준 GIL 빌드 확인 |
| wheel 원본 | 182개 전부 PyPI의 해당 버전·파일 SHA-256과 일치, yanked 아님 |
| 전체 의존성 | 동봉한 wheel만으로 설치, 182개 버전 고정 확인, `pip check` 성공 |
| 직접 선택 모듈 | 52개 모두 import 성공 |
| 기능 검증 | 아래 24개 전부 PASS |
| 설치 재실행 | 기존 키트 환경 재사용 후 전체 검증 PASS, 종료 코드 0 |
| 배포 ZIP 새 설치 | 한글·공백 경로에 새로 압축 해제, Python 사전 설치 없이 시작, 24개 전부 PASS, 종료 코드 0 |
| 한글 경로·출력 | 한글·공백 경로의 Python 실행 및 UTF-8 출력 확인 PASS |
| 설치기 보호 동작 | 아래 회귀 테스트 6개 PASS |
| 정적 검사 | `ruff check tools tests`, `black --check tools tests` 성공 |
| 배포 파일 무결성 | Git 인덱스의 실제 파일 바이트와 SHA256SUMS 전 항목 일치 |

준비 PC 환경: Windows 11 x86-64, OS 빌드 26200. Windows 10 및 회사 PC의
실제 실행 정책은 이 준비 PC에서 재현하지 않았습니다. 기계 판독용 결과는
[validation-summary.json](validation-summary.json)에 있습니다.

## 실제 기능 검증 24개

1. Python 버전·64비트·가상환경·GIL 빌드
2. 고정한 패키지 182개 버전
3. 직접 선택한 모듈 52개 import
4. NumPy/SciPy 연립방정식 계산
5. 한글 Excel 저장·읽기
6. XlsxWriter 생성 후 openpyxl로 읽기
7. Parquet 저장, Polars 읽기, DuckDB 집계
8. scikit-learn 회귀 학습·예측
9. statsmodels 회귀 적합
10. PNG 차트 생성·이미지 크기 확인
11. JavaScript를 내장한 독립 Plotly HTML 생성
12. 한글 Word 문서 저장·읽기
13. 한글 PowerPoint 저장·읽기
14. PDF 생성·텍스트 추출·페이지 PNG 렌더링
15. SQLAlchemy/SQLite 쿼리
16. pyodbc 설치된 드라이버 목록 열거
17. FastAPI 프로세스 내부 요청·응답
18. Beautiful Soup/lxml HTML 파싱
19. YAML/.env/Pydantic/Jinja2 처리
20. cryptography 암호화·복호화
21. 노트북 저장·HTML 변환, 위젯, JupyterLab 실행 파일
22. Windows API 및 COM 초기화
23. pytest/Ruff/Black/mypy 실제 실행
24. 외부 네트워크 차단 확인

## 설치기 보호 동작 테스트 6개

`python -m unittest discover -s tests -v`

- 올바른 파일·체크섬 수락
- 파일 변조 시 거부
- 파일 누락 시 거부
- 체크섬 목록의 상위 경로 접근 거부
- 런타임 ZIP의 상위 경로 접근 거부
- pip에 `--no-index`를 전달하지 않은 경우에도 네트워크 연결 차단

## 검증 범위

실제 Windows 준비 PC에서 이 묶음 전용 런타임과 새 가상환경을 사용했습니다.
인터넷 접속은 온라인 수집·원본 대조에만 사용했고, 설치용 pip는 모든 소켓
연결을 차단한 상태로 실행했습니다. 기능 검증 프로세스는 외부 접속과 DNS를
차단하며 Windows asyncio의 내부 동작에 필요한 loopback 통신을 허용합니다.

업무 DB 접속, Office 앱 제어, 사내 실행 정책, 완전히 초기화된 Windows VM은
검증 범위에 포함하지 않았습니다. pyodbc 검증은 드라이버 목록 열거까지,
pywin32 검증은 Windows API와 COM 초기화까지 수행합니다.

FastAPI의 TestClient 실행 시 Starlette가 기존 httpx 지원의 향후 변경을 안내하는
DeprecationWarning을 출력합니다. 현재 동봉 버전에서 요청·응답 검증은 통과했습니다.
상세 결과는 설치 PC에서 생성하는 `verification-output/verification.json`에 있습니다.
