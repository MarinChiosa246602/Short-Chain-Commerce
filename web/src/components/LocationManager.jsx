import React, { useState, useEffect } from 'react'
import { MapPin, Navigation, Globe, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react'

/**
 * Location Manager Component
 * Handles GPS coordinate capture and geofencing for automatic farm detection
 */
function LocationManager({ onLocationUpdate, onFarmDetected }) {
  const [location, setLocation] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [watchId, setWatchId] = useState(null)
  const [isTracking, setIsTracking] = useState(false)

  // Known farm locations for geofencing
  const [farmLocations] = useState([
    { id: 'farm-1', name: 'Green Valley Farm', lat: 37.7749, lng: -122.4194, radius: 5000 },
    { id: 'farm-2', name: 'Sunny Fields', lat: 37.8044, lng: -122.2712, radius: 5000 },
    { id: 'farm-3', name: 'Root Harvest Farm', lat: 37.7849, lng: -122.4094, radius: 5000 },
    { id: 'warehouse-1', name: 'Warehouse A', lat: 37.7649, lng: -122.4294, radius: 1000 },
    { id: 'warehouse-2', name: 'Warehouse B', lat: 37.7549, lng: -122.4394, radius: 1000 },
    { id: 'dc-1', name: 'Distribution Center', lat: 37.7949, lng: -122.3994, radius: 2000 },
  ])

  // Request location permission
  const requestLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser')
      return
    }

    setLoading(true)
    setError(null)

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const newLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp
        }

        setLocation(newLocation)
        setLoading(false)

        // Check for nearby farm
        checkNearbyFarm(newLocation)

        // Call parent callback
        if (onLocationUpdate) {
          onLocationUpdate(newLocation)
        }
      },
      (err) => {
        setError(getGeoErrorMessage(err.code))
        setLoading(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    )
  }

  // Start continuous location tracking
  const startTracking = () => {
    if (!navigator.geolocation) return

    const id = navigator.geolocation.watchPosition(
      (position) => {
        const newLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp
        }

        setLocation(newLocation)
        checkNearbyFarm(newLocation)

        if (onLocationUpdate) {
          onLocationUpdate(newLocation)
        }
      },
      (err) => {
        setError(getGeoErrorMessage(err.code))
      },
      {
        enableHighAccuracy: true,
        timeout: 30000,
        maximumAge: 10000
      }
    )

    setWatchId(id)
    setIsTracking(true)
    setError(null)
  }

  // Stop tracking
  const stopTracking = () => {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId)
      setWatchId(null)
      setIsTracking(false)
    }
  }

  // Check if location is within range of a known farm
  const checkNearbyFarm = (loc) => {
    for (const farm of farmLocations) {
      const distance = calculateDistance(
        loc.latitude, loc.longitude,
        farm.lat, farm.lng
      )

      if (distance <= farm.radius) {
        const farmData = {
          id: farm.id,
          name: farm.name,
          distance: Math.round(distance)
        }

        if (onFarmDetected) {
          onFarmDetected(farmData)
        }

        return farmData
      }
    }
    return null
  }

  // Calculate distance between two coordinates (Haversine formula)
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

  const getGeoErrorMessage = (code) => {
    switch (code) {
      case 1:
        return 'Location permission denied. Please enable location access in your browser settings.'
      case 2:
        return 'Location unavailable. Please check your device settings.'
      case 3:
        return 'Location request timed out. Please try again.'
      default:
        return 'Unable to get your location.'
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId)
      }
    }
  }, [watchId])

  // Format coordinates for display
  const formatCoordinates = (loc) => {
    if (!loc) return 'N/A'
    return `${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}`
  }

  return (
    <div className="location-manager">
      <div className="location-header">
        <h4>
          <MapPin size={18} />
          Location Services
        </h4>
        {location && (
          <span className="location-status">
            <CheckCircle size={14} />
            Location Active
          </span>
        )}
      </div>

      {error && (
        <div className="location-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="location-info">
        <div className="info-row">
          <span className="info-label">Coordinates:</span>
          <span className="info-value">
            {formatCoordinates(location)}
          </span>
        </div>

        {location && (
          <>
            <div className="info-row">
              <span className="info-label">Accuracy:</span>
              <span className="info-value">{Math.round(location.accuracy)}m</span>
            </div>
            <div className="info-row">
              <span className="info-label">Last Updated:</span>
              <span className="info-value">
                {new Date(location.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </>
        )}
      </div>

      <div className="location-actions">
        {!isTracking ? (
          <button
            className="location-btn"
            onClick={requestLocation}
            disabled={loading}
          >
            <Navigation size={16} />
            {loading ? 'Getting Location...' : 'Get Current Location'}
          </button>
        ) : (
          <button
            className="location-btn tracking"
            onClick={stopTracking}
          >
            <RefreshCw size={16} className="spin" />
            Stop Tracking
          </button>
        )}

        <button
          className="location-btn secondary"
          onClick={startTracking}
          disabled={isTracking}
        >
          <Globe size={16} />
          Start Tracking
        </button>
      </div>

      {location && (
        <div className="nearby-location">
          <small>
            <MapPin size={12} />
            Use this location for automatic farm detection
          </small>
        </div>
      )}
    </div>
  )
}

export default LocationManager
