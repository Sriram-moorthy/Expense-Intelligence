import React from 'react'
import './Sidebar.css'

interface NavItem {
  id: string
  label: string
  active?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', active: true },
  { id: 'transactions', label: 'Transactions' },
  { id: 'categories', label: 'Categories' },
  { id: 'budgets', label: 'Budgets' },
  { id: 'analytics', label: 'Analytics' },
]

export const Sidebar: React.FC = () => {
  return (
    <aside className="app-sidebar">
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <div
            key={item.id}
            className={`nav-item ${item.active ? 'active' : ''}`}
          >
            <span>{item.label}</span>
          </div>
        ))}
      </nav>
    </aside>
  )
}
