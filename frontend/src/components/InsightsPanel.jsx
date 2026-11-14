// InsightsPanel.jsx: a button that asks the backend for a plain-language
// explanation of the numbers, then shows the text (keeping line breaks).
// If the request fails, it shows the error but the rest of the page keeps working.

function InsightsPanel({ insights, disclaimer, loading, error, onExplain }) {
  return (
    <div className="card">
      <h3>Plain-language explanation</h3>

      <button onClick={onExplain} disabled={loading}>
        Explain my results
      </button>

      {loading && <p className="hint">Writing explanation...</p>}

      {error && <p className="error-text">{error}</p>}

      {insights && (
        <div>
          {/* white-space: pre-wrap in CSS keeps the model's line breaks. */}
          <p className="insights-text">{insights}</p>
          <p className="disclaimer">{disclaimer}</p>
        </div>
      )}
    </div>
  )
}

export default InsightsPanel
