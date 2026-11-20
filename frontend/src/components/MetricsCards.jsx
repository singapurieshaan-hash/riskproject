// MetricsCards.jsx: shows the headline metrics as a grid of cards.
// Each card shows the portfolio value large and the SPY value small underneath.
// Each card gets a "tone" (positive / negative / neutral) so the colour of the
// number tells the user at a glance whether the finding is good, bad, or neutral.
// Each card also has a title attribute with a plain-language definition on hover.
import { formatNumber, formatPercent, formatSignedPercent } from '../format'

// Decide the tone for a value that is simply "higher is better" (returns, Sharpe).
function toneHigherIsBetter(value) {
  if (value === null || value === undefined) {
    return 'neutral'
  }
  if (value > 0) {
    return 'positive'
  }
  if (value < 0) {
    return 'negative'
  }
  return 'neutral'
}

function MetricsCards({ metrics, benchmarkMetrics, comparison }) {
  // Build the list of cards. Each card carries its value AND a tone for colour.
  const cards = [
    {
      label: 'Total return',
      title: 'How much the portfolio grew in total over the whole period.',
      portfolio: formatPercent(metrics.total_return),
      benchmark: `SPY ${formatPercent(benchmarkMetrics.total_return)}`,
      // Green if it grew, red if it shrank.
      tone: toneHigherIsBetter(metrics.total_return),
    },
    {
      label: 'Annualized return',
      title: 'The average yearly growth rate, assuming it compounded steadily.',
      portfolio: formatPercent(metrics.annualized_return),
      benchmark: `SPY ${formatPercent(benchmarkMetrics.annualized_return)}`,
      tone: toneHigherIsBetter(metrics.annualized_return),
    },
    {
      label: 'Annualized volatility',
      title: 'How much the returns swing up and down in a year. Higher means riskier.',
      portfolio: formatPercent(metrics.annualized_volatility),
      benchmark: `SPY ${formatPercent(benchmarkMetrics.annualized_volatility)}`,
      // Volatility is just risk, not good or bad on its own: keep it neutral.
      tone: 'neutral',
    },
    {
      label: 'Sharpe ratio',
      title: 'Return earned per unit of risk, above the risk-free rate. Higher is better.',
      portfolio: formatNumber(metrics.sharpe_ratio),
      benchmark: `SPY ${formatNumber(benchmarkMetrics.sharpe_ratio)}`,
      // A positive Sharpe is good; a negative one is bad.
      tone: toneHigherIsBetter(metrics.sharpe_ratio),
    },
    {
      label: 'Maximum drawdown',
      title: 'The worst peak-to-trough drop over the period.',
      portfolio: formatPercent(metrics.max_drawdown),
      benchmark: `SPY ${formatPercent(benchmarkMetrics.max_drawdown)}`,
      // A drawdown is always a loss, so always show it in the warning colour.
      tone: 'negative',
    },
    {
      label: 'Beta',
      title: "The portfolio's sensitivity to the market (SPY). 1.0 moves with the market.",
      portfolio: formatNumber(metrics.beta),
      benchmark: 'SPY 1.00',
      // Beta is a description, not good or bad: neutral.
      tone: 'neutral',
    },
    {
      label: '1-day 95% VaR',
      title: 'On a bad day (worst 5%), the loss the portfolio did not exceed historically.',
      portfolio: formatPercent(metrics.var_95_1day),
      benchmark: `SPY ${formatPercent(benchmarkMetrics.var_95_1day)}`,
      // VaR represents a potential loss, so show it in the warning colour.
      tone: 'negative',
    },
  ]

  // Colour the headline "excess return" line green when we beat SPY, red when we trailed.
  const excessTone = toneHigherIsBetter(comparison.excess_annualized_return)

  return (
    <div>
      <div className="cards-grid">
        {cards.map((card) => (
          <div className="metric-card" key={card.label} title={card.title}>
            <div className="metric-label">{card.label}</div>
            <div className={`metric-value tone-${card.tone}`}>{card.portfolio}</div>
            <div className="metric-benchmark">{card.benchmark}</div>
          </div>
        ))}
      </div>
      <p className="excess-line">
        Excess annualized return vs SPY{' '}
        <span className={`tone-${excessTone}`}>
          {formatSignedPercent(comparison.excess_annualized_return)}
        </span>
      </p>
    </div>
  )
}

export default MetricsCards
