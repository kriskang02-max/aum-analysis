# Life & Fitness Dashboard

개인용 라이프 & 피트니스 미니멀 대시보드 (React + Vite + Tailwind CSS)

## 실행 방법

```bash
cd life-dashboard
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

## 빌드

```bash
npm run build
npm run preview
```

## 기능

- **Daily Actions**: 4개 데일리 체크박스 (운동/식단/도파민/독서)
- **Weekly Engine**: KPI 카드 + Chart.js 듀얼 차트 (체중/체지방, 심박/거리)
- **Monthly Archive**: GitHub 스타일 히트맵 + 월간 서머리 + 마인드 아카이브
- **localStorage** 영구 저장 (`daily_logs`, `weekly_metrics`, `routine_presets`, `thought_archive`)
- JSON 백업/복원, 요일별 루틴 설정

## iPad / 모바일에서 보기

GitHub Pages 배포 후 아이패드 Safari에서 접속:

**https://kriskang02-max.github.io/aum-analysis/**

(저장소 Settings → Pages에서 Source를 **GitHub Actions**로 설정해야 최초 1회 활성화됩니다.)

- React 19 + Vite
- Tailwind CSS v4
- Lucide React
- Chart.js + react-chartjs-2
