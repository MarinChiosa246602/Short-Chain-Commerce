import React, { useState, useEffect, useCallback } from 'react'
import { AlertTriangle, Calendar, CheckCircle, Bell, BellOff, Eye, Filter, Download } from 'lucide-react'
import api from '../services/api'

/**
 * Expiration Alerts Component
 * Monitors and displays products nearing expiration with customizable alerts
 */
function ExpirationAlerts() {
  const [alerts, setAlerts] = useState([])
  const [filteredAlerts, setFilteredAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [notificationsEnabled, setNotificationsEnabled] = useState(false)
  const [filterUrgency, setFilterUrgency] = useState('all') // all, critical, warning, info

  // Alert thresholds (days until expiry)
  const THRESHOLDS = {
    CRITICAL: 2,  // 0-2 days - Critical
    WARNING: 7,   // 3-7 days - Warning
    INFO: 14      // 8-14 days - Info
  }

  const fetchExpiringProducts = useCallback(async () => {
    try {
      setLoading(true)

      // Try to get from API first
      try {
        const response = await api.getRecentExtractions(200)

        if (response.results && response.results.length > 0) {
          const allProducts = []
          response.results.forEach(extraction => {
            if (extraction.data && extraction.data.products) {
              extraction.data.products.forEach(product => {
                if (product.expiry_date) {
                  allProducts.push({
                    ...product,
                    extractionId: extraction.id,
                    timestamp: extraction.timestamp
                  })
                }
              })
            }
          })

          generateAlerts(allProducts)
        } else {
          generateAlerts(getMockProducts())
        }
      } catch {
        // Fallback to mock data
        generateAlerts(getMockProducts())
      }

      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch products:', err)
      generateAlerts(getMockProducts())
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchExpiringProducts()
    const interval = setInterval(fetchExpiringProducts, 300000) // Check every 5 minutes
    return () => clearInterval(interval)
  }, [fetchExpiringProducts])

  useEffect(() => {
    applyFilters()
  }, [alerts, filterUrgency])

  const generateAlerts = (products) => {
    const now = new Date()
    const productAlerts = []

    products.forEach(product => {
      const expiryDate = new Date(product.expiry_date)
      const daysUntilExpiry = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24))

      let urgency = null
      let message = ''

      if (daysUntilExpiry < 0) {
        urgency = 'expired'
        message = `EXPIRED ${Math.abs(daysUntilExpiry)} days ago`
      } else if (daysUntilExpiry <= THRESHOLDS.CRITICAL) {
        urgency = 'critical'
        message = `Expires in ${daysUntilExpiry} day${daysUntilExpiry === 1 ? '' : 's'}`
      } else if (daysUntilExpiry <= THRESHOLDS.WARNING) {
        urgency = 'warning'
        message = `Expires in ${daysUntilExpiry} days`
      } else if (daysUntilExpiry <= THRESHOLDS.INFO) {
        urgency = 'info'
        message = `Expires in ${daysUntilExpiry} days`
      }

      if (urgency) {
        productAlerts.push({
          id: product.product_id + product.extractionId + Date.now(),
          product,
          daysUntilExpiry,
          urgency,
          message,
          checked: false
        })
      }
    })

    // Sort by urgency (most urgent first)
    productAlerts.sort((a, b) => {
      const urgencyOrder = { expired: 0, critical: 1, warning: 2, info: 3 }
      return urgencyOrder[a.urgency] - urgencyOrder[b.urgency]
    })

    setAlerts(productAlerts)

    // Send browser notification if enabled and there are critical alerts
    if (notificationsEnabled) {
      const criticalCount = productAlerts.filter(a => a.urgency === 'critical').length
      const expiredCount = productAlerts.filter(a => a.urgency === 'expired').length

      if (criticalCount > 0 || expiredCount > 0) {
        sendBrowserNotification(criticalCount, expiredCount)
      }
    }
  }

  const sendBrowserNotification = (criticalCount, expiredCount) => {
    if (!('Notification' in window)) return

    if (Notification.permission === 'granted') {
      let title = 'Expiration Alert'
      let body = ''

      if (expiredCount > 0 && criticalCount > 0) {
        body = `${expiredCount} expired and ${criticalCount} products expiring soon!`
      } else if (expiredCount > 0) {
        body = `${expiredCount} products have expired. Check inventory immediately.`
      } else {
        body = `${criticalCount} products expiring within 2 days. Immediate action required.`
      }

      new Notification(title, {
        body,
        icon: '/favicon.ico',
        badge: '/favicon.ico'
      })
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          setNotificationsEnabled(true)
        }
      })
    }
  }

  const applyFilters = () => {
    if (filterUrgency === 'all') {
      setFilteredAlerts(alerts)
    } else {
      setFilteredAlerts(alerts.filter(a => a.urgency === filterUrgency))
    }
  }

  const toggleCheck = (id) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === id ? { ...alert, checked: !alert.checked } : alert
    ))
  }

  const getUrgencyIcon = (urgency) => {
    switch (urgency) {
      case 'expired':
        return <AlertTriangle size={20} className="icon-expired" />
      case 'critical':
        return <AlertTriangle size={20} className="icon-critical" />
      case 'warning':
        return <Calendar size={20} className="icon-warning" />
      case 'info':
        return <Calendar size={20} className="icon-info" />
      default:
        return <AlertTriangle size={20} />
    }
  }

  const exportAlerts = () => {
    const csvContent = [
      'Status,Product ID,Product Name,Quantity,Expiry Date,Days Until Expiry,Source'
    ].concat(
      filteredAlerts.map(alert => {
        const status = alert.urgency === 'expired' ? 'EXPIRED' : 'Expiring'
        return [
          status,
          alert.product.product_id,
          `"${alert.product.product_name}"`,
          alert.product.quantity,
          new Date(alert.product.expiry_date).toLocaleDateString(),
          alert.daysUntilExpiry,
          alert.product.source_farm || 'N/A'
        ].join(',')
      })
    ).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `expiration_alerts_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="expiration-alerts">
        <div className="loading-state">Loading alerts...</div>
      </div>
    )
  }

  return (
    <div className="expiration-alerts">
      <div className="alerts-header">
        <div className="alerts-title">
          <Bell size={24} />
          <div>
            <h2>Expiration Alerts</h2>
            <p>Products requiring attention</p>
          </div>
        </div>

        <div className="alerts-actions">
          <button
            className={`notification-toggle ${notificationsEnabled ? 'active' : ''}`}
            onClick={() => {
              if (!notificationsEnabled) {
                if ('Notification' in window && Notification.permission !== 'granted') {
                  Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                      setNotificationsEnabled(true)
                    }
                  })
                } else {
                  setNotificationsEnabled(true)
                }
              } else {
                setNotificationsEnabled(false)
              }
            }}
          >
            {notificationsEnabled ? <Bell size={20} /> : <BellOff size={20} />}
            {notificationsEnabled ? 'Notifications On' : 'Notifications Off'}
          </button>

          <button className="btn-secondary" onClick={exportAlerts}>
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="alerts-summary">
        <div className="summary-card critical">
          <AlertTriangle size={24} />
          <div>
            <span className="number">{alerts.filter(a => a.urgency === 'critical').length}</span>
            <span className="label">Critical</span>
          </div>
        </div>

        <div className="summary-card warning">
          <Calendar size={24} />
          <div>
            <span className="number">{alerts.filter(a => a.urgency === 'warning').length}</span>
            <span className="label">Warning</span>
          </div>
        </div>

        <div className="summary-card info">
          <Calendar size={24} />
          <div>
            <span className="number">{alerts.filter(a => a.urgency === 'info').length}</span>
            <span className="label">Info</span>
          </div>
        </div>

        <div className="summary-card expired">
          <AlertTriangle size={24} />
          <div>
            <span className="number">{alerts.filter(a => a.urgency === 'expired').length}</span>
            <span className="label">Expired</span>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="alerts-filter">
        <Filter size={16} />
        <select
          value={filterUrgency}
          onChange={(e) => setFilterUrgency(e.target.value)}
        >
          <option value="all">All Alerts</option>
          <option value="expired">Expired</option>
          <option value="critical">Critical (0-2 days)</option>
          <option value="warning">Warning (3-7 days)</option>
          <option value="info">Info (8-14 days)</option>
        </select>
        <span className="showing-count">
          Showing {filteredAlerts.length} alert{filteredAlerts.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Alerts List */}
      <div className="alerts-list">
        {filteredAlerts.length === 0 ? (
          <div className="no-alerts">
            <CheckCircle size={48} />
            <h3>No Alerts</h3>
            <p>All products are within safe expiration dates</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-card ${alert.urgency} ${alert.checked ? 'checked' : ''}`}
            >
              <div className="alert-checkbox">
                <input
                  type="checkbox"
                  checked={alert.checked}
                  onChange={() => toggleCheck(alert.id)}
                />
              </div>

              <div className="alert-icon">
                {getUrgencyIcon(alert.urgency)}
              </div>

              <div className="alert-content">
                <div className="alert-header">
                  <span className="product-name">{alert.product.product_name}</span>
                  <span className={`alert-badge ${alert.urgency}`}>
                    {alert.message}
                  </span>
                </div>

                <div className="alert-details">
                  <span className="detail">
                    <strong>SKU:</strong> {alert.product.product_id}
                  </span>
                  <span className="detail">
                    <strong>Quantity:</strong> {alert.product.quantity} {alert.product.unit}
                  </span>
                  <span className="detail">
                    <strong>Source:</strong> {alert.product.source_farm || 'Not specified'}
                  </span>
                  {alert.product.condition && (
                    <span className="detail">
                      <strong>Condition:</strong> {alert.product.condition}
                    </span>
                  )}
                </div>
              </div>

              <div className="alert-actions">
                <button className="view-btn" title="View Details">
                  <Eye size={16} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// Mock data for demonstration
function getMockProducts() {
  const now = Date.now()
  return [
    { product_id: 'PROD-001', product_name: 'Organic Lettuce', quantity: 50, unit: 'piece',
      expiry_date: new Date(now + 1 * 24 * 60 * 60 * 1000).toISOString(), source_farm: 'Green Valley Farm', extractionId: 'ext1' },
    { product_id: 'PROD-002', product_name: 'Fresh Strawberries', quantity: 25, unit: 'box',
      expiry_date: new Date(now + 3 * 24 * 60 * 60 * 1000).toISOString(), source_farm: 'Sunny Fields', extractionId: 'ext2' },
    { product_id: 'PROD-003', product_name: 'Baby Spinach', quantity: 100, unit: 'box',
      expiry_date: new Date(now + 5 * 24 * 60 * 60 * 1000).toISOString(), source_farm: 'Green Valley Farm', extractionId: 'ext3' },
    { product_id: 'PROD-004', product_name: 'Milk', quantity: 40, unit: 'litre',
      expiry_date: new Date(now - 1 * 24 * 60 * 60 * 1000).toISOString(), source_farm: 'Dairy Fresh', extractionId: 'ext4' },
    { product_id: 'PROD-005', product_name: 'Carrots', quantity: 75, unit: 'kg',
      expiry_date: new Date(now + 10 * 24 * 60 * 60 * 1000).toISOString(), source_farm: 'Root Harvest', extractionId: 'ext5' },
    { product_id: 'PROD-006', product_name: 'Tomatoes', quantity: 60, unit: 'kg',
      expiry_date: new Date(now + 6 * 24 * 60 * 60 * 1000).toISOString(), source_farm: 'Sunny Fields', extractionId: 'ext6' },
  ]
}

export default ExpirationAlerts
