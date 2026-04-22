import React from 'react'
import { Clock, CheckCircle, AlertCircle, XCircle } from 'lucide-react'

function RecentExtractions({ extractions }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle size={16} className="text-green-500" />
      case 'partial':
        return <AlertCircle size={16} className="text-yellow-500" />
      case 'error':
        return <XCircle size={16} className="text-red-500" />
      default:
        return <Clock size={16} className="text-gray-400" />
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

  if (!extractions || extractions.length === 0) {
    return (
      <div className="recent-extractions">
        <h3>Recent Extractions</h3>
        <div className="empty-state">
          <p>No extractions yet. Start by uploading an image!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="recent-extractions">
      <div className="section-header">
        <h3>Recent Extractions</h3>
      </div>

      <div className="extraction-table">
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>Image ID</th>
              <th>Products</th>
              <th>Processing Time</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {extractions.slice(0, 10).map((extraction, idx) => (
              <tr key={idx}>
                <td>
                  <span className={`status-badge ${getStatusClass(extraction.status)}`}>
                    {getStatusIcon(extraction.status)}
                    {extraction.status}
                  </span>
                </td>
                <td>
                  <code>
                    {(extraction.extraction_id || '').substring(0, 8)}...
                  </code>
                </td>
                <td>
                  {extraction.extraction?.products?.length || 0} products
                </td>
                <td>
                  {extraction.processing_time_ms?.toFixed(0) || 0}ms
                </td>
                <td>
                  {extraction.timestamp
                    ? new Date(extraction.timestamp).toLocaleString()
                    : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default RecentExtractions
