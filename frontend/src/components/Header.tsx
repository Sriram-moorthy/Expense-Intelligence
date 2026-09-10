import React from 'react'
import './Header.css'

export const Header: React.FC = () => {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-icon">EI</div>
        <h1 className="brand-title">Expense Intelligence</h1>
      </div>
      <div className="header-actions">
        <div className="user-profile">
          <div className="user-avatar">US</div>
          <span>User Account</span>
        </div>
      </div>
    </header>
  )
}
