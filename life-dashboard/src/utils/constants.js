export const STORAGE_KEYS = {
  daily_logs: 'daily_logs',
  weekly_metrics: 'weekly_metrics',
  routine_presets: 'routine_presets',
  thought_archive: 'thought_archive',
}

export const MARATHON_DATE = '2026-11-03'

export const DAY_KEYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export const DAY_LABELS = {
  Sun: '일',
  Mon: '월',
  Tue: '화',
  Wed: '수',
  Thu: '목',
  Fri: '금',
  Sat: '토',
}

export const ARCHIVE_TAGS = ['독서', '인사이트', '마인드셋']

export const DAILY_ITEMS = [
  {
    key: 'workout',
    emoji: '🏃',
    label: '오늘의 관절 보호 운동',
    tooltip:
      '크로스핏: 점프류 동작 스텝으로 대체 (박스점프❌, 스텝업⭕) / 러닝: 심박 155 이하 걷뛰로 무릎 충격 분산',
    dynamicLabel: true,
  },
  {
    key: 'diet',
    emoji: '🥗',
    label: '클린 디너 & 야식 차단',
    tooltip:
      '취침 3시간 전 주방 마감 (물 제외 금식), 액상과당/배달음식/야식 절대 금지',
  },
  {
    key: 'dopamine',
    emoji: '📵',
    label: '스크린 & 도파민 리밋',
    tooltip:
      '기상 직후 & 취침 전 각 30~60분 스마트폰 차단, iOS 스크린타임 설정 시간 준수',
  },
  {
    key: 'read',
    emoji: '📖',
    label: '데일리 인지 충전 (20분)',
    tooltip:
      '출퇴근길/틈새 독서 15~20분 또는 코딩/기술 탐구 등 능동적 지적 자극 채우기',
  },
]
