import { useState, useEffect } from 'react'
import Modal from '../Modal'

export default function WeeklyDataModal({ open, onClose, metrics, onSave }) {
  const nextWeek = metrics.length > 0 ? Math.max(...metrics.map((m) => m.week)) + 1 : 1
  const latest = metrics[metrics.length - 1]

  const [form, setForm] = useState({
    week: nextWeek,
    weight: latest?.weight ?? '',
    bodyFat: latest?.bodyFat ?? '',
    distance: latest?.distance ?? '',
    avgHr: latest?.avgHr ?? '',
    pace: latest?.pace ?? '',
  })

  useEffect(() => {
    if (open) {
      setForm({
        week: nextWeek,
        weight: latest?.weight ?? '',
        bodyFat: latest?.bodyFat ?? '',
        distance: latest?.distance ?? '',
        avgHr: latest?.avgHr ?? '',
        pace: latest?.pace ?? '',
      })
    }
  }, [open, nextWeek, latest])

  const handleSubmit = (e) => {
    e.preventDefault()
    const entry = {
      week: Number(form.week),
      weight: Number(form.weight),
      bodyFat: Number(form.bodyFat),
      distance: Number(form.distance),
      avgHr: Number(form.avgHr),
      pace: form.pace,
    }
    const existing = metrics.findIndex((m) => m.week === entry.week)
    let updated
    if (existing >= 0) {
      updated = metrics.map((m, i) => (i === existing ? entry : m))
    } else {
      updated = [...metrics, entry].sort((a, b) => a.week - b.week)
    }
    onSave(updated)
    onClose()
  }

  return (
    <Modal open={open} onClose={onClose} title="➕ 주간 데이터 기록">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="주차" type="number" min={1} max={52} value={form.week}
            onChange={(v) => setForm((p) => ({ ...p, week: v }))} />
          <Field label="체중 (kg)" type="number" step="0.1" value={form.weight}
            onChange={(v) => setForm((p) => ({ ...p, weight: v }))} />
          <Field label="체지방률 (%)" type="number" step="0.1" value={form.bodyFat}
            onChange={(v) => setForm((p) => ({ ...p, bodyFat: v }))} />
          <Field label="주말 러닝 (km)" type="number" step="0.1" value={form.distance}
            onChange={(v) => setForm((p) => ({ ...p, distance: v }))} />
          <Field label="평균 심박 (bpm)" type="number" value={form.avgHr}
            onChange={(v) => setForm((p) => ({ ...p, avgHr: v }))} />
          <Field label="평균 페이스" type="text" placeholder="7:30" value={form.pace}
            onChange={(v) => setForm((p) => ({ ...p, pace: v }))} />
        </div>
        <button
          type="submit"
          className="w-full py-2.5 text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-cyan-600 rounded-lg hover:from-indigo-500 hover:to-cyan-500 transition-all"
        >
          기록 저장
        </button>
      </form>
    </Modal>
  )
}

function Field({ label, type, value, onChange, ...rest }) {
  return (
    <label className="block">
      <span className="text-xs text-zinc-400 mb-1 block">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full px-3 py-2 text-sm bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
        {...rest}
      />
    </label>
  )
}
