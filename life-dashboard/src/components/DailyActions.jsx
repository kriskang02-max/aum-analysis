import { Check } from 'lucide-react'
import Tooltip from './Tooltip'
import { DAILY_ITEMS } from '../utils/constants'
import { formatDateKey, getDayKey } from '../utils/dates'
import { ensureTodayLog } from '../utils/storage'

export default function DailyActions({ dailyLogs, routinePresets, onToggle }) {
  const todayKey = formatDateKey()
  const dayKey = getDayKey()
  const logs = ensureTodayLog(dailyLogs)
  const todayLog = logs[todayKey]

  const handleToggle = (key) => {
    onToggle(todayKey, key, !todayLog[key])
  }

  return (
    <section>
      <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
        Daily Actions
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        {DAILY_ITEMS.map((item) => {
          const checked = todayLog[item.key]
          const workoutLabel = item.dynamicLabel
            ? `${item.label} · ${routinePresets[dayKey] ?? '운동'}`
            : item.label

          return (
            <button
              key={item.key}
              type="button"
              onClick={() => handleToggle(item.key)}
              className={`check-card card-glow text-left p-4 rounded-xl border border-zinc-800/80 bg-zinc-900/60 ${checked ? 'checked' : ''}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <Tooltip content={item.tooltip}>
                    <p className="text-sm font-medium text-zinc-200 leading-snug">
                      {item.emoji} {workoutLabel}
                    </p>
                  </Tooltip>
                </div>
                <div
                  className={`flex-shrink-0 w-6 h-6 rounded-md border-2 flex items-center justify-center transition-all ${
                    checked
                      ? 'bg-emerald-500 border-emerald-500 text-white'
                      : 'border-zinc-600 bg-zinc-800/50'
                  }`}
                >
                  {checked && <Check size={14} strokeWidth={3} />}
                </div>
              </div>
              <p className="text-xs text-zinc-500 mt-2">
                {checked ? '완료 ✓' : '클릭하여 완료 표시'}
              </p>
            </button>
          )
        })}
      </div>
    </section>
  )
}
