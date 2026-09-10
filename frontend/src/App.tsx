import React from 'react'
import { AppShell } from './components/AppShell'
import './App.css'

export const App: React.FC = () => {
  return (
    <AppShell>
      <div className="page-header">
        <h2 className="page-title">Dashboard Overview</h2>
        <p className="page-subtitle">Application shell environment ready for V1 feature modules.</p>
      </div>

      <div className="card-grid">
        <div className="shell-card">
          <div className="card-label">Total Income</div>
          <div className="card-value income">$0.00</div>
        </div>

        <div className="shell-card">
          <div className="card-label">Total Expenses</div>
          <div className="card-value expense">$0.00</div>
        </div>

        <div className="shell-card">
          <div className="card-label">Net Balance</div>
          <div className="card-value teal">$0.00</div>
        </div>
      </div>

      <div className="shell-card">
        <div className="card-label">Shell Status</div>
        <p style={{ marginTop: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Header, Sidebar navigation, and Main content area rendered using calm financial design tokens.
        </p>
      </div>
    </AppShell>
  )
}

export default App
