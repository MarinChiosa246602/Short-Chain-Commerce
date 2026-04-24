import React from 'react'
import { LayoutDashboard, Upload, History, Settings, FileText, BarChart3, Camera, Package, Bell, Truck, TrendingUp } from 'lucide-react'

function Sidebar({ currentPage, setCurrentPage, isOpen }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'camera', label: 'Camera Scanner', icon: Camera },
    { id: 'products', label: 'Product Inventory', icon: Package },
    { id: 'alerts', label: 'Expiration Alerts', icon: Bell },
    { id: 'routes', label: 'Route Optimization', icon: Truck },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'extraction', label: 'New Extraction', icon: Upload },
    { id: 'history', label: 'History', icon: History },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id

          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setCurrentPage(item.id)}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="version-info">
          <small>v1.0.0</small>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
