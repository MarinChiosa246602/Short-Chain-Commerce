import React from 'react'
import { Menu, Sun, Moon, Bell } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

function Header({ sidebarOpen, toggleSidebar }) {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="header">
      <div className="header-left">
        <button className="menu-btn" onClick={toggleSidebar}>
          <Menu size={24} />
        </button>
        <h1 className="logo">
          <span className="logo-icon">📦</span>
          Short Chain Commerce
        </h1>
      </div>

      <div className="header-right">
        <button className="icon-btn" title="Notifications">
          <Bell size={20} />
        </button>
        <button className="icon-btn" onClick={toggleTheme} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <div className="user-avatar">
          <span>SC</span>
        </div>
      </div>
    </header>
  )
}

export default Header
