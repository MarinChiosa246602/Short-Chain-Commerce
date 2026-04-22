import React from 'react'

function ExtractionChart({ data }) {
  // Simple bar chart component using CSS
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        <p>No data available</p>
      </div>
    )
  }

  // Group by date and count
  const dailyStats = data.reduce((acc, item) => {
    const date = item.timestamp
      ? new Date(item.timestamp).toLocaleDateString()
      : 'Unknown'
    acc[date] = (acc[date] || 0) + 1
    return acc
  }, {})

  const dates = Object.keys(dailyStats).slice(-7) // Last 7 days
  const counts = dates.map((date) => dailyStats[date])
  const maxCount = Math.max(...counts, 1)

  return (
    <div className="bar-chart">
      <div className="chart-bars">
        {dates.map((date, idx) => (
          <div key={idx} className="bar-container">
            <div
              className="bar"
              style={{ height: `${(counts[idx] / maxCount) * 100}%` }}
            >
              <span className="bar-value">{counts[idx]}</span>
            </div>
            <span className="bar-label">{date}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ExtractionChart
