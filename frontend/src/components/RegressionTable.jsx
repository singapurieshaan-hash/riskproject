// RegressionTable.jsx: a table of the per-stock CAPM regression results.
// It joins each security's regression numbers with its weight from the holdings.
import { formatNumber, formatPercent } from '../format'

function RegressionTable({ securities, holdings }) {
  // Build a quick lookup from ticker to its weight.
  const weightByTicker = {}
  for (const holding of holdings) {
    weightByTicker[holding.ticker] = holding.weight
  }

  return (
    <div className="card">
      <h3>Per-stock CAPM regression</h3>
      <table className="regression-table">
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Weight</th>
            <th>Beta</th>
            <th>Alpha (annualized)</th>
            <th>R-squared</th>
            <th>Beta p-value</th>
          </tr>
        </thead>
        <tbody>
          {securities.map((security) => (
            <tr key={security.ticker}>
              <td>{security.ticker}</td>
              <td>{formatPercent(weightByTicker[security.ticker])}</td>
              <td>{formatNumber(security.beta)}</td>
              <td>{formatPercent(security.alpha_annualized)}</td>
              <td>{formatNumber(security.r_squared)}</td>
              <td>{formatNumber(security.beta_p_value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="table-note">
        Beta is each stock's sensitivity to SPY. R-squared shows how much of the stock's movement is
        explained by the market. Estimated from daily returns.
      </p>
    </div>
  )
}

export default RegressionTable
