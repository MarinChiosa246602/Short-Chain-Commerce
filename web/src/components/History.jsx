import React, { useState, useEffect } from 'react'
import { Search, Filter, Download, XCircle, AlertCircle, CheckCircle } from 'lucide-react'
import api from '../services/api'

function History() {
  const [extractions, setExtractions] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedExtraction, setSelectedExtraction] = useState(null)

  useEffect(() => {
    fetchExtractions()
  }, [])

  const fetchExtractions = async () => {
    setLoading(true)
    try {
      // This would connect to your database endpoint
      const response = await api.getRecentExtractions(100)
      setExtractions(response.results || [])
    } catch (error) {
      console.error('Failed to fetch history:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredExtractions = extractions.filter((item) => {
    const matchesSearch =
      searchTerm === '' ||
      (item.extraction_id?.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (item.extraction?.metadata?.source_farm?.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesStatus =
      statusFilter === 'all' || item.status === statusFilter

    return matchesSearch && matchesStatus
  })

  const exportToCSV = () => {
    const headers = ['Extraction ID', 'Status', 'Products', 'Processing Time', 'Timestamp', 'Source Farm', 'Destination']
    const rows = filteredExtractions.map((item) => [
      item.extraction_id || '',
      item.status,
      item.extraction?.products?.length || 0,
      `${item.processing_time_ms?.toFixed(0) || 0}ms`,
      item.timestamp || '',
      item.extraction?.metadata?.source_farm || '',
      item.extraction?.metadata?.destination || '',
    ])

    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `extractions_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle size={16} />
      case 'partial':
        return <AlertCircle size={16} />
      case 'error':
        return <XCircle size={16} />
      default:
        return null
    }
  }

  const getStatusClass = (status) => {
    switch (status) {
      case 'success':
        return 'status-success'
      case 'partial':
        return 'status-partial'
      case 'error':
        return 'status-error'
      default:
        return ''
    }
  }

  return (
    <div className="history">
      <div className="page-header">
        <h1>Extraction History</h1>
        <p className="subtitle">Browse and manage past extractions</p>
      </div>

      {/* Filters */}
      <div className="filters">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search by extraction ID or source farm..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <Filter size={18} />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="success">Success</option>
            <option value="partial">Partial</option>
            <option value="error">Error</option>
          </select>
        </div>

        <button className="btn-secondary" onClick={exportToCSV}>
          <Download size={18} />
          Export CSV
        </button>
      </div>

      {/* Results Table */}
      {loading ? (
        <div className="loading-state">
          <div className="spinner">Loading history...</div>
        </div>
      ) : filteredExtractions.length === 0 ? (
        <div className="empty-state">
          <p>No extractions found matching your criteria.</p>
        </div>
      ) : (
        <div className="history-table">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Extraction ID</th>
                <th>Source Farm</th>
                <th>Destination</th>
                <th>Products</th>
                <th>Processing Time</th>
                <th>Timestamp</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredExtractions.map((item, idx) => (
                <tr key={idx}>
                  <td>
                    <span className={`status-badge ${getStatusClass(item.status)}`}>
                      {getStatusIcon(item.status)}
                      {item.status}
                    </span>
                  </td>
                  <td>
                    <code>{(item.extraction_id || '').substring(0, 12)}...</code>
                  </td>
                  <td>{item.extraction?.metadata?.source_farm || '-'}</td>
                  <td>{item.extraction?.metadata?.destination || '-'}</td>
                  <td>{item.extraction?.products?.length || 0}</td>
                  <td>{item.processing_time_ms?.toFixed(0) || 0}ms</td>
                  <td>
                    {item.timestamp
                      ? new Date(item.timestamp).toLocaleString()
                      : '-'}
                  </td>
                  <td>
                    <button
                      className="btn-text"
                      onClick={() => setSelectedExtraction(item)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Modal */}
      {selectedExtraction && (
        <div className="modal-overlay" onClick={() => setSelectedExtraction(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Extraction Details</h2>
              <button className="close-btn" onClick={() => setSelectedExtraction(null)}>
                <XCircle size={24} />
              </button>
            </div>
            <div className="modal-content">
              <pre>
                {JSON.stringify(selectedExtraction, null, 2)}
              </pre>
            </div>
            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={() => {
                  const blob = new Blob([JSON.stringify(selectedExtraction, null, 2)], {
                    type: 'application/json',
                  })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `extraction_${selectedExtraction.extraction_id}.json`
                  a.click()
                  URL.revokeObjectURL(url)
                }}
              >
                <Download size={18} />
                Download JSON
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default History
