import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

export default function CardioEfficiencyChart({ metrics }) {
  const sorted = [...metrics].sort((a, b) => a.week - b.week).slice(-8)
  const labels = sorted.map((m) => `${m.week}주`)

  const data = {
    labels,
    datasets: [
      {
        label: '평균 심박 (bpm)',
        data: sorted.map((m) => m.avgHr),
        borderColor: 'rgba(6, 182, 212, 1)',
        backgroundColor: 'rgba(6, 182, 212, 0.1)',
        pointBackgroundColor: 'rgba(6, 182, 212, 1)',
        pointRadius: 4,
        tension: 0.3,
        yAxisID: 'y',
      },
      {
        label: '주행 거리 (km)',
        data: sorted.map((m) => m.distance),
        borderColor: 'rgba(16, 185, 129, 1)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        pointBackgroundColor: 'rgba(16, 185, 129, 1)',
        pointRadius: 4,
        tension: 0.3,
        yAxisID: 'y1',
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        labels: { color: '#a1a1aa', font: { size: 11 } },
      },
      title: {
        display: true,
        text: '심폐 효율성 곡선',
        color: '#e4e4e7',
        font: { size: 13, weight: '600' },
      },
    },
    scales: {
      x: {
        ticks: { color: '#71717a' },
        grid: { color: 'rgba(255,255,255,0.05)' },
      },
      y: {
        type: 'linear',
        position: 'left',
        reverse: false,
        ticks: { color: '#22d3ee' },
        grid: { color: 'rgba(255,255,255,0.05)' },
        title: { display: true, text: '심박 (bpm)', color: '#22d3ee', font: { size: 10 } },
      },
      y1: {
        type: 'linear',
        position: 'right',
        ticks: { color: '#34d399' },
        grid: { drawOnChartArea: false },
        title: { display: true, text: '거리 (km)', color: '#34d399', font: { size: 10 } },
      },
    },
  }

  return (
    <div className="h-64">
      <Line data={data} options={options} />
    </div>
  )
}
