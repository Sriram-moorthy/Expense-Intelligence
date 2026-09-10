import React from 'react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import './AppShell.css'

interface AppShellProps {
  children: React.ReactNode
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <div className="app-shell">
      <Header />
      <div className="shell-body">
        <Sidebar />
        <main className="main-content">{children}</main>
      </div>
    </div>
  )
}
