// CumulativeChart.jsx: a line chart of cumulative return for the portfolio vs SPY.
// The data comes in as decimals (0.05 means +5%), so we format the axis and
// tooltip as percentages.
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

function CumulativeChart({ data }) {
  return (
    <div className="card chart-card">
      <h3>Cumulative return</h3>
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
            stroke="#1a1a1a"
            strokeWidth={1.6}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="benchmark"
            name="SPY"
            stroke="#b0b0ac"
            strokeWidth={1.6}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default CumulativeChart
