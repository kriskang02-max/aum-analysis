import { useState } from 'react'
import Modal from '../Modal'
import { ARCHIVE_TAGS } from '../../utils/constants'
import { formatDateKey } from '../../utils/dates'

export default function ArchiveAddModal({ open, onClose, archive, onSave }) {
  const [form, setForm] = useState({ tag: '독서', title: '', note: '' })

  const reset = () => setForm({ tag: '독서', title: '', note: '' })

  const handleSubmit = (e) => {
    e.preventDefault()
    const maxId = archive.reduce((max, item) => Math.max(max, item.id), 0)
    const entry = {
      id: maxId + 1,
      date: formatDateKey(),
      tag: form.tag,
      title: form.title.trim(),
      note: form.note.trim(),
    }
    onSave([entry, ...archive])
    reset()
    onClose()
  }

  return (
    <Modal open={open} onClose={onClose} title="➕ 1줄 기록 추가">
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block">
          <span className="text-xs text-zinc-400 mb-1 block">태그</span>
          <select
            value={form.tag}
            onChange={(e) => setForm((p) => ({ ...p, tag: e.target.value }))}
            className="w-full px-3 py-2 text-sm bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
          >
            {ARCHIVE_TAGS.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-xs text-zinc-400 mb-1 block">제목</span>
          <input
            type="text"
            value={form.title}
            onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
            required
            className="w-full px-3 py-2 text-sm bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
            placeholder="책 제목, 주제 등"
          />
        </label>
        <label className="block">
          <span className="text-xs text-zinc-400 mb-1 block">메모 (1~3줄)</span>
          <textarea
            value={form.note}
            onChange={(e) => setForm((p) => ({ ...p, note: e.target.value }))}
            required
            rows={3}
            className="w-full px-3 py-2 text-sm bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 resize-none"
            placeholder="핵심 인사이트를 기록하세요"
          />
        </label>
        <button
          type="submit"
          className="w-full py-2.5 text-sm font-medium text-white bg-gradient-to-r from-emerald-600 to-indigo-600 rounded-lg hover:from-emerald-500 hover:to-indigo-500 transition-all"
        >
          추가
        </button>
      </form>
    </Modal>
  )
}
