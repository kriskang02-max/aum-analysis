import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { DAILY_ITEMS } from '../utils/constants'
import { getMonthDays, formatDateKey } from '../utils/dates'
import { getDayCompletionCount } from '../utils/storage'

const HEATMAP_COLORS = [
  'bg-zinc-800/80',
  'bg-emerald-900/80',
  'bg-emerald-700/80',
  'bg-emerald-500/80',
  'bg-emerald-400',
]

const TAG_COLORS = {
  독서: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  인사이트: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
  마인드셋: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
}

export default function MonthlyArchive({
  dailyLogs,
  weeklyMetrics,
  thoughtArchive,
  onOpenArchiveModal,
  onDeleteArchive,
}) {
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth()
  const { days, firstDay } = getMonthDays(year, month)

  const monthSummary = computeMonthSummary(dailyLogs, weeklyMetrics, year, month)

  return (
    <section>
      <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
        Monthly Achievement & Archive
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className="lg:col-span-2 card-glow bg-zinc-900/60 border border-zinc-800/60 rounded-xl p-4">
          <p className="text-xs text-zinc-500 mb-3">
            {year}년 {month + 1}월 퀘스트 히트맵
          </p>
          <Heatmap
            year={year}
            month={month}
            days={days}
            firstDay={firstDay}
            dailyLogs={dailyLogs}
          />
          <div className="flex items-center gap-2 mt-3 text-xs text-zinc-500">
            <span>적음</span>
            {HEATMAP_COLORS.map((c, i) => (
              <div key={i} className={`w-3 h-3 rounded-sm ${c}`} />
            ))}
            <span>많음</span>
          </div>
        </div>

        <div className="card-glow bg-zinc-900/60 border border-zinc-800/60 rounded-xl p-4 space-y-4">
          <p className="text-xs text-zinc-500">월간 서머리</p>
          <SummaryRow label="총 운동 일수" value={`${monthSummary.workoutDays}일`} />
          <SummaryRow label="누적 거리" value={`${monthSummary.totalDistance.toFixed(1)} km`} />
          <SummaryRow
            label="체지방 순감소"
            value={
              monthSummary.bodyFatChange !== null
                ? `${monthSummary.bodyFatChange > 0 ? '+' : ''}${monthSummary.bodyFatChange.toFixed(1)}%p`
                : '—'
            }
            highlight={monthSummary.bodyFatChange !== null && monthSummary.bodyFatChange < 0}
          />
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-zinc-300">독서 & 마인드 아카이브</p>
        <button
          type="button"
          onClick={onOpenArchiveModal}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/20 transition-colors"
        >
          <Plus size={14} />
          1줄 기록 추가
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {thoughtArchive.length === 0 ? (
          <p className="col-span-full text-sm text-zinc-500 text-center py-8">
            아직 기록이 없습니다. 첫 인사이트를 추가해보세요.
          </p>
        ) : (
          thoughtArchive.map((item) => (
            <ArchiveCard key={item.id} item={item} onDelete={() => onDeleteArchive(item.id)} />
          ))
        )}
      </div>
    </section>
  )
}

function Heatmap({ year, month, days, firstDay, dailyLogs }) {
  const [tooltip, setTooltip] = useState(null)
  const weekdays = ['일', '월', '화', '수', '목', '금', '토']

  const cells = []
  for (let i = 0; i < firstDay; i++) {
    cells.push(<div key={`empty-${i}`} className="w-full aspect-square" />)
  }
  for (let d = 1; d <= days; d++) {
    const date = new Date(year, month, d)
    const key = formatDateKey(date)
    const log = dailyLogs[key]
    const count = getDayCompletionCount(log)
    const color = HEATMAP_COLORS[count]

    cells.push(
      <div
        key={key}
        className={`heatmap-cell w-full aspect-square rounded-sm ${color} cursor-pointer`}
        onMouseEnter={() => setTooltip({ key, date: key, log, count, x: d })}
        onMouseLeave={() => setTooltip(null)}
        title={buildTooltipText(key, log, count)}
      />
    )
  }

  return (
    <div className="relative">
      <div className="grid grid-cols-7 gap-1 mb-1">
        {weekdays.map((w) => (
          <div key={w} className="text-center text-[10px] text-zinc-600">{w}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">{cells}</div>
      {tooltip && (
        <div className="absolute bottom-full left-0 mb-2 z-10 px-3 py-2 text-xs bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl max-w-xs">
          <p className="font-medium text-zinc-200 mb-1">{tooltip.key}</p>
          <p className="text-zinc-400">{buildTooltipText(tooltip.key, tooltip.log, tooltip.count)}</p>
        </div>
      )}
    </div>
  )
}

function buildTooltipText(key, log, count) {
  if (!log || count === 0) return `${key}: 미완료`
  const items = DAILY_ITEMS.filter((item) => log[item.key]).map((item) => item.emoji + ' ' + item.label.split(' ')[0])
  return `${key}: ${count}/4 — ${items.join(', ') || '없음'}`
}

function SummaryRow({ label, value, highlight }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-zinc-400">{label}</span>
      <span className={`text-sm font-semibold ${highlight ? 'text-emerald-400' : 'text-zinc-200'}`}>
        {value}
      </span>
    </div>
  )
}

function ArchiveCard({ item, onDelete }) {
  const tagClass = TAG_COLORS[item.tag] ?? TAG_COLORS['독서']

  return (
    <div className="card-glow bg-zinc-900/60 border border-zinc-800/60 rounded-xl p-4 group">
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded border ${tagClass}`}>
          {item.tag}
        </span>
        <button
          type="button"
          onClick={onDelete}
          className="opacity-0 group-hover:opacity-100 p-1 text-zinc-500 hover:text-red-400 transition-all"
          aria-label="삭제"
        >
          <Trash2 size={14} />
        </button>
      </div>
      <h3 className="text-sm font-semibold text-zinc-100 mb-1">{item.title}</h3>
      <p className="text-xs text-zinc-400 leading-relaxed line-clamp-3">{item.note}</p>
      <p className="text-[10px] text-zinc-600 mt-2">{item.date}</p>
    </div>
  )
}

function computeMonthSummary(dailyLogs, weeklyMetrics, year, month) {
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  let workoutDays = 0

  for (let d = 1; d <= daysInMonth; d++) {
    const key = formatDateKey(new Date(year, month, d))
    if (dailyLogs[key]?.workout) workoutDays++
  }

  const sorted = [...weeklyMetrics].sort((a, b) => a.week - b.week)
  const totalDistance = sorted.reduce((sum, m) => sum + (m.distance || 0), 0)

  let bodyFatChange = null
  if (sorted.length >= 2) {
    bodyFatChange = sorted[sorted.length - 1].bodyFat - sorted[0].bodyFat
  }

  return { workoutDays, totalDistance, bodyFatChange }
}
