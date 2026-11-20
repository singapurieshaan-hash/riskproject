// App.jsx: the single page. It loads the stock list, lets the user build a
// portfolio, runs the analysis, and shows the cards, charts, table, and insights.
// It holds all the shared state and passes pieces down to the child components.
import { useEffect, useState } from 'react'
import { createPortfolio, getAnalysis, getInsights, getSecurities } from './api'
import PortfolioBuilder from './components/PortfolioBuilder'
import MetricsCards from './components/MetricsCards'
import CumulativeChart from './components/CumulativeChart'
import DrawdownChart from './components/DrawdownChart'
import RegressionTable from './components/RegressionTable'
import InsightsPanel from './components/InsightsPanel'

const DISCLAIMER = 'This is educational analysis based on historical data, not investment advice.'

function App() {
  const [securities, setSecurities] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [insights, setInsights] = useState(null)
  const [insightsDisclaimer, setInsightsDisclaimer] = useState(DISCLAIMER)
  const [years, setYears] = useState(5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [portfolioId, setPortfolioId] = useState(null)

  // Insights have their own loading and error state so they do not block the page.
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [insightsError, setInsightsError] = useState('')

  // On first load, fetch the list of securities for the dropdown.
  useEffect(() => {
    async function loadSecurities() {
      try {
        const data = await getSecurities()
        setSecurities(data)
      } catch (loadError) {
        setError(loadError.message)
      }
    }
    loadSecurities()
  }, [])

  // When the period changes and we already have a portfolio, re-run the analysis.
  useEffect(() => {
    if (portfolioId === null) {
      return
    }
    runAnalysis(portfolioId, years)
    // We intentionally only react to year changes here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [years])

  async function runAnalysis(idToUse, yearsToUse) {
    setLoading(true)
    setError('')
    try {
      const data = await getAnalysis(idToUse, yearsToUse)
      setAnalysis(data)
    } catch (analysisError) {
      setError(analysisError.message)
      setAnalysis(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleAnalyze(holdings) {
    // Clear any previous insights when a new portfolio is analyzed.
    setInsights(null)
    setInsightsError('')
    setLoading(true)
    setError('')
    try {
      const created = await createPortfolio('My portfolio', holdings)
      setPortfolioId(created.id)
      await runAnalysis(created.id, years)
    } catch (createError) {
      setError(createError.message)
      setLoading(false)
    }
  }

  async function handleExplain() {
    if (portfolioId === null) {
      return
    }
    setInsightsLoading(true)
    setInsightsError('')
    try {
      const data = await getInsights(portfolioId, years)
      setInsights(data.insights)
      setInsightsDisclaimer(data.disclaimer)
    } catch (explainError) {
      setInsightsError(explainError.message)
    } finally {
      setInsightsLoading(false)
    }
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Portfolio Analytics</h1>
        <p>
          Build a portfolio from US equities and measure its risk and return against
          the S&amp;P&nbsp;500.
        </p>
      </header>

      <PortfolioBuilder securities={securities} onAnalyze={handleAnalyze} />

      {analysis && (
        <div className="period-selector">
          <span>Period</span>
          {[1, 3, 5].map((option) => (
            <button
              key={option}
              className={years === option ? 'period-active' : ''}
              onClick={() => setYears(option)}
            >
              {option} year{option > 1 ? 's' : ''}
            </button>
          ))}
        </div>
      )}

      {loading && <p className="hint">Loading...</p>}
      {error && <p className="error-text">{error}</p>}

      {analysis && !loading && (
        <div>
          <p className="period-info">
            Showing {analysis.period.start_date} to {analysis.period.end_date} (
            {analysis.period.trading_days} trading days).
          </p>

          {analysis.warnings.map((warning) => (
            <p className="warning-text" key={warning}>
              {warning}
            </p>
          ))}

          <MetricsCards
            metrics={analysis.metrics}
            benchmarkMetrics={analysis.benchmark_metrics}
            comparison={analysis.comparison}
          />

          <CumulativeChart data={analysis.charts.cumulative} />
          <DrawdownChart data={analysis.charts.drawdown} />

          <RegressionTable
            securities={analysis.securities}
            holdings={analysis.portfolio.holdings}
          />

          <InsightsPanel
            insights={insights}
            disclaimer={insightsDisclaimer}
            loading={insightsLoading}
            error={insightsError}
            onExplain={handleExplain}
          />
        </div>
      )}

      <footer className="footer">
        <p>{DISCLAIMER}</p>
      </footer>
    </div>
  )
}

export default App
