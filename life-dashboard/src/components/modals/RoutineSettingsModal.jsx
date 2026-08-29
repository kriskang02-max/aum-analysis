import { useState, useEffect } from 'react'
import Modal from '../Modal'
import { DAY_KEYS, DAY_LABELS } from '../../utils/constants'

export default function RoutineSettingsModal({ open, onClose, presets, onSave }) {
  const [local, setLocal] = useState(presets)

  useEffect(() => {
    if (open) setLocal({ ...presets })
  }, [open, presets])

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="⚙️ 요일별 루틴 설정"
    >
      <div className="space-y-3">
        {DAY_KEYS.map((day) => (
          <label key={day} className="flex items-center gap-3">
            <span className="w-12 text-sm font-medium text-zinc-400">{DAY_LABELS[day]}요일</span>
            <input
              type="text"
              value={local[day] ?? ''}
              onChange={(e) => setLocal((p) => ({ ...p, [day]: e.target.value }))}
              className="flex-1 px-3 py-2 text-sm bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              placeholder="운동 종류 입력"
            />
          </label>
        ))}
        <button
          type="button"
          onClick={() => {
            onSave(local)
            onClose()
          }}
          className="w-full mt-4 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-emerald-600 to-cyan-600 rounded-lg hover:from-emerald-500 hover:to-cyan-500 transition-all"
        >
          저장
        </button>
      </div>
    </Modal>
  )
}
