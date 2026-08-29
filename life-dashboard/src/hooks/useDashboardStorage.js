import { useCallback, useEffect, useState } from 'react'
import {
  loadAllData,
  saveDailyLogs,
  saveWeeklyMetrics,
  saveRoutinePresets,
  saveThoughtArchive,
} from '../utils/storage'

export function useDashboardStorage() {
  const [data, setData] = useState(() => loadAllData())

  const refresh = useCallback(() => {
    setData(loadAllData())
  }, [])

  useEffect(() => {
    const onStorage = (e) => {
      if (e.key?.startsWith('daily_') || e.key?.startsWith('weekly_') ||
          e.key?.startsWith('routine_') || e.key?.startsWith('thought_')) {
        refresh()
      }
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [refresh])

  const updateDailyLogs = useCallback((updater) => {
    setData((prev) => {
      const next = typeof updater === 'function' ? updater(prev.daily_logs) : updater
      saveDailyLogs(next)
      return { ...prev, daily_logs: next }
    })
  }, [])

  const updateWeeklyMetrics = useCallback((updater) => {
    setData((prev) => {
      const next = typeof updater === 'function' ? updater(prev.weekly_metrics) : updater
      saveWeeklyMetrics(next)
      return { ...prev, weekly_metrics: next }
    })
  }, [])

  const updateRoutinePresets = useCallback((updater) => {
    setData((prev) => {
      const next = typeof updater === 'function' ? updater(prev.routine_presets) : updater
      saveRoutinePresets(next)
      return { ...prev, routine_presets: next }
    })
  }, [])

  const updateThoughtArchive = useCallback((updater) => {
    setData((prev) => {
      const next = typeof updater === 'function' ? updater(prev.thought_archive) : updater
      saveThoughtArchive(next)
      return { ...prev, thought_archive: next }
    })
  }, [])

  const replaceAllData = useCallback((newData) => {
    saveDailyLogs(newData.daily_logs)
    saveWeeklyMetrics(newData.weekly_metrics)
    saveRoutinePresets(newData.routine_presets)
    saveThoughtArchive(newData.thought_archive)
    setData(newData)
  }, [])

  return {
    data,
    updateDailyLogs,
    updateWeeklyMetrics,
    updateRoutinePresets,
    updateThoughtArchive,
    replaceAllData,
    refresh,
  }
}
