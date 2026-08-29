import { Settings, Database } from 'lucide-react'
import { MARATHON_DATE } from '../utils/constants'
import { formatDisplayDate, getMarathonDDay } from '../utils/dates'
import { countDailyScore, ensureTodayLog, getDayCompletionCount } from '../utils/storage'
import { getWeekStart, formatDateKey } from '../utils/dates'

export default function Header({ onOpenRoutine, onOpenBackup, dailyLogs }) {
  const today = new Date()
  const dday = getMarathonDDay(MARATHON_DATE)
  const logs = ensureTodayLog(dailyLogs)
  const todayKey = formatDateKey(today)
  const todayCount = getDayCompletionCount(logs[todayKey])

  const weekStart = getWeekStart(today)
  const weekEnd = new Date(weekStart)
  weekEnd.setDate(weekEnd.getDate() + 6)
  const weekScore = countDailyScore(logs, weekStart, weekEnd)

  const statusBadge =
    todayCount === 4
      ? { text: '🔥 All Clear', className: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' }
      : todayCount >= 2
        ? { text: '⚡ In Progress', className: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30' }
        : { text: '🌱 Start Today', className: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' }

  return (
    <header className="card-glow bg-zinc-900/80 backdrop-blur-md border border-zinc-800/60 rounded-2xl p-4 md:p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
          <div>
            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-0.5">Today</p>
            <h1 className="text-lg md:text-xl font-semibold text-zinc-100">{formatDisplayDate(today)}</h1>
          </div>
          <span className={`inline-flex self-start items-center px-3 py-1 text-xs font-medium rounded-full border ${statusBadge.className}`}>
            {statusBadge.text} · {todayCount}/4
          </span>
        </div>

        <div className="flex justify-center">
          <div className="px-5 py-2.5 bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 rounded-xl">
            <p className="text-center text-sm md:text-base font-semibold text-emerald-400">
              🏃 10km 챌린지 {dday.label}
            </p>
            <p className="text-center text-xs text-zinc-500 mt-0.5">
              이번 주 {weekScore.completed}/{weekScore.total} ({weekScore.percent}%)
            </p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={onOpenRoutine}
            className="flex items-center gap-1.5 px-3 py-2 text-xs md:text-sm font-medium text-zinc-300 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 hover:text-zinc-100 transition-colors"
          >
            <Settings size={15} />
            <span className="hidden sm:inline">루틴 설정</span>
            <span className="sm:hidden">설정</span>
          </button>
          <button
            type="button"
            onClick={onOpenBackup}
            className="flex items-center gap-1.5 px-3 py-2 text-xs md:text-sm font-medium text-zinc-300 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 hover:text-zinc-100 transition-colors"
          >
            <Database size={15} />
            <span className="hidden sm:inline">JSON 백업/복원</span>
            <span className="sm:hidden">백업</span>
          </button>
        </div>
      </div>
    </header>
  )
}
