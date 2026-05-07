import React, { useState, useEffect, useCallback } from 'react'
import {
  Package, Calendar, Thermometer, Download, Filter, Search,
  AlertTriangle, CheckCircle, Clock, Truck, MapPin, Eye,
  ChevronDown, ChevronUp, RefreshCw, FileSpreadsheet, FileText, Printer
} from 'lucide-react'
import api, { getInventory } from '../services/api'

function ProductDashboard() {
  const [products, setProducts] = useState([])
  const [filteredProducts, setFilteredProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filter states
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState('all') // all, expiring, expired, good-condition
  const [filterStorage, setFilterStorage] = useState('all')
  const [sortBy, setSortBy] = useState('expiryDate')
  const [sortOrder, setSortOrder] = useState('asc')

  // Selected products for batch operations
  const [selectedProducts, setSelectedProducts] = useState([])
  const [showExportModal, setShowExportModal] = useState(false)

  // Dashboard stats
  const [stats, setStats] = useState({
    totalProducts: 0,
    expiringSoon: 0,
    expired: 0,
    goodCondition: 0,
    totalValue: 0
  })

  const fetchProducts = useCallback(async () => {
    try {
      setLoading(true)
      // Use the new inventory API which returns pre-aggregated data
      const response = await getInventory()

      if (response.products && response.products.length > 0) {
        setProducts(response.products)
      } else {
        // Mock data for demonstration
        setProducts(getMockProducts())
      }

      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch products:', err)
      // Use mock data on error
      setProducts(getMockProducts())
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProducts()
    const interval = setInterval(fetchProducts, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [fetchProducts])

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...products]

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(p =>
        p.product_name?.toLowerCase().includes(query) ||
        p.product_id?.toLowerCase().includes(query) ||
        p.source_farm?.toLowerCase().includes(query)
      )
    }

    // Status filter
    const now = new Date()
    if (filterStatus === 'expiring') {
      filtered = filtered.filter(p => {
        if (!p.expiry_date) return false
        const expiry = new Date(p.expiry_date)
        const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24)
        return daysUntilExpiry > 0 && daysUntilExpiry <= 7
      })
    } else if (filterStatus === 'expired') {
      filtered = filtered.filter(p => {
        if (!p.expiry_date) return false
        return new Date(p.expiry_date) < now
      })
    } else if (filterStatus === 'good-condition') {
      filtered = filtered.filter(p =>
        p.condition === 'excellent' || p.condition === 'good'
      )
    }

    // Storage filter
    if (filterStorage !== 'all') {
      filtered = filtered.filter(p => {
        const storageType = getStorageType(p.product_name)?.type
        return storageType === filterStorage
      })
    }

    // Sorting
    filtered.sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'expiryDate':
          if (!a.expiry_date) comparison = 1
          else if (!b.expiry_date) comparison = -1
          else comparison = new Date(a.expiry_date) - new Date(b.expiry_date)
          break
        case 'name':
          comparison = (a.product_name || '').localeCompare(b.product_name || '')
          break
        case 'condition':
          comparison = (a.condition || '').localeCompare(b.condition || '')
          break
        case 'quantity':
          comparison = (a.quantity || 0) - (b.quantity || 0)
          break
        case 'source':
          comparison = (a.source_farm || '').localeCompare(b.source_farm || '')
          break
        default:
          comparison = 0
      }

      return sortOrder === 'desc' ? -comparison : comparison
    })

    setFilteredProducts(filtered)

    // Update stats
    const expiryThreshold = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
    setStats({
      totalProducts: products.length,
      expiringSoon: products.filter(p => {
        if (!p.expiry_date) return false
        const expiry = new Date(p.expiry_date)
        const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24)
        return daysUntilExpiry > 0 && daysUntilExpiry <= 7
      }).length,
      expired: products.filter(p => {
        if (!p.expiry_date) return false
        return new Date(p.expiry_date) < now
      }).length,
      goodCondition: products.filter(p =>
        p.condition === 'excellent' || p.condition === 'good'
      ).length,
      totalValue: products.reduce((sum, p) => sum + (p.quantity || 0), 0)
    })
  }, [products, searchQuery, filterStatus, filterStorage, sortBy, sortOrder])

  const toggleProductSelection = (productId) => {
    setSelectedProducts(prev => {
      if (prev.includes(productId)) {
        return prev.filter(id => id !== productId)
      }
      return [...prev, productId]
    })
  }

  const selectAllProducts = () => {
    if (selectedProducts.length === filteredProducts.length) {
      setSelectedProducts([])
    } else {
      setSelectedProducts(filteredProducts.map(p => p.product_id + p.extractionId))
    }
  }

  const exportToCSV = () => {
    const headers = [
      'Product ID', 'Product Name', 'Quantity', 'Unit',
      'Expiry Date', 'Condition', 'Source Farm', 'Destination',
      'Storage Type', 'Temperature', 'Humidity'
    ]

    const rows = filteredProducts.map(p => {
      const storage = getStorageType(p.product_name)
      return [
        p.product_id,
        p.product_name,
        p.quantity,
        p.unit,
        p.expiry_date ? new Date(p.expiry_date).toLocaleDateString() : 'N/A',
        p.condition || 'N/A',
        p.source_farm || 'N/A',
        p.destination || 'N/A',
        storage.type,
        storage.temp,
        storage.humidity
      ].map(field => `"${field}"`).join(',')
    })

    const csvContent = [headers.join(','), ...rows].join('\n')
    downloadFile(csvContent, `products_export_${Date.now()}.csv`)
  }

  const exportToJSON = () => {
    const dataStr = JSON.stringify(filteredProducts, null, 2)
    downloadFile(dataStr, `products_export_${Date.now()}.json`)
  }

  const exportToExcel = () => {
    // Excel export using simple HTML table format
    const htmlContent = `
      <table border="1">
        <thead>
          <tr>
            <th>Product ID</th>
            <th>Product Name</th>
            <th>Quantity</th>
            <th>Unit</th>
            <th>Expiry Date</th>
            <th>Condition</th>
            <th>Source Farm</th>
            <th>Destination</th>
            <th>Storage Type</th>
            <th>Temperature</th>
            <th>Humidity</th>
          </tr>
        </thead>
        <tbody>
          ${filteredProducts.map(p => {
            const storage = getStorageType(p.product_name)
            return `
          <tr>
            <td>${p.product_id}</td>
            <td>${p.product_name}</td>
            <td>${p.quantity}</td>
            <td>${p.unit}</td>
            <td>${p.expiry_date ? new Date(p.expiry_date).toLocaleDateString() : 'N/A'}</td>
            <td>${p.condition || 'N/A'}</td>
            <td>${p.source_farm || 'N/A'}</td>
            <td>${p.destination || 'N/A'}</td>
            <td>${storage.type}</td>
            <td>${storage.temp}</td>
            <td>${storage.humidity}</td>
          </tr>`
          }).join('')}
        </tbody>
      </table>
    `

    const blob = new Blob([htmlContent], { type: 'application/vnd.ms-excel' })
    downloadFile(URL.createObjectURL(blob), `products_export_${Date.now()}.xls`)
  }

  const downloadFile = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const printReport = () => {
    window.print()
  }

  if (loading) {
    return (
      <div className="product-dashboard">
        <div className="loading-state">
          <RefreshCw className="spin" size={32} />
          <p>Loading products...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="product-dashboard">
      <div className="dashboard-header">
        <h1>Product Inventory Dashboard</h1>
        <p className="subtitle">Track products, expiration dates, and storage conditions</p>
      </div>

      {/* Stats Cards */}
      <div className="product-stats">
        <div className="stat-card">
          <div className="stat-icon blue">
            <Package size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-label">Total Products</span>
            <span className="stat-value">{stats.totalProducts}</span>
          </div>
        </div>

        <div className="stat-card warning">
          <div className="stat-icon">
            <AlertTriangle size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-label">Expiring Soon</span>
            <span className="stat-value">{stats.expiringSoon}</span>
          </div>
        </div>

        <div className="stat-card danger">
          <div className="stat-icon">
            <Clock size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-label">Expired</span>
            <span className="stat-value">{stats.expired}</span>
          </div>
        </div>

        <div className="stat-card success">
          <div className="stat-icon">
            <CheckCircle size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-label">Good Condition</span>
            <span className="stat-value">{stats.goodCondition}</span>
          </div>
        </div>
      </div>

      {/* Filters and Actions */}
      <div className="dashboard-controls">
        <div className="search-filters">
          <div className="search-box">
            <Search size={20} />
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <Filter size={16} />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">All Products</option>
              <option value="expiring">Expiring in 7 Days</option>
              <option value="expired">Expired</option>
              <option value="good-condition">Good Condition</option>
            </select>
          </div>

          <div className="filter-group">
            <Thermometer size={16} />
            <select
              value={filterStorage}
              onChange={(e) => setFilterStorage(e.target.value)}
            >
              <option value="all">All Storage Types</option>
              <option value="Refrigerated">Refrigerated</option>
              <option value="Cold Storage">Cold Storage</option>
              <option value="Cool Storage">Cool Storage</option>
              <option value="Dry Storage">Dry Storage</option>
              <option value="Room Temperature">Room Temperature</option>
            </select>
          </div>
        </div>

        <div className="action-buttons">
          <div className="sort-group">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="expiryDate">Sort by Expiry</option>
              <option value="name">Sort by Name</option>
              <option value="condition">Sort by Condition</option>
              <option value="quantity">Sort by Quantity</option>
              <option value="source">Sort by Source</option>
            </select>
            <button
              className="sort-order-btn"
              onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
            >
              {sortOrder === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>

          <button className="btn-primary" onClick={fetchProducts}>
            <RefreshCw size={16} />
            Refresh
          </button>

          <div className="dropdown">
            <button className="btn-secondary" onClick={() => setShowExportModal(!showExportModal)}>
              <Download size={16} />
              Export
              <ChevronDown size={16} />
            </button>

            {showExportModal && (
              <div className="dropdown-menu">
                <button onClick={() => { exportToCSV(); setShowExportModal(false); }}>
                  <FileText size={16} />
                  Export as CSV
                </button>
                <button onClick={() => { exportToJSON(); setShowExportModal(false); }}>
                  <FileText size={16} />
                  Export as JSON
                </button>
                <button onClick={() => { exportToExcel(); setShowExportModal(false); }}>
                  <FileSpreadsheet size={16} />
                  Export as Excel
                </button>
                <button onClick={() => { printReport(); setShowExportModal(false); }}>
                  <Printer size={16} />
                  Print Report
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Products Table */}
      <div className="products-table-container">
        <table className="products-table">
          <thead>
            <tr>
              <th className="select-col">
                <input
                  type="checkbox"
                  checked={selectedProducts.length === filteredProducts.length && filteredProducts.length > 0}
                  onChange={selectAllProducts}
                />
              </th>
              <th>Product</th>
              <th>Quantity</th>
              <th>Expiry Date</th>
              <th>Condition</th>
              <th>Source</th>
              <th>Storage</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.length === 0 ? (
              <tr>
                <td colSpan="8" className="empty-message">
                  <Package size={48} />
                  <p>No products found</p>
                  <p>Scan products using the Camera Scanner or upload images</p>
                </td>
              </tr>
            ) : (
              filteredProducts.map((product) => {
                const storage = getStorageType(product.product_name)
                const daysUntilExpiry = product.expiry_date
                  ? Math.ceil((new Date(product.expiry_date) - new Date()) / (1000 * 60 * 60 * 24))
                  : null
                const isExpired = daysUntilExpiry !== null && daysUntilExpiry < 0
                const isExpiringSoon = daysUntilExpiry !== null && daysUntilExpiry <= 7 && daysUntilExpiry >= 0

                return (
                  <tr
                    key={product.product_id + product.extractionId}
                    className={isExpired ? 'expired' : isExpiringSoon ? 'expiring' : ''}
                  >
                    <td className="select-col">
                      <input
                        type="checkbox"
                        checked={selectedProducts.includes(product.product_id + product.extractionId)}
                        onChange={() => toggleProductSelection(product.product_id + product.extractionId)}
                      />
                    </td>
                    <td>
                      <div className="product-info">
                        <span className="product-name">{product.product_name}</span>
                        <span className="product-id">{product.product_id}</span>
                      </div>
                    </td>
                    <td>
                      <span className="quantity-badge">
                        {product.quantity} {product.unit}
                      </span>
                    </td>
                    <td>
                      {product.expiry_date ? (
                        <div className="expiry-info">
                          <span>{new Date(product.expiry_date).toLocaleDateString()}</span>
                          {daysUntilExpiry !== null && (
                            <span className={`expiry-badge ${isExpired ? 'expired' : isExpiringSoon ? 'expiring' : ''}`}>
                              {isExpired ? 'Expired' : `${daysUntilExpiry} days`}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="no-date">N/A</span>
                      )}
                    </td>
                    <td>
                      {product.condition ? (
                        <span className={`condition-badge condition-${product.condition}`}>
                          {product.condition}
                        </span>
                      ) : (
                        <span className="no-date">N/A</span>
                      )}
                    </td>
                    <td>
                      <div className="location-info">
                        {product.source_farm && (
                          <div className="location-row">
                            <MapPin size={14} />
                            <span>{product.source_farm}</span>
                          </div>
                        )}
                        {product.destination && (
                          <div className="location-row">
                            <Truck size={14} />
                            <span>{product.destination}</span>
                          </div>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="storage-info">
                        <span className="storage-type">{storage.type}</span>
                        <span className="storage-temp">{storage.temp}°C</span>
                        <span className="storage-humidity">{storage.humidity}%</span>
                      </div>
                    </td>
                    <td className="actions-col">
                      <button className="action-btn view" title="View Details">
                        <Eye size={16} />
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <span className="showing-info">
          Showing {filteredProducts.length} of {products.length} products
        </span>
        {selectedProducts.length > 0 && (
          <span className="selected-count">
            {selectedProducts.length} selected
          </span>
        )}
      </div>
    </div>
  )
}

// Storage type lookup function
function getStorageType(productName) {
  if (!productName) return { type: 'Cool Storage', temp: '4-10', humidity: '85' }

  const productLower = productName.toLowerCase()

  if (productLower.includes('lettuce') || productLower.includes('spinach') ||
      productLower.includes('kale') || productLower.includes('arugula') ||
      productLower.includes('leafy') || productLower.includes('greens')) {
    return { type: 'Refrigerated', temp: '0-4', humidity: '95' }
  }

  if (productLower.includes('carrot') || productLower.includes('potato') ||
      productLower.includes('onion') || productLower.includes('beet') ||
      productLower.includes('radish') || productLower.includes('turnip')) {
    return { type: 'Cool Storage', temp: '0-10', humidity: '90' }
  }

  if (productLower.includes('tomato') || productLower.includes('cucumber') ||
      productLower.includes('pepper') || productLower.includes('zucchini')) {
    return { type: 'Cool Storage', temp: '10-13', humidity: '85-90' }
  }

  if (productLower.includes('strawberr') || productLower.includes('raspberry') ||
      productLower.includes('blueberry') || productLower.includes('blackberry') ||
      productLower.includes('berry')) {
    return { type: 'Refrigerated', temp: '0-2', humidity: '90-95' }
  }

  if (productLower.includes('orange') || productLower.includes('lemon') ||
      productLower.includes('lime') || productLower.includes('grapefruit') ||
      productLower.includes('citrus')) {
    return { type: 'Cool Storage', temp: '4-10', humidity: '85-90' }
  }

  if (productLower.includes('apple') || productLower.includes('pear')) {
    return { type: 'Cold Storage', temp: '-1 to 4', humidity: '90-95' }
  }

  if (productLower.includes('basil') || productLower.includes('cilantro') ||
      productLower.includes('parsley') || productLower.includes('dill') ||
      productLower.includes('mint') || productLower.includes('herb')) {
    return { type: 'Refrigerated', temp: '0-4', humidity: '95' }
  }

  if (productLower.includes('mushroom')) {
    return { type: 'Refrigerated', temp: '0-4', humidity: '90-95' }
  }

  if (productLower.includes('egg') || productLower.includes('milk') ||
      productLower.includes('cheese') || productLower.includes('yogurt')) {
    return { type: 'Refrigerated', temp: '0-4', humidity: '85-90' }
  }

  if (productLower.includes('chicken') || productLower.includes('beef') ||
      productLower.includes('pork') || productLower.includes('lamb') ||
      productLower.includes('meat')) {
    return { type: 'Refrigerated', temp: '0-2', humidity: '85-90' }
  }

  if (productLower.includes('fish') || productLower.includes('salmon') ||
      productLower.includes('tuna') || productLower.includes('shrimp') ||
      productLower.includes('seafood')) {
    return { type: 'Cold Storage (Ice)', temp: '-1 to 2', humidity: '95-98' }
  }

  if (productLower.includes('rice') || productLower.includes('wheat') ||
      productLower.includes('corn') || productLower.includes('oat') ||
      productLower.includes('bean') || productLower.includes('dry')) {
    return { type: 'Dry Storage', temp: '10-21', humidity: '50-60' }
  }

  if (productLower.includes('bread') || productLower.includes('bakery') ||
      productLower.includes('pastry')) {
    return { type: 'Room Temperature', temp: '18-24', humidity: '60-70' }
  }

  return { type: 'Cool Storage', temp: '4-10', humidity: '85' }
}

// Mock data for demonstration
function getMockProducts() {
  return [
    {
      product_id: 'PROD-001',
      product_name: 'Organic Lettuce',
      quantity: 50,
      unit: 'piece',
      expiry_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
      condition: 'excellent',
      source_farm: 'Green Valley Farm',
      destination: 'Warehouse A',
      extractionId: 'ext1',
      extractionTimestamp: new Date().toISOString()
    },
    {
      product_id: 'PROD-002',
      product_name: 'Fresh Strawberries',
      quantity: 25,
      unit: 'box',
      expiry_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
      condition: 'good',
      source_farm: 'Sunny Fields',
      destination: 'Warehouse B',
      extractionId: 'ext2',
      extractionTimestamp: new Date().toISOString()
    },
    {
      product_id: 'PROD-003',
      product_name: 'Baby Spinach',
      quantity: 100,
      unit: 'box',
      expiry_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
      condition: 'good',
      source_farm: 'Green Valley Farm',
      destination: 'Distribution Center',
      extractionId: 'ext3',
      extractionTimestamp: new Date().toISOString()
    },
    {
      product_id: 'PROD-004',
      product_name: 'Carrots',
      quantity: 75,
      unit: 'kg',
      expiry_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
      condition: 'excellent',
      source_farm: 'Root Harvest Farm',
      destination: 'Warehouse A',
      extractionId: 'ext4',
      extractionTimestamp: new Date().toISOString()
    },
    {
      product_id: 'PROD-005',
      product_name: 'Tomatoes',
      quantity: 60,
      unit: 'kg',
      expiry_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      condition: 'fair',
      source_farm: 'Sunny Fields',
      destination: 'Distribution Center',
      extractionId: 'ext5',
      extractionTimestamp: new Date().toISOString()
    },
    {
      product_id: 'PROD-006',
      product_name: 'Blueberries',
      quantity: 30,
      unit: 'box',
      expiry_date: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString(),
      condition: 'excellent',
      source_farm: 'Berry Best Farm',
      destination: 'Warehouse B',
      extractionId: 'ext6',
      extractionTimestamp: new Date().toISOString()
    },
    {
      product_id: 'PROD-007',
      product_name: 'Apples',
      quantity: 200,
      unit: 'kg',
      expiry_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      condition: 'excellent',
      source_farm: 'Orchard Hills',
      destination: 'Warehouse A',
      extractionId: 'ext7',
      extractionTimestamp: new Date().toISOString()
    },
    {
      product_id: 'PROD-008',
      product_name: 'Milk',
      quantity: 40,
      unit: 'litre',
      expiry_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      condition: 'good',
      source_farm: 'Dairy Fresh Farms',
      destination: 'Distribution Center',
      extractionId: 'ext8',
      extractionTimestamp: new Date().toISOString()
    }
  ]
}

export default ProductDashboard
