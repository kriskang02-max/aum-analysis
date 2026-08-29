import { useState, useCallback } from 'react'
import Header from './components/Header'
import DailyActions from './components/DailyActions'
import WeeklyEngine from './components/WeeklyEngine'
import MonthlyArchive from './components/MonthlyArchive'
import RoutineSettingsModal from './components/modals/RoutineSettingsModal'
import WeeklyDataModal from './components/modals/WeeklyDataModal'
import ArchiveAddModal from './components/modals/ArchiveAddModal'
import JsonBackupModal from './components/modals/JsonBackupModal'
import { useDashboardStorage } from './hooks/useDashboardStorage'
import { ensureTodayLog } from './utils/storage'

export default function App() {
  const {
    data,
    updateDailyLogs,
    updateWeeklyMetrics,
    updateRoutinePresets,
    updateThoughtArchive,
    replaceAllData,
    refresh,
  } = useDashboardStorage()

  const [routineOpen, setRoutineOpen] = useState(false)
  const [weeklyOpen, setWeeklyOpen] = useState(false)
  const [archiveOpen, setArchiveOpen] = useState(false)
  const [backupOpen, setBackupOpen] = useState(false)

  const handleToggle = useCallback(
    (dateKey, field, value) => {
      updateDailyLogs((logs) => {
        const updated = ensureTodayLog(logs)
        return {
          ...updated,
          [dateKey]: { ...updated[dateKey], [field]: value },
        }
      })
    },
    [updateDailyLogs],
  )

  const handleDeleteArchive = useCallback(
    (id) => {
      updateThoughtArchive((archive) => archive.filter((item) => item.id !== id))
    },
    [updateThoughtArchive],
  )

  return (
    <div className="min-h-screen text-zinc-100">
      <div className="max-w-7xl mx-auto px-4 py-6 md:py-8 space-y-6 md:space-y-8">
        <Header
          dailyLogs={data.daily_logs}
          onOpenRoutine={() => setRoutineOpen(true)}
          onOpenBackup={() => setBackupOpen(true)}
        />

        <DailyActions
          dailyLogs={data.daily_logs}
          routinePresets={data.routine_presets}
          onToggle={handleToggle}
        />

        <WeeklyEngine
          weeklyMetrics={data.weekly_metrics}
          dailyLogs={data.daily_logs}
          onOpenWeeklyModal={() => setWeeklyOpen(true)}
        />

        <MonthlyArchive
          dailyLogs={data.daily_logs}
          weeklyMetrics={data.weekly_metrics}
          thoughtArchive={data.thought_archive}
          onOpenArchiveModal={() => setArchiveOpen(true)}
          onDeleteArchive={handleDeleteArchive}
        />
      </div>

      <RoutineSettingsModal
        open={routineOpen}
        onClose={() => setRoutineOpen(false)}
        presets={data.routine_presets}
        onSave={updateRoutinePresets}
      />

      <WeeklyDataModal
        open={weeklyOpen}
        onClose={() => setWeeklyOpen(false)}
        metrics={data.weekly_metrics}
        onSave={updateWeeklyMetrics}
      />

      <ArchiveAddModal
        open={archiveOpen}
        onClose={() => setArchiveOpen(false)}
        archive={data.thought_archive}
        onSave={updateThoughtArchive}
      />

      <JsonBackupModal
        open={backupOpen}
        onClose={() => setBackupOpen(false)}
        onImport={() => refresh()}
      />
    </div>
  )
}
