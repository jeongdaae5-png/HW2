# TonePick · AI 퍼스널 컬러 진단

사진을 업로드하면 OpenCV와 Pillow/NumPy로 피부 영역의 RGB·HSV 값을 분석해 퍼스널 컬러 유형과 추천 색상 팔레트를 보여주는 로컬 웹앱입니다.

분석 결과는 조명, 카메라, 이미지 품질에 따라 달라질 수 있는 **추정치**입니다. OpenCV 5 환경에서 레거시 얼굴 검출 API를 사용할 수 없으면 중앙 영역을 대체 분석하며, 화면에 낮은 신뢰도로 표시합니다.

## 요구 환경

- Windows
- Python 3.10 이상 권장
- 일반 CPU로 실행 가능
- 별도 대용량 모델 파일 불필요

## 설치

PowerShell에서 프로젝트 폴더로 이동한 뒤 실행합니다.

```powershell
cd "C:\path\to\personal_color_app"
python -m pip install -r requirements.txt
```

가상환경은 필수가 아닙니다. 권한 오류가 발생하면 사용자 설치를 사용할 수 있습니다.

```powershell
python -m pip install --user -r requirements.txt
```

## 실행

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

브라우저에서 http://127.0.0.1:8000 을 열고 이미지를 선택한 뒤 **이 사진으로 분석하기**를 누릅니다.

## 주요 기능

- 이미지 업로드 및 미리보기
- 이미지 형식·크기 오류 처리
- OpenCV 기반 얼굴 영역 검출 지원
- 피부 톤 RGB·HSV 분석
- 퍼스널 컬러 4종 분류
- 추천 색상 5개와 워스트 컬러 2개 표시
- 분석 결과가 추정치임을 명확하게 표시

## 프로젝트 구조

```text
app.py              FastAPI 서버와 분석 로직
requirements.txt    실행 의존성
static/index.html   화면 구조
static/style.css    화면 스타일
static/app.js       업로드·미리보기·API 연동
```

