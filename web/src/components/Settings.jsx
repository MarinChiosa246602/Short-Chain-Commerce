import React, { useState } from 'react'
import { Save, RefreshCw, Upload, Camera } from 'lucide-react'

function Settings() {
  const [settings, setSettings] = useState({
    confidenceThreshold: 0.7,
    detectionConfidence: 0.5,
    ocrLanguage: 'en',
    useGpu: false,
    sourceFarm: '',
    destination: '',
    maxBatchSize: 50,
  })

  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    localStorage.setItem('extractionSettings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleReset = () => {
    setSettings({
      confidenceThreshold: 0.7,
      detectionConfidence: 0.5,
      ocrLanguage: 'en',
      useGpu: false,
      sourceFarm: '',
      destination: '',
      maxBatchSize: 50,
    })
  }

  return (
    <div className="settings">
      <div className="page-header">
        <h1>Settings</h1>
        <p className="subtitle">Configure extraction pipeline preferences</p>
      </div>

      <div className="settings-grid">
        {/* General Settings */}
        <div className="settings-section">
          <h3>General Settings</h3>

          <div className="setting-group">
            <label htmlFor="sourceFarm">Default Source Farm</label>
            <input
              id="sourceFarm"
              type="text"
              value={settings.sourceFarm}
              onChange={(e) => setSettings({ ...settings, sourceFarm: e.target.value })}
              placeholder="e.g., Farm-A"
            />
            <small>Used as default for new extractions</small>
          </div>

          <div className="setting-group">
            <label htmlFor="destination">Default Destination</label>
            <input
              id="destination"
              type="text"
              value={settings.destination}
              onChange={(e) => setSettings({ ...settings, destination: e.target.value })}
              placeholder="e.g., Warehouse-B"
            />
            <small>Used as default for new extractions</small>
          </div>
        </div>

        {/* Detection Settings */}
        <div className="settings-section">
          <h3>Detection Settings</h3>

          <div className="setting-group">
            <label htmlFor="confidence">Confidence Threshold</label>
            <input
              id="confidence"
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={settings.confidenceThreshold}
              onChange={(e) => setSettings({ ...settings, confidenceThreshold: parseFloat(e.target.value) })}
            />
            <small>Detection confidence (0-1). Higher = more accurate but may miss items</small>
          </div>

          <div className="setting-group">
            <label htmlFor="detectionConfidence">Detection Confidence</label>
            <input
              id="detectionConfidence"
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={settings.detectionConfidence}
              onChange={(e) => setSettings({ ...settings, detectionConfidence: parseFloat(e.target.value) })}
            />
            <small>Minimum confidence for object detection</small>
          </div>

          <div className="setting-group">
            <label htmlFor="maxBatchSize">Maximum Batch Size</label>
            <input
              id="maxBatchSize"
              type="number"
              min="1"
              max="100"
              value={settings.maxBatchSize}
              onChange={(e) => setSettings({ ...settings, maxBatchSize: parseInt(e.target.value) })}
            />
            <small>Maximum images per batch request</small>
          </div>
        </div>

        {/* OCR Settings */}
        <div className="settings-section">
          <h3>OCR Settings</h3>

          <div className="setting-group">
            <label htmlFor="ocrLanguage">OCR Language</label>
            <select
              id="ocrLanguage"
              value={settings.ocrLanguage}
              onChange={(e) => setSettings({ ...settings, ocrLanguage: e.target.value })}
            >
              <option value="en">English</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="es">Spanish</option>
              <option value="it">Italian</option>
            </select>
            <small>Language for text recognition</small>
          </div>

          <div className="setting-group toggle">
            <label htmlFor="useGpu">Use GPU Acceleration</label>
            <label className="toggle-switch">
              <input
                id="useGpu"
                type="checkbox"
                checked={settings.useGpu}
                onChange={(e) => setSettings({ ...settings, useGpu: e.target.checked })}
              />
              <span className="slider"></span>
            </label>
            <small>Enable GPU for faster processing (requires NVIDIA GPU)</small>
          </div>
        </div>

        {/* Actions */}
        <div className="settings-section actions-section">
          <div className="action-buttons">
            <button className="btn-primary" onClick={handleSave}>
              <Save size={18} />
              Save Changes
            </button>
            <button className="btn-secondary" onClick={handleReset}>
              <RefreshCw size={18} />
              Reset to Defaults
            </button>
          </div>

          {saved && (
            <div className="save-message">
              Settings saved successfully!
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Settings
