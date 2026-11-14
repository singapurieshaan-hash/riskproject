// api.js: small functions that talk to the backend API using fetch.
// The backend URL comes from the VITE_API_URL environment variable.
// Every function throws an Error (with the server's message) if the request fails.

const API_URL = import.meta.env.VITE_API_URL

async function handleResponse(response) {
  // Read the JSON body and throw a helpful error if the status is not OK.
  const data = await response.json()
  if (!response.ok) {
    // The backend sends errors as {"error": "..."} or {"errors": [...]}.
    let message = 'Request failed.'
    if (data.error) {
      message = data.error
    } else if (data.errors) {
      message = data.errors.join(' ')
    }
    throw new Error(message)
  }
  return data
}

export async function getSecurities() {
  const response = await fetch(`${API_URL}/securities`)
  return handleResponse(response)
}

export async function createPortfolio(name, holdings) {
  const response = await fetch(`${API_URL}/portfolios`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, holdings }),
  })
  return handleResponse(response)
}

export async function getAnalysis(portfolioId, years) {
  const response = await fetch(`${API_URL}/portfolios/${portfolioId}/analysis?years=${years}`)
  return handleResponse(response)
}

export async function getInsights(portfolioId, years) {
  const response = await fetch(`${API_URL}/portfolios/${portfolioId}/insights?years=${years}`, {
    method: 'POST',
  })
  return handleResponse(response)
}
