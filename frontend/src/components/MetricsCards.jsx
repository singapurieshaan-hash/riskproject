// MetricsCards.jsx: shows the headline metrics as a grid of cards.
// Each card shows the portfolio value large and the SPY value small underneath.
// Each card has a title attribute with a plain-language definition on hover.
import { formatNumber, formatPercent, formatSignedPercent } from '../format'

function MetricsCards({ metrics, benchmarkMetrics, comparison }) {
  // Build the list of cards. Each card knows how to show its own value.
  const cards = [
    {
      label: 'Total return',
      title: 'How much the portfolio grew in total over the whole period.',
      portfolio: formatPercent(metrics.total_return),
      benchmark: `SPY: ${formatPercent(benchmarkMetrics.total_return)}`,
    },
    {
      label: 'Annualized return',
      title: 'The average yearly growth rate, assuming it compounded steadily.',
      portfolio: formatPercent(metrics.annualized_return),
      benchmark: `SPY: ${formatPercent(benchmarkMetrics.annualized_return)}`,
    },
    {
      label: 'Annualized volatility',
      title: 'How much the returns swing up and down in a year. Higher means riskier.',
      portfolio: formatPercent(metrics.annualized_volatility),
      benchmark: `SPY: ${formatPercent(benchmarkMetrics.annualized_volatility)}`,
    },
    {
      label: 'Sharpe ratio',
      title: 'Return earned per unit of risk, above the risk-free rate. Higher is better.',
      portfolio: formatNumber(metrics.sharpe_ratio),
      benchmark: `SPY: ${formatNumber(benchmarkMetrics.sharpe_ratio)}`,
    },
    {
      label: 'Maximum drawdown',
      title: 'The worst peak-to-trough drop over the period.',
      portfolio: formatPercent(metrics.max_drawdown),
      benchmark: `SPY: ${formatPercent(benchmarkMetrics.max_drawdown)}`,
    },
    {
      label: 'Beta',
      title: "The portfolio's sensitivity to the market (SPY). 1.0 moves with the market.",
      portfolio: formatNumber(metrics.beta),
      benchmark: 'SPY: 1.00',
    },
    {
      label: '1-day 95% VaR',
      title: 'On a bad day (worst 5%), the loss the portfolio did not exceed historically.',
      portfolio: formatPercent(metrics.var_95_1day),
      benchmark: `SPY: ${formatPercent(benchmarkMetrics.var_95_1day)}`,
    },
  ]

  return (
    <div>
      <div className="cards-grid">
        {cards.map((card) => (
          <div className="card metric-card" key={card.label} title={card.title}>
            <div className="metric-label">{card.label}</div>
            <div className="metric-value">{card.portfolio}</div>
            <div className="metric-benchmark">{card.benchmark}</div>
          </div>
        ))}
      </div>
      <p className="excess-line">
        Excess annualized return vs SPY: {formatSignedPercent(comparison.excess_annualized_return)}
      </p>
    </div>
  )
}

export default MetricsCards
