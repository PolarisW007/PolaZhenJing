/**
 * =============================================================================
 * Module: main.tsx
 * Description: React application entry point – renders the App root component.
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * =============================================================================
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
