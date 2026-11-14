// format.js: tiny helpers for showing numbers nicely in the UI.
// Decimals like 0.1234 are treated as fractions and shown as percentages.
// Null values are shown as "N/A".

export function formatPercent(value) {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  const asPercent = value * 100
  return `${asPercent.toFixed(2)}%`
}

export function formatNumber(value) {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  return value.toFixed(2)
}

export function formatSignedPercent(value) {
  // Like formatPercent but always shows a + or - sign (used for "excess" returns).
  if (value === null || value === undefined) {
    return 'N/A'
  }
  const asPercent = value * 100
  const sign = asPercent >= 0 ? '+' : ''
  return `${sign}${asPercent.toFixed(2)}%`
}
