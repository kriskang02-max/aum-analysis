import { useRef, useState } from 'react'
import { Download, Upload } from 'lucide-react'
import Modal from '../Modal'
import { exportAllData, importAllData } from '../../utils/storage'

export default function JsonBackupModal({ open, onClose, onImport }) {
  const fileRef = useRef(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleExport = () => {
    const data = exportAllData()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `life-dashboard-backup-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    setSuccess('백업 파일이 다운로드되었습니다.')
    setError('')
  }

  const handleImport = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        const parsed = JSON.parse(ev.target.result)
        importAllData(parsed)
        onImport()
        setSuccess('데이터가 성공적으로 복원되었습니다.')
        setError('')
      } catch (err) {
        setError('JSON 파일 형식이 올바르지 않습니다.')
        setSuccess('')
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  return (
    <Modal open={open} onClose={onClose} title="JSON 백업 / 복원">
      <div className="space-y-4">
        <p className="text-sm text-zinc-400">
          모든 대시보드 데이터를 JSON 파일로 내보내거나, 이전 백업을 복원할 수 있습니다.
        </p>
        <button
          type="button"
          onClick={handleExport}
          className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-medium text-white bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 transition-colors"
        >
          <Download size={16} />
          JSON 백업 다운로드
        </button>
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-cyan-600 to-indigo-600 rounded-lg hover:from-cyan-500 hover:to-indigo-500 transition-all"
        >
          <Upload size={16} />
          JSON 파일 복원
        </button>
        <input ref={fileRef} type="file" accept=".json" className="hidden" onChange={handleImport} />
        {error && <p className="text-sm text-red-400">{error}</p>}
        {success && <p className="text-sm text-emerald-400">{success}</p>}
      </div>
    </Modal>
  )
}
