import { Plus, TrendingDown, TrendingUp, Activity, Target } from 'lucide-react'
import BodyCompositionChart from './charts/BodyCompositionChart'
import CardioEfficiencyChart from './charts/CardioEfficiencyChart'
import { countDailyScore } from '../utils/storage'
import { getWeekStart } from '../utils/dates'

export default function WeeklyEngine({ weeklyMetrics, dailyLogs, onOpenWeeklyModal }) {
  const today = new Date()
  const weekStart = getWeekStart(today)
  const weekEnd = new Date(weekStart)
  weekEnd.setDate(weekEnd.getDate() + 6)
  const weekScore = countDailyScore(dailyLogs, weekStart, weekEnd)

  const sorted = [...weeklyMetrics].sort((a, b) => a.week - b.week)
  const latest = sorted[sorted.length - 1]
  const prev = sorted.length > 1 ? sorted[sorted.length - 2] : null

  const bodyFatDelta = latest && prev ? (latest.bodyFat - prev.bodyFat).toFixed(1) : null
  const bodyFatTrend = bodyFatDelta !== null ? (parseFloat(bodyFatDelta) <= 0 ? 'down' : 'up') : null

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
          Weekly Engine & Body Hub
        </h2>
        <button
          type="button"
          onClick={onOpenWeeklyModal}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 rounded-lg hover:bg-cyan-500/20 transition-colors"
        >
          <Plus size={14} />
          주간 데이터 기록
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <KpiCard
          icon={<Target size={18} className="text-emerald-400" />}
          label="이번 주 실천 스코어"
          value={`${weekScore.completed}/${weekScore.total}`}
          sub={`${weekScore.percent}% 달성`}
          accent="emerald"
        />
        <KpiCard
          icon={
            bodyFatTrend === 'down'
              ? <TrendingDown size={18} className="text-emerald-400" />
              : <TrendingUp size={18} className="text-amber-400" />
          }
          label="최신 체지방률"
          value={latest ? `${latest.bodyFat}%` : '—'}
          sub={
            bodyFatDelta !== null
              ? `전주 대비 ${parseFloat(bodyFatDelta) > 0 ? '+' : ''}${bodyFatDelta}%p`
              : '데이터 없음'
          }
          accent={bodyFatTrend === 'down' ? 'emerald' : 'amber'}
        />
        <KpiCard
          icon={<Activity size={18} className="text-cyan-400" />}
          label="유산소 효율 요약"
          value={latest ? `${latest.pace} 페이스` : '—'}
          sub={latest ? `@ 심박 ${latest.avgHr}bpm · ${latest.distance}km` : '데이터 없음'}
          accent="cyan"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card-glow bg-zinc-900/60 border border-zinc-800/60 rounded-xl p-4">
          <BodyCompositionChart metrics={weeklyMetrics} />
        </div>
        <div className="card-glow bg-zinc-900/60 border border-zinc-800/60 rounded-xl p-4">
          <CardioEfficiencyChart metrics={weeklyMetrics} />
        </div>
      </div>
    </section>
  )
}

function KpiCard({ icon, label, value, sub, accent }) {
  const borderColors = {
    emerald: 'border-emerald-500/20',
    cyan: 'border-cyan-500/20',
    amber: 'border-amber-500/20',
  }

  return (
    <div className={`card-glow bg-zinc-900/60 border ${borderColors[accent]} rounded-xl p-4`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs text-zinc-500">{label}</span>
      </div>
      <p className="text-xl font-bold text-zinc-100">{value}</p>
      <p className="text-xs text-zinc-500 mt-1">{sub}</p>
    </div>
  )
}
