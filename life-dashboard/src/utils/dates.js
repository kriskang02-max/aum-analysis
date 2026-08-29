import { DAY_KEYS, DAY_LABELS } from './constants'

export function formatDateKey(date = new Date()) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function formatDisplayDate(date = new Date()) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const dayLabel = DAY_LABELS[DAY_KEYS[date.getDay()]]
  return `${y}.${m}.${d} ${dayLabel}요일`
}

export function getDayKey(date = new Date()) {
  return DAY_KEYS[date.getDay()]
}

export function getMarathonDDay(marathonDate) {
  const target = new Date(marathonDate + 'T00:00:00')
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diff = Math.ceil((target - today) / (1000 * 60 * 60 * 24))
  if (diff > 0) return { label: `D-${diff}`, days: diff }
  if (diff === 0) return { label: 'D-Day', days: 0 }
  return { label: `D+${Math.abs(diff)}`, days: diff }
}

export function getWeekStart(date = new Date()) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

export function getDaysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate()
}

export function getMonthDays(year, month) {
  const days = getDaysInMonth(year, month)
  const firstDay = new Date(year, month, 1).getDay()
  return { days, firstDay, year, month }
}

export function parseDateKey(key) {
  const [y, m, d] = key.split('-').map(Number)
  return new Date(y, m - 1, d)
}
