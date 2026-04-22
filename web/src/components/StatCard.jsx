import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

function StatCard({ icon: Icon, title, value, trend, trendValue, color = 'blue' }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400',
    green: 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400',
    purple: 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400',
    red: 'bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400',
    gray: 'bg-gray-50 text-gray-600 dark:bg-gray-900/20 dark:text-gray-400',
    orange: 'bg-orange-50 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400',
  }

  const borderClasses = {
    blue: 'border-blue-200 dark:border-blue-800',
    green: 'border-green-200 dark:border-green-800',
    purple: 'border-purple-200 dark:border-purple-800',
    red: 'border-red-200 dark:border-red-800',
    gray: 'border-gray-200 dark:border-gray-800',
    orange: 'border-orange-200 dark:border-orange-800',
  }

  return (
    <div className={`stat-card ${borderClasses[color]}`}>
      <div className={`stat-icon ${colorClasses[color]}`}>
        <Icon size={24} />
      </div>
      <div className="stat-content">
        <span className="stat-title">{title}</span>
        <span className="stat-value">{value}</span>
        {trend && (
          <div className={`stat-trend ${trend === 'up' ? 'trend-up' : 'trend-down'}`}>
            {trend === 'up' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            <span>{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default StatCard
