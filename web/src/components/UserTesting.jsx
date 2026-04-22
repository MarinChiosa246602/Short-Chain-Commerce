import React, { useState, useEffect } from 'react'
import { Play, Pause, Flag, Target, Eye, Brain } from 'lucide-react'

function UserTesting() {
  const [active, setActive] = useState(false)
  const [sessionData, setSessionData] = useState({
    startTime: null,
    actions: [],
    heatmaps: [],
    errors: [],
  })

  useEffect(() => {
    if (active) {
      sessionData.startTime = Date.now()
      startTracking()
    } else {
      stopTracking()
    }
  }, [active])

  const startTracking = () => {
    // Track user interactions
    const handleInteraction = (event) => {
      const action = {
        type: event.type,
        target: event.target.tagName,
        timestamp: Date.now() - sessionData.startTime,
        coordinates: { x: event.clientX, y: event.clientY },
      }
      setSessionData((prev) => ({ ...prev, actions: [...prev.actions, action] }))
    }

    document.addEventListener('click', handleInteraction)
    document.addEventListener('mousemove', handleInteraction)
  }

  const stopTracking = () => {
    document.removeEventListener('click', () => {})
    document.removeEventListener('mousemove', () => {})
  }

  const exportSession = () => {
    const data = {
      ...sessionData,
      duration: Date.now() - sessionData.startTime,
      totalActions: sessionData.actions.length,
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `user_session_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const clearData = () => {
    setSessionData({
      startTime: null,
      actions: [],
      heatmaps: [],
      errors: [],
    })
  }

  return (
    <div className="user-testing-panel">
      <div className="testing-header">
        <h3>User Testing Mode</h3>
        <div className="testing-controls">
          <button
            className={`btn-icon ${active ? 'active' : ''}`}
            onClick={() => setActive(!active)}
            title={active ? 'Stop Tracking' : 'Start Tracking'}
          >
            {active ? <Pause size={20} /> : <Play size={20} />}
          </button>
          <button className="btn-icon" onClick={exportSession} title="Export Session Data">
            <Target size={20} />
          </button>
          <button className="btn-icon" onClick={clearData} title="Clear Data">
            <Eye size={20} />
          </button>
        </div>
      </div>

      {active && (
        <div className="testing-status">
          <div className="status-item">
            <Brain size={16} />
            <span>Actions Recorded: {sessionData.actions.length}</span>
          </div>
          <div className="status-item">
            <Target size={16} />
            <span>Active Session</span>
          </div>
        </div>
      )}

      <div className="testing-info">
        <h4>Testing Features</h4>
        <ul>
          <li>Track all user interactions (clicks, movements)</li>
          <li>Record action timestamps and coordinates</li>
          <li>Export session data for analysis</li>
          <li>Identify usability issues</li>
        </ul>
        <p className="info-note">
          Enable tracking mode to start collecting user interaction data for UX improvements.
        </p>
      </div>
    </div>
  )
}

export default UserTesting
