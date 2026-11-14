// main.jsx: the entry point for the React app.
// It finds the <div id="root"> in index.html and renders <App /> into it.
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './App.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
