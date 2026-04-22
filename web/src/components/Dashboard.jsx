import React, { useState, useEffect } from 'react'
import api from '../services/api'
import StatCard from './StatCard'
import RecentExtractions from './RecentExtractions'
import ExtractionChart from './ExtractionChart'
import { TrendingUp, TrendingDown, Package, Clock, AlertTriangle, CheckCircle } from 'lucide-react'

function Dashboard() {
  const [stats, setStats] = useState({
    totalExtractions: 0,
    successRate: 0,
    avgProcessingTime: 0,
    pendingAlerts: 0,
  })
  const [recentExtractions, setRecentExtractions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const fetchDashboardData = async () => {
    try {
      // Get metrics from API
      const metricsRes = await api.getMetrics()

      // Get recent extractions from database
      const historyRes = await api.getRecentExtractions(10)

      setStats({
        totalExtractions: metricsRes.total_requests || 0,
        successRate: ((metricsRes.successful_requests || 0) / (metricsRes.total_requests || 1) * 100).toFixed(1),
        avgProcessingTime: metricsRes.avg_processing_time_ms?.toFixed(0) || 0,
        pendingAlerts: historyRes.results?.filter(r => r.status === 'error' || r.status === 'partial').length || 0,
      })

      setRecentExtractions(historyRes.results || [])
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="dashboard loading-state">
        <div className="spinner">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p className="subtitle">Overview of extraction pipeline performance</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <StatCard
          icon={Package}
          title="Total Extractions"
          value={stats.totalExtractions}
          trend="up"
          trendValue="12%"
          color="blue"
        />
        <StatCard
          icon={CheckCircle}
          title="Success Rate"
          value={`${stats.successRate}%`}
          trend={stats.successRate >= 80 ? 'up' : 'down'}
          trendValue={stats.successRate >= 80 ? '+5%' : '-3%'}
          color="green"
        />
        <StatCard
          icon={Clock}
          title="Avg Processing Time"
          value={`${stats.avgProcessingTime}ms`}
          trend="down"
          trendValue="-8%"
          color="purple"
        />
        <StatCard
          icon={AlertTriangle}
          title="Pending Alerts"
          value={stats.pendingAlerts}
          trend={stats.pendingAlerts === 0 ? 'up' : 'down'}
          trendValue={stats.pendingAlerts === 0 ? 'All clear' : 'Needs attention'}
          color={stats.pendingAlerts > 0 ? 'red' : 'gray'}
        />
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        <div className="chart-card">
          <h3>Extraction Trends (Last 7 Days)</h3>
          <ExtractionChart data={recentExtractions} />
        </div>
      </div>

      {/* Recent Extractions */}
      <div className="recent-section">
        <RecentExtractions extractions={recentExtractions} />
      </div>
    </div>
  )
}

export default Dashboard
