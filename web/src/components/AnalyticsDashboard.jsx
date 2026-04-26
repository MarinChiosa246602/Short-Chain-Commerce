import React, { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Package, AlertTriangle, Calendar, DollarSign, Truck, Activity } from 'lucide-react'
import api from '../services/api'

/**
 * Enhanced Analytics Dashboard
 * Provides forecasting, trend analysis, and predictive insights
 */
function AnalyticsDashboard() {
  const [timeRange, setTimeRange] = useState('30d') // 7d, 30d, 90d, 1y
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  const fetchAnalytics = async () => {
    setLoading(true)
    // In production, fetch from backend API
    setAnalytics(getMockAnalytics())
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="analytics-dashboard">
        <div className="loading-state">Loading analytics...</div>
      </div>
    )
  }

  return (
    <div className="analytics-dashboard">
      <div className="analytics-header">
        <div className="analytics-title">
          <BarChart size={24} />
          <div>
            <h2>Analytics & Forecasting</h2>
            <p>Insights, trends, and predictive analytics</p>
          </div>
        </div>
        <div className="time-range">
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="1y">Last Year</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <MetricCard
          icon={Package}
          title="Total Products Tracked"
          value={analytics?.totalProducts || 0}
          trend={analytics?.productGrowth || 0}
          trendLabel="vs previous period"
          color="blue"
        />
        <MetricCard
          icon={DollarSign}
          title="Inventory Value"
          value={`$${analytics?.inventoryValue?.toLocaleString() || 0}`}
          trend={analytics?.valueGrowth || 0}
          trendLabel="vs previous period"
          color="green"
        />
        <MetricCard
          icon={AlertTriangle}
          title="Waste Prevention"
          value={`${analytics?.wastePrevented || 0} kg`}
          trend={analytics?.wasteReduction || 0}
          trendLabel="saved from expiration"
          color="orange"
        />
        <MetricCard
          icon={Truck}
          title="Deliveries Completed"
          value={analytics?.deliveriesCompleted || 0}
          trend={analytics?.deliveryGrowth || 0}
          trendLabel="vs previous period"
          color="purple"
        />
      </div>

      {/* Charts Section */}
      <div className="charts-grid">
        {/* Inventory Trend Chart */}
        <div className="chart-card large">
          <h3>Inventory Trend</h3>
          <LineChartComponent data={analytics?.inventoryTrend} />
        </div>

        {/* Product Category Distribution */}
        <div className="chart-card">
          <h3>Product Categories</h3>
          <PieChartComponent data={analytics?.categoryDistribution} />
        </div>

        {/* Expiration Risk Forecast */}
        <div className="chart-card">
          <h3>Expiration Risk Forecast</h3>
          <BarChartComponent data={analytics?.expirationForecast} />
        </div>

        {/* Condition Trends */}
        <div className="chart-card large">
          <h3>Product Condition Trends</h3>
          <AreaChartComponent data={analytics?.conditionTrends} />
        </div>
      </div>

      {/* Insights Section */}
      <div className="insights-section">
        <h3>AI-Powered Insights</h3>
        <div className="insights-grid">
          {analytics?.insights?.map((insight, idx) => (
            <InsightCard key={idx} insight={insight} />
          ))}
        </div>
      </div>

      {/* Top/Bottom Performers */}
      <div className="performers-section">
        <div className="performers-column">
          <h3>Top Products by Volume</h3>
          <TopProductsList products={analytics?.topProducts} />
        </div>
        <div className="performers-column">
          <h3>Needs Attention</h3>
          <NeedsAttentionList items={analytics?.needsAttention} />
        </div>
      </div>
    </div>
  )
}

// Metric Card Component
function MetricCard({ icon: Icon, title, value, trend, trendLabel, color }) {
  const colorClasses = {
    blue: 'bg-blue',
    green: 'bg-green',
    orange: 'bg-orange',
    purple: 'bg-purple',
    red: 'bg-red'
  }

  return (
    <div className="metric-card">
      <div className={`metric-icon ${colorClasses[color]}`}>
        <Icon size={24} />
      </div>
      <div className="metric-content">
        <span className="metric-label">{title}</span>
        <span className="metric-value">{value}</span>
        <div className="metric-trend">
          {trend > 0 ? (
            <TrendingUp size={16} className="trend-up" />
          ) : (
            <TrendingDown size={16} className="trend-down" />
          )}
          <span className={trend > 0 ? 'trend-up' : 'trend-down'}>
            {Math.abs(trend)}%
          </span>
          <span className="trend-label">{trendLabel}</span>
        </div>
      </div>
    </div>
  )
}

// Line Chart Component (Simplified visualization)
function LineChartComponent({ data }) {
  const maxVal = Math.max(...data.map(d => d.value), 1)

  return (
    <div className="line-chart">
      <div className="chart-axes">
        <div className="chart-lines">
          {data.map((point, idx) => {
            const height = (point.value / maxVal) * 100
            return (
              <div key={idx} className="chart-point-wrapper" style={{ flex: 1 }}>
                <div className="chart-point" style={{ height: `${height}%` }}>
                  <div className="point-value">{point.value}</div>
                </div>
                <div className="point-label">{point.label}</div>
              </div>
            )
          })}
        </div>
        <div className="chart-trend-line">
          {data.map((point, idx) => (
            <span key={idx} style={{ left: `${(idx / (data.length - 1)) * 100}%` }} />
          ))}
        </div>
      </div>
    </div>
  )
}

// Bar Chart Component
function BarChartComponent({ data }) {
  const maxVal = Math.max(...data.map(d => d.value), 1)

  return (
    <div className="bar-chart">
      <div className="bar-container">
        {data.map((item, idx) => {
          const height = (item.value / maxVal) * 100
          return (
            <div key={idx} className="bar-item" style={{ height: `${height}%` }}>
              <div className="bar-value">{item.value}</div>
              <div className={`bar-severity ${item.severity || ''}`} />
            </div>
          )
        })}
      </div>
      <div className="bar-labels">
        {data.map((item, idx) => (
          <div key={idx} className="bar-label">{item.label}</div>
        ))}
      </div>
    </div>
  )
}

// Pie Chart Component (Simplified)
function PieChartComponent({ data }) {
  return (
    <div className="pie-chart">
      <div className="pie-segments">
        {data.map((item, idx) => (
          <div
            key={idx}
            className="pie-segment"
            style={{
              width: `${item.percentage}%`,
              backgroundColor: item.color
            }}
          >
            {item.percentage > 10 && (
              <span className="segment-label">{item.label}</span>
            )}
          </div>
        ))}
      </div>
      <div className="pie-legend">
        {data.map((item, idx) => (
          <div key={idx} className="legend-item">
            <div className="legend-color" style={{ backgroundColor: item.color }} />
            <span>{item.label}: {item.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Area Chart Component
function AreaChartComponent({ data }) {
  return (
    <div className="area-chart">
      <div className="area-series">
        {data?.map((series, idx) => (
          <div key={idx} className="area-series-item">
            <div className="series-header">
              <div className="series-color" style={{ backgroundColor: series.color }} />
              <span>{series.name}</span>
            </div>
            <div className="series-bar">
              {series.data?.map((point, i) => (
                <div
                  key={i}
                  className="series-point"
                  style={{
                    height: `${point * 20}%`,
                    backgroundColor: series.color
                  }}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Insight Card Component
function InsightCard({ insight }) {
  const getInsightIcon = (type) => {
    switch (type) {
      case 'warning': return <AlertTriangle size={20} className="insight-warning" />
      case 'success': return <TrendingUp size={20} className="insight-success" />
      case 'info': return <Calendar size={20} className="insight-info" />
      default: return <Package size={20} />
    }
  }

  return (
    <div className={`insight-card ${insight.type || 'info'}`}>
      <div className="insight-icon">{getInsightIcon(insight.type)}</div>
      <div className="insight-content">
        <h4>{insight.title}</h4>
        <p>{insight.description}</p>
        {insight.action && (
          <button className="insight-action">{insight.action}</button>
        )}
      </div>
    </div>
  )
}

// Top Products List
function TopProductsList({ products }) {
  return (
    <div className="top-products">
      {products?.map((product, idx) => (
        <div key={idx} className="top-product-item">
          <span className="rank">{idx + 1}</span>
          <div className="product-info">
            <span className="product-name">{product.name}</span>
            <span className="product-value">{product.value}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

// Needs Attention List
function NeedsAttentionList({ items }) {
  return (
    <div className="needs-attention">
      {items?.map((item, idx) => (
        <div key={idx} className={`attention-item ${item.priority || 'medium'}`}>
          <AlertTriangle size={16} />
          <div className="attention-content">
            <span className="attention-item-name">{item.name}</span>
            <span className="attention-item-desc">{item.description}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

// Mock analytics data
function getMockAnalytics() {
  return {
    totalProducts: 1250,
    productGrowth: 12.5,
    inventoryValue: 45600,
    valueGrowth: 8.3,
    wastePrevented: 340,
    wasteReduction: 15.2,
    deliveriesCompleted: 87,
    deliveryGrowth: 5.8,

    inventoryTrend: [
      { label: 'Week 1', value: 850 },
      { label: 'Week 2', value: 920 },
      { label: 'Week 3', value: 1050 },
      { label: 'Week 4', value: 1180 },
      { label: 'Week 5', value: 1250 },
    ],

    categoryDistribution: [
      { label: 'Vegetables', value: 45, percentage: 45, color: '#10b981' },
      { label: 'Fruits', value: 30, percentage: 30, color: '#f59e0b' },
      { label: 'Dairy', value: 15, percentage: 15, color: '#3b82f6' },
      { label: 'Meat', value: 10, percentage: 10, color: '#ef4444' },
    ],

    expirationForecast: [
      { label: 'Today', value: 2, severity: 'critical' },
      { label: '3 days', value: 5, severity: 'warning' },
      { label: '7 days', value: 12, severity: 'info' },
      { label: '14 days', value: 20, severity: '' },
    ],

    conditionTrends: [
      { name: 'Excellent', color: '#10b981', data: [70, 72, 75, 73, 78] },
      { name: 'Good', color: '#3b82f6', data: [20, 18, 17, 19, 16] },
      { name: 'Fair', color: '#f59e0b', data: [7, 8, 6, 6, 4] },
      { name: 'Poor', color: '#ef4444', data: [3, 2, 2, 2, 2] },
    ],

    insights: [
      {
        type: 'warning',
        title: 'Expiration Risk Detected',
        description: '5 products expiring within 3 days. Schedule immediate delivery.',
        action: 'View Critical Items'
      },
      {
        type: 'success',
        title: 'Waste Reduction Achievement',
        description: 'You\'ve prevented 340kg of waste this month through proactive management.',
        action: 'View Report'
      },
      {
        type: 'info',
        title: 'Seasonal Trend Alert',
        description: 'Leafy greens demand typically increases 20% in the next 2 weeks.',
        action: 'Review Forecast'
      },
      {
        type: 'success',
        title: 'Efficiency Improvement',
        description: 'Route optimization saved an average of 12% on delivery time this week.',
        action: 'View Routes'
      }
    ],

    topProducts: [
      { name: 'Organic Lettuce', value: '250 boxes/week' },
      { name: 'Baby Spinach', value: '180 boxes/week' },
      { name: 'Tomatoes', value: '150 kg/week' },
      { name: 'Carrots', value: '120 kg/week' },
      { name: 'Strawberries', value: '100 boxes/week' },
    ],

    needsAttention: [
      { name: 'Milk Batch #4521', description: 'Expires in 1 day', priority: 'critical' },
      { name: 'Fresh Berries', description: 'Condition declining - sell soon', priority: 'high' },
      { name: 'Herb Mix', description: 'Low inventory alert', priority: 'medium' },
    ]
  }
}

export default AnalyticsDashboard
