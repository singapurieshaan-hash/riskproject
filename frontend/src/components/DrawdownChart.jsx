// DrawdownChart.jsx: a line chart showing how far below its peak each line is.
// Drawdown values are negative decimals (-0.2 means 20% below the peak).
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatPercent } from '../format'

function DrawdownChart({ data }) {
  return (
    <div className="card chart-card">
      <h3>Drawdown (portfolio vs SPY)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" minTickGap={40} />
          <YAxis tickFormatter={formatPercent} />
          <Tooltip formatter={(value) => formatPercent(value)} />
          <Legend />
          <Line
            type="monotone"
            dataKey="portfolio"
            name="Portfolio"
            stroke="#2563eb"
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="benchmark"
            name="SPY"
            stroke="#f59e0b"
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default DrawdownChart
