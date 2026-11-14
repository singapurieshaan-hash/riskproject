// PortfolioBuilder.jsx: lets the user pick stocks and set weights (in percent).
// When the weights add up to 100, the user can click Analyze, which sends
// the holdings (as fractions) up to the parent App via onAnalyze.
import { useState } from 'react'

function PortfolioBuilder({ securities, onAnalyze }) {
  // Each chosen stock: { ticker, weightPercent }.
  const [chosen, setChosen] = useState([])
  // The ticker currently selected in the dropdown.
  const [selectedTicker, setSelectedTicker] = useState('')

  // Tickers already chosen, so we can hide them from the dropdown.
  const chosenTickers = chosen.map((item) => item.ticker)
  const availableSecurities = securities.filter((security) => !chosenTickers.includes(security.ticker))

  // The running total of all weights, used to enable/disable Analyze.
  let totalWeight = 0
  for (const item of chosen) {
    totalWeight = totalWeight + Number(item.weightPercent)
  }
  const totalIsValid = Math.abs(totalWeight - 100) < 0.01
  const canAnalyze = chosen.length >= 1 && totalIsValid

  function addStock() {
    if (!selectedTicker) {
      return
    }
    const newItem = { ticker: selectedTicker, weightPercent: 0 }
    setChosen([...chosen, newItem])
    setSelectedTicker('')
  }

  function removeStock(ticker) {
    const remaining = chosen.filter((item) => item.ticker !== ticker)
    setChosen(remaining)
  }

  function changeWeight(ticker, newWeight) {
    const updated = chosen.map((item) => {
      if (item.ticker === ticker) {
        return { ...item, weightPercent: newWeight }
      }
      return item
    })
    setChosen(updated)
  }

  function setEqualWeight() {
    // Give every stock the same weight, then put the rounding leftover on the first.
    const count = chosen.length
    if (count === 0) {
      return
    }
    const each = Math.round((100 / count) * 100) / 100
    const updated = chosen.map((item) => ({ ...item, weightPercent: each }))
    // Fix the total so it is exactly 100 by adjusting the first stock.
    const sumOfRest = each * count
    const leftover = Math.round((100 - sumOfRest) * 100) / 100
    updated[0] = { ...updated[0], weightPercent: Math.round((each + leftover) * 100) / 100 }
    setChosen(updated)
  }

  function handleAnalyze() {
    // Convert percents to fractions before sending to the parent.
    const holdings = chosen.map((item) => ({
      ticker: item.ticker,
      weight: Number(item.weightPercent) / 100,
    }))
    onAnalyze(holdings)
  }

  return (
    <div className="card builder">
      <h2>Build your portfolio</h2>

      <div className="builder-add">
        <select value={selectedTicker} onChange={(event) => setSelectedTicker(event.target.value)}>
          <option value="">Choose a stock...</option>
          {availableSecurities.map((security) => (
            <option key={security.ticker} value={security.ticker}>
              {security.ticker} - {security.name} ({security.sector})
            </option>
          ))}
        </select>
        <button onClick={addStock} disabled={!selectedTicker}>
          Add
        </button>
        <button onClick={setEqualWeight} disabled={chosen.length === 0}>
          Equal weight
        </button>
      </div>

      {chosen.length === 0 && <p className="hint">Add at least one stock to begin.</p>}

      {chosen.map((item) => (
        <div key={item.ticker} className="holding-row">
          <span className="holding-ticker">{item.ticker}</span>
          <input
            type="number"
            value={item.weightPercent}
            min="0"
            max="100"
            step="0.01"
            onChange={(event) => changeWeight(item.ticker, event.target.value)}
          />
          <span className="percent-sign">%</span>
          <button onClick={() => removeStock(item.ticker)}>Remove</button>
        </div>
      ))}

      {chosen.length > 0 && (
        <p className={totalIsValid ? 'total-ok' : 'total-bad'}>
          Total weight: {totalWeight.toFixed(2)}%
        </p>
      )}

      <button className="analyze-button" onClick={handleAnalyze} disabled={!canAnalyze}>
        Analyze
      </button>
    </div>
  )
}

export default PortfolioBuilder
