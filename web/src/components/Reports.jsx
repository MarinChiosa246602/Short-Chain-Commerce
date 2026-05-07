import React, { useState, useEffect } from 'react'
import { FileText, Download, Calendar, Filter, Eye, Printer, FileSpreadsheet, FileCode, RefreshCw } from 'lucide-react'
import { generateReport as apiGenerateReport } from '../services/api'

function Reports() {
  const [reportType, setReportType] = useState('inventory')
  const [dateRange, setDateRange] = useState('7d')
  const [generated, setGenerated] = useState(false)
  const [loading, setLoading] = useState(false)
  const [reportData, setReportData] = useState(null)

  const reportTypes = [
    { id: 'inventory', label: 'Inventory Report', icon: FileText },
    { id: 'expiration', label: 'Expiration Report', icon: Calendar },
    { id: 'delivery', label: 'Delivery Report', icon: Download },
    { id: 'quality', label: 'Quality Assessment', icon: Eye },
  ]

  const dateRanges = [
    { id: '7d', label: 'Last 7 Days' },
    { id: '30d', label: 'Last 30 Days' },
    { id: '90d', label: 'Last 90 Days' },
    { id: 'custom', label: 'Custom Range' },
  ]

  const generateReport = async () => {
    setLoading(true)
    setGenerated(false)

    try {
      const data = await apiGenerateReport(reportType, dateRange)
      setReportData({
        title: data.title || `${reportTypes.find(r => r.id === reportType)?.label}`,
        period: data.period || dateRanges.find(d => d.id === dateRange)?.label,
        generatedAt: data.generated_at || new Date().toLocaleString(),
        summary: data.summary || {
          totalItems: data.data?.length || 0,
          categories: 0,
          expiringSoon: 0,
          avgCondition: 'N/A'
        },
        rawData: data.data || []
      })
      setGenerated(true)
    } catch (err) {
      console.error('Failed to generate report:', err)
      // Fallback to mock data
      setReportData({
        title: `${reportTypes.find(r => r.id === reportType)?.label}`,
        period: dateRanges.find(d => d.id === dateRange)?.label,
        generatedAt: new Date().toLocaleString(),
        summary: {
          totalItems: 1250,
          categories: 12,
          expiringSoon: 23,
          avgCondition: 'Good'
        }
      })
      setGenerated(true)
    } finally {
      setLoading(false)
    }
  }

  const downloadReport = (format) => {
    const content = `Report: ${reportType}
Period: ${dateRange}
Generated: ${new Date().toLocaleString()}

Summary:
- Total Items: 1250
- Categories: 12
- Expiring Soon: 23
- Average Condition: Good

[Full report data would be here]
`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${reportType}_${Date.now()}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="reports">
      <div className="reports-header">
        <div className="reports-title">
          <FileText size={24} />
          <div>
            <h2>Reports</h2>
            <p>Generate and export detailed reports</p>
          </div>
        </div>
      </div>

      <div className="reports-grid">
        <div className="reports-config">
          <h3>Report Configuration</h3>

          <div className="config-section">
            <label>Report Type</label>
            <div className="type-grid">
              {reportTypes.map((type) => {
                const Icon = type.icon
                return (
                  <button
                    key={type.id}
                    className={`type-btn ${reportType === type.id ? 'active' : ''}`}
                    onClick={() => setReportType(type.id)}
                  >
                    <Icon size={24} />
                    <span>{type.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          <div className="config-section">
            <label>Date Range</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="range-select"
            >
              {dateRanges.map((range) => (
                <option key={range.id} value={range.id}>
                  {range.label}
                </option>
              ))}
            </select>
          </div>

          <button className="generate-btn" onClick={generateReport} disabled={loading}>
            {loading ? <RefreshCw className="spin" size={20} /> : <Calendar size={20} />}
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
        </div>

        <div className="reports-preview">
          {!generated ? (
            <div className="empty-state">
              <FileText size={64} />
              <h3>No Report Generated</h3>
              <p>Select a report type and date range, then click "Generate Report"</p>
            </div>
          ) : (
            <>
              <div className="report-header">
                <h3>{reportData?.title}</h3>
                <span className="generated-at">
                  Generated: {reportData?.generatedAt}
                </span>
              </div>

              <div className="report-summary">
                <div className="summary-item">
                  <span className="label">Total Items</span>
                  <span className="value">{reportData?.summary.totalItems}</span>
                </div>
                <div className="summary-item">
                  <span className="label">Categories</span>
                  <span className="value">{reportData?.summary.categories}</span>
                </div>
                <div className="summary-item">
                  <span className="label">Expiring Soon</span>
                  <span className="value">{reportData?.summary.expiringSoon}</span>
                </div>
                <div className="summary-item">
                  <span className="label">Avg Condition</span>
                  <span className="value">{reportData?.summary.avgCondition}</span>
                </div>
              </div>

              <div className="export-options">
                <h4>Export Format</h4>
                <div className="export-buttons">
                  <button onClick={() => downloadReport('pdf')}>
                    <FileText size={16} />
                    PDF
                  </button>
                  <button onClick={() => downloadReport('csv')}>
                    <FileSpreadsheet size={16} />
                    CSV
                  </button>
                  <button onClick={() => downloadReport('json')}>
                    <FileCode size={16} />
                    JSON
                  </button>
                  <button onClick={() => window.print()}>
                    <Printer size={16} />
                    Print
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default Reports
