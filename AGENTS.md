# 사내 오프라인 설치 작업 지침

사용자가 이 폴더의 설치·검증을 요청하면 아래 작업을 끝까지 수행한다.

1. `README.md`와 `bundle-manifest.json`을 읽는다. 대상은 Windows 10/11 x86-64, 표준 CPython 3.13.16이다.
2. 이 폴더에서 `setup.cmd --no-pause`를 실행한다. PowerShell에서는 `.\setup.cmd --no-pause`를 사용한다. 프로세스 종료까지 로그를 확인한다.
3. 종료 코드가 0인지 확인한다. `verification-output/verification.json`의 `status`가 `PASS`이고 `failed`가 0인지 확인한다. 실행하지 않은 검증을 통과했다고 보고하지 않는다.
4. `.runtime-info.json`의 `python` 절대 경로를 읽고 이후 Python 실행에 그 경로를 사용한다. 시스템의 `python`, `py`, `pip`가 이 환경을 가리킨다고 가정하지 않는다.
5. 사용자에게 Python 버전·실행 경로·패키지 수·검증 결과와 보고서 위치를 간단히 알린다.

## 설치 범위

- 기본 설치는 이 폴더의 `.runtime`와 `.venv`에 한정한다. 기존 시스템 Python이나 다른 프로젝트 환경을 업그레이드·삭제하지 않는다.
- 기존 Python이 없어도 `setup.cmd`로 시작할 수 있다. NuGet CLI나 EXE 설치기를 따로 실행할 필요가 없다.
- 설치·검증에 인터넷을 사용하지 않는다. 온라인용 `tools/build_bundle.py --download` 및 `--freeze`는 사내 PC에서 실행하지 않는다.
- 일반적인 `pip install 패키지명`, 온라인 인덱스, `curl`/`Invoke-WebRequest`, winget, Microsoft Store로 대체하지 않는다.
- `requirements.lock`, `bootstrap.lock`, `wheels`를 사용한다. 누락·해시 오류를 무시하거나 검증을 생략하지 않는다.
- 이 키트가 만든 가상환경에서 `tools/offline_pip.py`를 실행하면 pip의 네트워크 연결과 외부 설정이 차단된다.
- 패키지가 추가로 필요하면 현재 목록에서 해결 가능한지 먼저 확인한다. 없는 모듈은 인터넷이 되는 준비 PC에서 새 오프라인 묶음에 추가해야 한다고 알린다.

## 실패 시

- 종료 코드와 `logs`의 최신 설치 로그, `verification-output/verification.json`을 확인해 원인을 보고한다.
- 불완전한 `.runtime`, 소유 표식 없는 `.venv`, 이동한 가상환경을 임의 삭제하지 않는다. 로그를 보존하고 원본 ZIP을 새 폴더에 풀어 재시도한다.
- 조직의 스크립트·실행 파일 차단 정책이 있으면 필요한 서명/허용 대상과 실제 오류를 알린다. 정책을 변경하지 않는다.
- 실패를 해결한 뒤 `verify.cmd --no-pause`로 확인한다. 부분 성공을 설치 완료라고 표현하지 않는다.

## 유지보수 PC에서 수정할 때

- 이 지침의 인터넷 금지는 사내 설치 경로에 적용한다. 사용자가 인터넷이 되는 준비 PC에서 묶음의 제작·갱신을 요청한 경우 PyPI 및 공식 배포 사이트에서 원본 수집과 출처 확인을 수행할 수 있다.
- 사용자 요청 범위에서 문서·스크립트를 수정한 뒤 `tools/build_bundle.py --checksums`로 체크섬을 갱신한다.
- 배포에는 `installers`, `wheels`, lock, 목록, 라이선스, 설치·검증 스크립트를 포함한다. `.runtime`, `.venv`, `.work`, 로그, 로컬 검증 산출물은 커밋하지 않는다.
