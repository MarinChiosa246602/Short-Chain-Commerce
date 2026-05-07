import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Extraction API
export const extractData = async (formData) => {
  const response = await api.post('/api/v1/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export const extractBatch = async (files, sourceFarm = null, destination = null) => {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })
  if (sourceFarm) formData.append('source_farm', sourceFarm)
  if (destination) formData.append('destination', destination)

  const response = await api.post('/api/v1/extract/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

// Metrics API
export const getMetrics = async () => {
  const response = await api.get('/api/v1/metrics')
  return response.data
}

// Health API
export const getHealth = async () => {
  const response = await api.get('/health')
  return response.data
}

export const getDetailedHealth = async () => {
  const response = await api.get('/api/v1/health/detailed')
  return response.data
}

// Database/API for history
export const getRecentExtractions = async (limit = 50) => {
  const response = await api.get('/api/v1/extractions', {
    params: { limit, status: 'all' },
  })
  return response.data
}

export const getExtractionById = async (id) => {
  const response = await api.get(`/api/v1/extractions/${id}`)
  return response.data
}

export const getAnalyticsSummary = async (days = 7) => {
  const response = await api.get('/api/v1/analytics/summary', {
    params: { days },
  })
  return response.data
}

// Schemas
export const getSchemas = async () => {
  const response = await api.get('/api/v1/schemas')
  return response.data
}

// Inventory API
export const getInventory = async () => {
  const response = await api.get('/api/v1/inventory')
  return response.data
}

// Expiration Alerts API
export const getExpiringProducts = async (days = 14) => {
  const response = await api.get('/api/v1/alerts/expiring', {
    params: { days },
  })
  return response.data
}

// Deliveries API
export const getDeliveries = async () => {
  const response = await api.get('/api/v1/deliveries')
  return response.data
}

// Reports API
export const generateReport = async (reportType, dateRange) => {
  const response = await api.post('/api/v1/reports/generate', {
    report_type: reportType,
    date_range: dateRange,
  })
  return response.data
}

// Anomalies API
export const getAnomalies = async (limit = 50) => {
  const response = await api.get('/api/v1/anomalies', {
    params: { limit },
  })
  return response.data
}

export default {
  extractData,
  extractBatch,
  getMetrics,
  getHealth,
  getDetailedHealth,
  getRecentExtractions,
  getExtractionById,
  getSchemas,
  getInventory,
  getExpiringProducts,
  getDeliveries,
  generateReport,
  getAnomalies,
}
