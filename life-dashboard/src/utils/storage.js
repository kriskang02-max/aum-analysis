import { STORAGE_KEYS } from './constants'
import { formatDateKey } from './dates'

function generateMockDailyLogs() {
  const logs = {}
  const today = new Date()
  for (let i = 59; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const key = formatDateKey(d)
    const rand = Math.random()
    logs[key] = {
      workout: rand > 0.25,
      diet: rand > 0.2,
      dopamine: rand > 0.35,
      read: rand > 0.3,
    }
  }
  return logs
}

export const DEFAULT_ROUTINE_PRESETS = {
  Mon: '크로스핏',
  Tue: '크로스핏',
  Wed: '러닝 35분',
  Thu: '크로스핏',
  Fri: '러닝 35분',
  Sat: '장거리 러닝',
  Sun: '휴식 & 스트레칭',
}

export const DEFAULT_WEEKLY_METRICS = [
  { week: 1, weight: 84.2, bodyFat: 37.2, distance: 3.5, avgHr: 175, pace: '8:10' },
  { week: 2, weight: 83.8, bodyFat: 36.9, distance: 4.0, avgHr: 173, pace: '7:55' },
  { week: 3, weight: 83.5, bodyFat: 36.7, distance: 4.5, avgHr: 171, pace: '7:50' },
  { week: 4, weight: 83.1, bodyFat: 36.5, distance: 5.0, avgHr: 170, pace: '7:45' },
  { week: 5, weight: 82.8, bodyFat: 36.3, distance: 5.5, avgHr: 168, pace: '7:40' },
  { week: 6, weight: 82.5, bodyFat: 36.1, distance: 6.0, avgHr: 167, pace: '7:35' },
  { week: 7, weight: 82.2, bodyFat: 35.8, distance: 6.5, avgHr: 166, pace: '7:32' },
  { week: 8, weight: 82.0, bodyFat: 35.6, distance: 7.0, avgHr: 165, pace: '7:30' },
]

export const DEFAULT_THOUGHT_ARCHIVE = [
  {
    id: 1,
    date: '2026-08-28',
    tag: '독서',
    title: '아토믹 해빗',
    note: '1% 개선의 복리 효과. 작은 습관이 정체기를 돌파한다.',
  },
  {
    id: 2,
    date: '2026-08-25',
    tag: '인사이트',
    title: '심박 존 트레이닝',
    note: 'Zone 2 유산소가 지방 연소와 회복력에 핵심. 155bpm 이하 유지.',
  },
  {
    id: 3,
    date: '2026-08-20',
    tag: '마인드셋',
    title: '프로세스 > 결과',
    note: '체중계 숫자보다 4개 데일리 루틴 완료율에 집중한다.',
  },
  {
    id: 4,
    date: '2026-08-15',
    tag: '독서',
    title: 'Why We Sleep',
    note: '수면 7시간 미만 시 회복과 심박 효율 모두 저하. 야식 차단과 연결.',
  },
]

export function getDefaultData() {
  return {
    daily_logs: generateMockDailyLogs(),
    weekly_metrics: DEFAULT_WEEKLY_METRICS,
    routine_presets: { ...DEFAULT_ROUTINE_PRESETS },
    thought_archive: [...DEFAULT_THOUGHT_ARCHIVE],
  }
}

function readJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    if (raw === null) return fallback
    return JSON.parse(raw)
  } catch {
    return fallback
  }
}

function writeJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

export function loadAllData() {
  const defaults = getDefaultData()
  const hasAny = Object.values(STORAGE_KEYS).some((k) => localStorage.getItem(k) !== null)

  if (!hasAny) {
    writeJSON(STORAGE_KEYS.daily_logs, defaults.daily_logs)
    writeJSON(STORAGE_KEYS.weekly_metrics, defaults.weekly_metrics)
    writeJSON(STORAGE_KEYS.routine_presets, defaults.routine_presets)
    writeJSON(STORAGE_KEYS.thought_archive, defaults.thought_archive)
    return defaults
  }

  return {
    daily_logs: readJSON(STORAGE_KEYS.daily_logs, defaults.daily_logs),
    weekly_metrics: readJSON(STORAGE_KEYS.weekly_metrics, defaults.weekly_metrics),
    routine_presets: readJSON(STORAGE_KEYS.routine_presets, defaults.routine_presets),
    thought_archive: readJSON(STORAGE_KEYS.thought_archive, defaults.thought_archive),
  }
}

export function saveDailyLogs(logs) {
  writeJSON(STORAGE_KEYS.daily_logs, logs)
}

export function saveWeeklyMetrics(metrics) {
  writeJSON(STORAGE_KEYS.weekly_metrics, metrics)
}

export function saveRoutinePresets(presets) {
  writeJSON(STORAGE_KEYS.routine_presets, presets)
}

export function saveThoughtArchive(archive) {
  writeJSON(STORAGE_KEYS.thought_archive, archive)
}

export function exportAllData() {
  return loadAllData()
}

export function importAllData(data) {
  if (!data || typeof data !== 'object') throw new Error('Invalid data format')
  saveDailyLogs(data.daily_logs ?? {})
  saveWeeklyMetrics(data.weekly_metrics ?? [])
  saveRoutinePresets(data.routine_presets ?? DEFAULT_ROUTINE_PRESETS)
  saveThoughtArchive(data.thought_archive ?? [])
}

export function countDailyScore(logs, startDate, endDate) {
  let completed = 0
  let total = 0
  const current = new Date(startDate)
  while (current <= endDate) {
    const key = formatDateKey(current)
    const log = logs[key]
    if (log) {
      total += 4
      completed += [log.workout, log.diet, log.dopamine, log.read].filter(Boolean).length
    }
    current.setDate(current.getDate() + 1)
  }
  return { completed, total, percent: total ? Math.round((completed / total) * 100) : 0 }
}

export function getDayCompletionCount(log) {
  if (!log) return 0
  return [log.workout, log.diet, log.dopamine, log.read].filter(Boolean).length
}

export function ensureTodayLog(logs) {
  const key = formatDateKey()
  if (!logs[key]) {
    return { ...logs, [key]: { workout: false, diet: false, dopamine: false, read: false } }
  }
  return logs
}
