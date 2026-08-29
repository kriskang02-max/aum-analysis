import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Chart } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
)

export default function BodyCompositionChart({ metrics }) {
  const sorted = [...metrics].sort((a, b) => a.week - b.week).slice(-8)
  const labels = sorted.map((m) => `${m.week}주`)

  const data = {
    labels,
    datasets: [
      {
        type: 'bar',
        label: '체중 (kg)',
        data: sorted.map((m) => m.weight),
        backgroundColor: 'rgba(99, 102, 241, 0.6)',
        borderColor: 'rgba(99, 102, 241, 1)',
        borderWidth: 1,
        yAxisID: 'y',
        borderRadius: 4,
      },
      {
        type: 'line',
        label: '체지방률 (%)',
        data: sorted.map((m) => m.bodyFat),
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
        text: '신체 구성 변화',
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
        ticks: { color: '#818cf8' },
        grid: { color: 'rgba(255,255,255,0.05)' },
        title: { display: true, text: '체중 (kg)', color: '#818cf8', font: { size: 10 } },
      },
      y1: {
        type: 'linear',
        position: 'right',
        ticks: { color: '#34d399' },
        grid: { drawOnChartArea: false },
        title: { display: true, text: '체지방 (%)', color: '#34d399', font: { size: 10 } },
      },
    },
  }

  return (
    <div className="h-64">
      <Chart type="bar" data={data} options={options} />
    </div>
  )
}
