import React, { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import Extraction from './components/Extraction'
import History from './components/History'
import Settings from './components/Settings'
import CameraDashboard from './components/CameraDashboard'
import ProductDashboard from './components/ProductDashboard'
import ExpirationAlerts from './components/ExpirationAlerts'
import RouteOptimizer from './components/RouteOptimizer'
import AnalyticsDashboard from './components/AnalyticsDashboard'
import Reports from './components/Reports'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import { ThemeProvider } from './context/ThemeContext'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'camera':
        return <CameraDashboard />
      case 'products':
        return <ProductDashboard />
      case 'alerts':
        return <ExpirationAlerts />
      case 'routes':
        return <RouteOptimizer />
      case 'analytics':
        return <AnalyticsDashboard />
      case 'reports':
        return <Reports />
      case 'extraction':
        return <Extraction />
      case 'history':
        return <History />
      case 'settings':
        return <Settings />
      default:
        return <Dashboard />
    }
  }

  return (
    <ThemeProvider>
      <div className="app">
        <Sidebar
          currentPage={currentPage}
          setCurrentPage={setCurrentPage}
          isOpen={sidebarOpen}
        />
        <div className="main-content">
          <Header
            sidebarOpen={sidebarOpen}
            toggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          />
          <main className="page-content">
            {renderPage()}
          </main>
        </div>
      </div>
    </ThemeProvider>
  )
}

export default App
