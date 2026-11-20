// InsightsPanel.jsx: a button that asks the backend for a plain-language
// explanation of the numbers, then shows it with simple formatting.
// The backend returns plain text: UPPERCASE lines are headings, lines that
// start with "- " are bullet points, everything else is a paragraph.
// If the request fails, it shows the error but the rest of the page keeps working.

// Decide whether a line is a heading. Headings are short, all-capital labels
// like "OVERALL SUMMARY" (letters and spaces only, no lowercase).
function isHeadingLine(line) {
  const trimmed = line.trim()
  if (trimmed.length === 0) {
    return false
  }
  // A heading has no lowercase letters and does contain at least one letter.
  const hasLowercase = /[a-z]/.test(trimmed)
  const hasLetter = /[A-Z]/.test(trimmed)
  return hasLetter && !hasLowercase
}

// Turn the plain-text explanation into formatted React elements.
function renderInsights(text) {
  const lines = text.split('\n')
  const elements = []

  lines.forEach((line, index) => {
    const trimmed = line.trim()

    if (trimmed.length === 0) {
      return
    }

    if (isHeadingLine(trimmed)) {
      // A section heading, shown in bold.
      elements.push(
        <h4 className="insights-heading" key={index}>
          {trimmed}
        </h4>
      )
    } else if (trimmed.startsWith('- ')) {
      // A bullet point. Remove the leading "- " before showing it.
      const bulletText = trimmed.slice(2)
      elements.push(
        <li className="insights-bullet" key={index}>
          {bulletText}
        </li>
      )
    } else {
      // A normal paragraph.
      elements.push(
        <p className="insights-paragraph" key={index}>
          {trimmed}
        </p>
      )
    }
  })

  return elements
}

function InsightsPanel({ insights, disclaimer, loading, error, onExplain }) {
  return (
    <div className="card">
      <h3>Explanation</h3>

      <button onClick={onExplain} disabled={loading}>
        Explain my results
      </button>

      {loading && <p className="hint">Writing explanation...</p>}

      {error && <p className="error-text">{error}</p>}

      {insights && (
        <div className="insights-body">
          {renderInsights(insights)}
          <p className="disclaimer">{disclaimer}</p>
        </div>
      )}
    </div>
  )
}

export default InsightsPanel
