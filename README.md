# 수탁고 증감 분석 대시보드

운용사별 공모·사모·투자일임 수탁고(설정규모 **합계**, 단위: 억원)를 엑셀에서 읽어 기준일·유형·운용사별 증감을 분석하는 Streamlit 대시보드입니다.

## 데이터 파일 규칙

| 접두어 | 유형 |
|--------|------|
| `공모_` | 공모펀드 |
| `사모_` | 사모펀드 |
| `일임_` | 투자일임 |

파일명 예: `공모_251231.xlsx` → 2025-12-31 기준

- 위치: 프로젝트 **루트** 또는 `data/` 폴더
- 시트: `회사별설정규모` (첫 시트)
- 사용 컬럼: `회사명`, `합계` (단위: 일억원)

## 로컬 실행

```powershell
cd "C:\Users\infomax\Documents\AUM Analysis"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 이 열립니다.

## 대시보드 기능

- **전체 수탁고**: 유형별 수탁고 추이, 기준일→비교일 유형별 증감
- **TOP20 비교**: 비교일 기준 상위 20개사 순위·유형별 분석
- **운용사별 수탁고**: 선택 운용사 시계열·CEO 요약·기간 증감
- **운용사 비교**: 두 운용사 유형별 비교
- **상세 데이터**: 직전 기준일 대비 증감, CSV 다운로드

페이지 상단에서 기준일·비교일·유형·자산을 필터링합니다.

## 배포 (Streamlit Community Cloud)

엑셀 데이터는 `data/*.xlsx`에 두고 Git에 포함합니다(루트 `*.xlsx`는 무시).

1. GitHub에 **비공개** 저장소 생성 후 푸시
2. [share.streamlit.io](https://share.streamlit.io) 로그인 → **New app**
3. Repository / branch 선택, **Main file path**: `app.py`
4. **Deploy** → URL 예: `https://<앱이름>.streamlit.app`

```powershell
cd "C:\Users\infomax\Documents\AUM Analysis"
git init
git add .
git commit -m "Deploy AUM analysis dashboard"
git remote add origin https://github.com/<계정>/<저장소>.git
git push -u origin main
```

## 로컬·사내망 공개

```powershell
.\publish.ps1
```

브라우저: `http://localhost:8501` (같은 네트워크: `http://<PC-IP>:8501`)

## 엑셀 변경 → 사이트 자동 반영

프로젝트 **루트**에 `공모_YYMMDD.xlsx` 등을 추가·수정한 뒤:

| 파일 | 용도 |
|------|------|
| **`sync_deploy.bat`** | 1회 실행: 루트 엑셀 → `data/` 복사 → GitHub 푸시 (Streamlit Cloud 재배포) |
| **`sync_deploy_watch.bat`** | 5분마다 변경 여부 확인 후 자동 푸시 (창을 켜 둠) |

로그: `logs/sync_deploy.log`

**최초 1회:** GitHub 로그인(푸시 권한)이 되어 있어야 합니다.  
저장소: `https://github.com/kriskang02-max/aum-analysis`

Windows 작업 스케줄러로 `sync_deploy.bat`을 매일/매시간 실행해도 됩니다.

새 기준일 엑셀은 **루트 또는 `data/`**에 두면 됩니다. 배치가 루트 → `data/`를 맞춘 뒤 푸시합니다.
