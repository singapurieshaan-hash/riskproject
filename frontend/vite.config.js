// vite.config.js: Vite build configuration for the React frontend.
// Enables the React plugin so JSX files compile correctly.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
