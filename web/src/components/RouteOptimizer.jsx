import React, { useState, useEffect, useCallback } from 'react'
import { Truck, MapPin, Calendar, Clock, AlertTriangle, CheckCircle, Navigation, RefreshCw, Download, Play, Pause } from 'lucide-react'
import api, { getDeliveries } from '../services/api'

/**
 * Route Optimizer Component
 * Optimizes delivery routes based on product priority, expiration, and locations
 */
function RouteOptimizer() {
  const [deliveries, setDeliveries] = useState([])
  const [optimizedRoute, setOptimizedRoute] = useState(null)
  const [loading, setLoading] = useState(false)
  const [isCalculating, setIsCalculating] = useState(false)
  const [selectedVehicle, setSelectedVehicle] = useState('van-1')
  const [routeStatus, setRouteStatus] = useState('idle') // idle, calculating, optimized, active, completed

  // Warehouse/depot location
  const depots = [
    { id: 'dc-1', name: 'Main Distribution Center', lat: 37.7749, lng: -122.4194 },
    { id: 'wh-1', name: 'Warehouse A', lat: 37.7649, lng: -122.4294 },
    { id: 'wh-2', name: 'Warehouse B', lat: 37.7549, lng: -122.4394 },
  ]

  const vehicles = [
    { id: 'van-1', name: 'Van 1', capacity: 1000, type: 'Refrigerated' },
    { id: 'van-2', name: 'Van 2', capacity: 800, type: 'Cool Storage' },
    { id: 'truck-1', name: 'Truck 1', capacity: 5000, type: 'Mixed' },
  ]

  // Fetch pending deliveries
  const fetchDeliveries = useCallback(async () => {
    try {
      setLoading(true)

      // Use the new deliveries API
      try {
        const response = await getDeliveries()

        if (response.deliveries && response.deliveries.length > 0) {
          setDeliveries(response.deliveries)
        } else {
          setDeliveries(getMockDeliveries())
        }
      } catch {
        // Fallback to mock data
        setDeliveries(getMockDeliveries())
      }

      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch deliveries:', err)
      setDeliveries(getMockDeliveries())
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDeliveries()
  }, [fetchDeliveries])

  // Calculate optimized route using nearest neighbor algorithm with priority weights
  const optimizeRoute = async () => {
    if (deliveries.length === 0) {
      alert('No deliveries to optimize')
      return
    }

    setIsCalculating(true)
    setRouteStatus('calculating')

    // Simulate calculation delay
    await new Promise(resolve => setTimeout(resolve, 1500))

    const optimized = calculateOptimizedRoute(deliveries, depots[0])
    setOptimizedRoute(optimized)
    setRouteStatus('optimized')
    setIsCalculating(false)
  }

  const calculateOptimizedRoute = (deliveries, depot) => {
    // Priority scoring: expiring items get higher priority
    const now = new Date()
    const scoredDeliveries = deliveries.map(d => {
      let priorityScore = 50 // Base score

      // Expiration priority (most important)
      if (d.expiryDate) {
        const daysUntilExpiry = Math.ceil((new Date(d.expiryDate) - now) / (1000 * 60 * 60 * 24))
        if (daysUntilExpiry <= 2) priorityScore += 50 // Critical
        else if (daysUntilExpiry <= 7) priorityScore += 30 // Warning
        else if (daysUntilExpiry <= 14) priorityScore += 15 // Info
      }

      // Distance priority (closer = higher priority for efficiency)
      const distance = calculateDistance(depot.lat, depot.lng, d.location.lat, d.location.lng)
      const distanceScore = Math.max(0, 50 - distance) // Closer = higher score

      // Customer priority
      const customerPriority = d.priority === 'high' ? 20 : d.priority === 'medium' ? 10 : 0

      return {
        ...d,
        priorityScore: priorityScore + distanceScore + customerPriority,
        distanceFromDepot: distance
      }
    })

    // Sort by priority score (highest first)
    scoredDeliveries.sort((a, b) => b.priorityScore - a.priorityScore)

    // Build optimized route using nearest neighbor with priority
    const route = []
    const visited = new Set()
    let currentLocation = { lat: depot.lat, lng: depot.lng }

    // Add depot as start
    route.push({
      stopNumber: 0,
      type: 'depot',
      name: depot.name,
      location: depot,
      arrivalTime: '08:00',
      departureTime: '08:30',
      distance: 0,
      products: []
    })

    let totalDistance = 0
    let currentTime = 8.5 // 8:30 AM in decimal hours
    let remainingCapacity = vehicles.find(v => v.id === selectedVehicle)?.capacity || 1000

    // Process deliveries in priority order
    const sortedByNearest = optimizeWithNearestNeighbor(scoredDeliveries, currentLocation, visited)

    sortedByNearest.forEach((delivery, index) => {
      if (remainingCapacity < delivery.quantity) {
        // Skip if vehicle capacity exceeded
        return
      }

      const distance = calculateDistance(
        currentLocation.lat, currentLocation.lng,
        delivery.location.lat, delivery.location.lng
      )
      totalDistance += distance

      // Calculate travel time (average 40 km/h + 30 min loading)
      const travelTime = distance / 40 // hours
      const arrivalTime = currentTime + travelTime
      const departureTime = arrivalTime + 0.5 // 30 min for unloading

      route.push({
        stopNumber: index + 1,
        type: 'delivery',
        name: delivery.customerName,
        location: delivery.location,
        address: delivery.address,
        arrivalTime: formatTime(arrivalTime),
        departureTime: formatTime(departureTime),
        distance: Math.round(distance * 10) / 10,
        products: delivery.products,
        priority: delivery.priority,
        expiryAlert: delivery.expiryDate
      })

      currentLocation = delivery.location
      currentTime = departureTime
      remainingCapacity -= delivery.quantity
    })

    // Return to depot
    const returnDistance = calculateDistance(
      currentLocation.lat, currentLocation.lng,
      depot.lat, depot.lng
    )
    totalDistance += returnDistance
    const returnTime = currentTime + returnDistance / 40

    route.push({
      stopNumber: route.length,
      type: 'depot',
      name: depot.name,
      location: depot,
      arrivalTime: formatTime(returnTime),
      distance: Math.round(returnDistance * 10) / 10,
      products: []
    })

    return {
      route,
      totalDistance: Math.round(totalDistance * 10) / 10,
      totalStops: route.filter(s => s.type === 'delivery').length,
      estimatedEndTime: formatTime(returnTime),
      totalDrivingTime: Math.round((returnTime - 8) * 60),
      vehicleCapacityUsed: vehicles.find(v => v.id === selectedVehicle)?.capacity - remainingCapacity,
      capacityUtilization: Math.round(((vehicles.find(v => v.id === selectedVehicle)?.capacity - remainingCapacity) / vehicles.find(v => v.id === selectedVehicle)?.capacity) * 100)
    }
  }

  // Nearest neighbor optimization with priority consideration
  const optimizeWithNearestNeighbor = (deliveries, startLocation, visited) => {
    const result = []
    let current = startLocation

    while (result.length < deliveries.length) {
      // Find nearest unvisited delivery with priority weighting
      let nearest = null
      let nearestScore = Infinity

      deliveries.forEach(delivery => {
        if (visited.has(delivery.id)) return

        const distance = calculateDistance(
          current.lat, current.lng,
          delivery.location.lat, delivery.location.lng
        )

        // Score combines distance and priority (lower is better)
        const priorityWeight = delivery.priorityScore ? 1 / (delivery.priorityScore / 100) : 0.5
        const score = distance * priorityWeight

        if (score < nearestScore) {
          nearestScore = score
          nearest = delivery
        }
      })

      if (nearest) {
        visited.add(nearest.id)
        result.push(nearest)
        current = nearest.location
      } else {
        break
      }
    }

    return result
  }

  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371 // Earth's radius in km
    const dLat = toRad(lat2 - lat1)
    const dLon = toRad(lon2 - lon1)
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    return R * c
  }

  const toRad = (deg) => deg * (Math.PI / 180)

  const formatTime = (decimalTime) => {
    const hours = Math.floor(decimalTime)
    const minutes = Math.round((decimalTime - hours) * 60)
    const h = hours % 24
    const m = minutes % 60
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`
  }

  const startRoute = () => {
    setRouteStatus('active')
  }

  const completeRoute = () => {
    setRouteStatus('completed')
  }

  const resetRoute = () => {
    setOptimizedRoute(null)
    setRouteStatus('idle')
  }

  const exportRoute = () => {
    if (!optimizedRoute) return

    const csvContent = [
      'Stop Number,Type,Name,Address,Arrival,Departure,Distance (km),Products'
    ].concat(
      optimizedRoute.route.map(stop => {
        const productList = stop.products?.map(p => `${p.quantity} ${p.unit} ${p.name}`).join('; ') || 'N/A'
        return [
          stop.stopNumber,
          stop.type,
          `"${stop.name}"`,
          `"${stop.address || ''}"`,
          stop.arrivalTime,
          stop.departureTime || '',
          stop.distance || 0,
          `"${productList}"`
        ].join(',')
      })
    ).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `delivery_route_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="route-optimizer">
        <div className="loading-state">Loading deliveries...</div>
      </div>
    )
  }

  return (
    <div className="route-optimizer">
      <div className="route-header">
        <div className="route-title">
          <Truck size={24} />
          <div>
            <h2>Route Optimization</h2>
            <p>Optimize delivery routes based on priority and location</p>
          </div>
        </div>
        <div className="route-status">
          <span className={`status-badge ${routeStatus}`}>
            {routeStatus === 'idle' && 'Ready'}
            {routeStatus === 'calculating' && 'Calculating...'}
            {routeStatus === 'optimized' && 'Optimized'}
            {routeStatus === 'active' && 'In Progress'}
            {routeStatus === 'completed' && 'Completed'}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div className="route-controls">
        <div className="control-group">
          <label>Vehicle</label>
          <select
            value={selectedVehicle}
            onChange={(e) => setSelectedVehicle(e.target.value)}
            disabled={routeStatus === 'active'}
          >
            {vehicles.map(v => (
              <option key={v.id} value={v.id}>
                {v.name} ({v.capacity}kg) - {v.type}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Depot</label>
          <select disabled>
            {depots.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>

        <div className="control-actions">
          {routeStatus === 'idle' || routeStatus === 'completed' ? (
            <button className="btn-primary" onClick={optimizeRoute} disabled={isCalculating}>
              {isCalculating ? <RefreshCw className="spin" size={18} /> : <Play size={18} />}
              {isCalculating ? 'Calculating...' : 'Optimize Route'}
            </button>
          ) : routeStatus === 'optimized' ? (
            <>
              <button className="btn-primary" onClick={startRoute}>
                <Navigation size={18} />
                Start Route
              </button>
              <button className="btn-secondary" onClick={resetRoute}>
                Reset
              </button>
            </>
          ) : routeStatus === 'active' ? (
            <button className="btn-success" onClick={completeRoute}>
              <CheckCircle size={18} />
              Complete Route
            </button>
          ) : null}
        </div>
      </div>

      {/* Route Summary */}
      {optimizedRoute && (
        <div className="route-summary">
          <div className="summary-card">
            <MapPin size={24} />
            <div>
              <span className="label">Total Distance</span>
              <span className="value">{optimizedRoute.totalDistance} km</span>
            </div>
          </div>
          <div className="summary-card">
            <Navigation size={24} />
            <div>
              <span className="label">Stops</span>
              <span className="value">{optimizedRoute.totalStops}</span>
            </div>
          </div>
          <div className="summary-card">
            <Clock size={24} />
            <div>
              <span className="label">Driving Time</span>
              <span className="value">{optimizedRoute.totalDrivingTime} min</span>
            </div>
          </div>
          <div className="summary-card">
            <Truck size={24} />
            <div>
              <span className="label">Capacity Used</span>
              <span className="value">{optimizedRoute.capacityUtilization}%</span>
            </div>
          </div>
          <div className="summary-card">
            <Calendar size={24} />
            <div>
              <span className="label">End Time</span>
              <span className="value">{optimizedRoute.estimatedEndTime}</span>
            </div>
          </div>
        </div>
      )}

      {/* Route Details */}
      {optimizedRoute && (
        <>
          <div className="route-actions">
            <button className="btn-secondary" onClick={exportRoute}>
              <Download size={16} />
              Export Route
            </button>
          </div>

          <div className="route-stops">
            <h3>Stop Sequence</h3>
            <div className="stops-timeline">
              {optimizedRoute.route.map((stop, index) => (
                <div key={index} className={`stop-item ${stop.type} ${stop.priority || ''}`}>
                  <div className="stop-marker">
                    {stop.type === 'depot' ? <MapPin size={20} /> : <CheckCircle size={20} />}
                  </div>
                  <div className="stop-content">
                    <div className="stop-header">
                      <span className="stop-number">Stop {stop.stopNumber}</span>
                      <span className="stop-time">
                        {stop.arrivalTime} - {stop.departureTime || 'Depart'}
                      </span>
                    </div>
                    <div className="stop-details">
                      <strong>{stop.name}</strong>
                      {stop.address && <p>{stop.address}</p>}
                      {stop.distance > 0 && (
                        <span className="stop-distance">{stop.distance} km</span>
                      )}
                      {stop.products && stop.products.length > 0 && (
                        <div className="stop-products">
                          {stop.products.map((p, i) => (
                            <span key={i} className="product-tag">
                              {p.quantity} {p.unit}
                            </span>
                          ))}
                        </div>
                      )}
                      {stop.expiryAlert && (
                        <div className="expiry-warning">
                          <AlertTriangle size={14} />
                          <span>Expiring: {new Date(stop.expiryDate).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  {index < optimizedRoute.route.length - 1 && (
                    <div className="stop-connector" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Pending Deliveries */}
      {!optimizedRoute && deliveries.length > 0 && (
        <div className="pending-deliveries">
          <h3>Pending Deliveries ({deliveries.length})</h3>
          <div className="deliveries-list">
            {deliveries.map((d) => (
              <div key={d.id} className={`delivery-item priority-${d.priority}`}>
                <span className="delivery-name">{d.customerName}</span>
                <span className="delivery-qty">{d.quantity} kg</span>
                {d.expiryDate && (
                  <span className="delivery-expiry">
                    <AlertTriangle size={14} />
                    {new Date(d.expiryDate).toLocaleDateString()}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Mock deliveries for demonstration
function getMockDeliveries() {
  const now = Date.now()
  return [
    { id: 'del-1', customerName: 'Local Grocery Store', quantity: 150, priority: 'high',
      address: '123 Main St, San Francisco, CA',
      location: { lat: 37.7849, lng: -122.4094 },
      expiryDate: new Date(now + 2 * 24 * 60 * 60 * 1000).toISOString(),
      products: [{ name: 'Lettuce', quantity: 50, unit: 'piece' }, { name: 'Spinach', quantity: 100, unit: 'box' }] },
    { id: 'del-2', customerName: 'Fresh Market', quantity: 200, priority: 'medium',
      address: '456 Oak Ave, San Francisco, CA',
      location: { lat: 37.7649, lng: -122.4294 },
      expiryDate: new Date(now + 5 * 24 * 60 * 60 * 1000).toISOString(),
      products: [{ name: 'Tomatoes', quantity: 100, unit: 'kg' }, { name: 'Peppers', quantity: 100, unit: 'kg' }] },
    { id: 'del-3', customerName: 'Community Kitchen', quantity: 300, priority: 'high',
      address: '789 Pine St, San Francisco, CA',
      location: { lat: 37.7549, lng: -122.4394 },
      expiryDate: new Date(now + 1 * 24 * 60 * 60 * 1000).toISOString(),
      products: [{ name: 'Carrots', quantity: 150, unit: 'kg' }, { name: 'Potatoes', quantity: 150, unit: 'kg' }] },
    { id: 'del-4', customerName: 'Organic Cafe', quantity: 100, priority: 'low',
      address: '321 Elm St, San Francisco, CA',
      location: { lat: 37.7949, lng: -122.3994 },
      products: [{ name: 'Herbs Mix', quantity: 50, unit: 'box' }, { name: 'Microgreens', quantity: 50, unit: 'box' }] },
    { id: 'del-5', customerName: 'Farmers Market Stand', quantity: 250, priority: 'medium',
      address: '555 Market St, San Francisco, CA',
      location: { lat: 37.7749, lng: -122.4144 },
      expiryDate: new Date(now + 7 * 24 * 60 * 60 * 1000).toISOString(),
      products: [{ name: 'Berries', quantity: 100, unit: 'box' }, { name: 'Apples', quantity: 150, unit: 'kg' }] },
  ]
}

export default RouteOptimizer
