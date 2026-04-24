import React, { useState, useRef, useEffect } from 'react'
import { Camera, Plus, Trash2, CheckCircle, X, Upload, Package, AlertCircle } from 'lucide-react'
import api from '../services/api'

/**
 * Batch Scanner Component
 * Allows capturing and processing multiple products in sequence
 */
function BatchScanner({ onComplete, onAddToBatch }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)

  const [isCameraActive, setIsCameraActive] = useState(false)
  const [batchItems, setBatchItems] = useState([])
  const [currentPreview, setCurrentPreview] = useState(null)
  const [currentProcessing, setCurrentProcessing] = useState(false)
  const [error, setError] = useState(null)

  // Start camera
  const startCamera = async () => {
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }

      const constraints = {
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }

      setIsCameraActive(true)
      setError(null)
    } catch (err) {
      setError('Unable to access camera. Please check permissions.')
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    setIsCameraActive(false)
  }

  const captureAndProcess = async () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    const imageData = canvas.toDataURL('image/jpeg', 0.95)

    canvas.toBlob(async (blob) => {
      const file = new File([blob], `batch_${Date.now()}.jpg`, { type: 'image/jpeg' })
      setCurrentProcessing(true)
      setError(null)

      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await api.extractData(formData)

        const batchItem = {
          id: `batch-${Date.now()}`,
          image: imageData,
          timestamp: new Date().toISOString(),
          result: response
        }

        setBatchItems(prev => [...prev, batchItem])

        if (onAddToBatch) {
          onAddToBatch(batchItem)
        }

        setCurrentPreview(null)
      } catch (err) {
        setError('Failed to process image. Please try again.')
      } finally {
        setCurrentProcessing(false)
      }
    }, 'image/jpeg', 0.95)
  }

  const removeItem = (id) => {
    setBatchItems(prev => prev.filter(item => item.id !== id))
  }

  const clearBatch = () => {
    setBatchItems([])
    setError(null)
  }

  const exportBatch = () => {
    const data = {
      batchId: `batch-${Date.now()}`,
      exportTime: new Date().toISOString(),
      itemCount: batchItems.length,
      items: batchItems.map(item => ({
        timestamp: item.timestamp,
        extraction: item.result
      }))
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `batch_${data.batchId}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const closeCamera = () => {
    stopCamera()
    if (batchItems.length > 0 && onComplete) {
      onComplete(batchItems)
    }
  }

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  return (
    <div className="batch-scanner">
      <div className="batch-header">
        <div className="batch-title">
          <Package size={24} />
          <div>
            <h3>Batch Scanner</h3>
            <p>Capture multiple products in one session</p>
          </div>
        </div>
        <div className="batch-stats">
          <span className="item-count">{batchItems.length} items captured</span>
        </div>
      </div>

      {error && (
        <div className="batch-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="batch-camera">
        {!isCameraActive ? (
          <div className="camera-placeholder">
            <Camera size={48} />
            <p>Click below to activate camera</p>
            <button className="start-btn" onClick={startCamera}>
              <Camera size={20} />
              Start Camera
            </button>
          </div>
        ) : (
          <div className="camera-feed-container">
            <video ref={videoRef} autoPlay playsInline muted className="video-feed" />
            <canvas ref={canvasRef} className="capture-canvas" />

            {currentProcessing && (
              <div className="processing-overlay">
                <div className="processing-indicator">
                  <div className="spinner" />
                  <span>Processing...</span>
                </div>
              </div>
            )}

            <div className="batch-capture-controls">
              <button
                className="capture-btn-large"
                onClick={captureAndProcess}
                disabled={currentProcessing}
              >
                <Camera size={32} />
              </button>
            </div>
          </div>
        )}
      </div>

      {batchItems.length > 0 && (
        <div className="batch-items">
          <div className="batch-items-header">
            <h4>Captured Items ({batchItems.length})</h4>
            <div className="batch-actions">
              <button className="btn-small" onClick={exportBatch}>
                <Upload size={14} />
                Export Batch
              </button>
              <button className="btn-small danger" onClick={clearBatch}>
                <Trash2 size={14} />
                Clear All
              </button>
            </div>
          </div>

          <div className="batch-items-grid">
            {batchItems.map((item) => (
              <div key={item.id} className="batch-item">
                <div className="batch-item-image">
                  <img src={item.image} alt="Captured" />
                </div>
                <div className="batch-item-info">
                  <span className="item-time">
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </span>
                  {item.result?.data?.products?.map((product, idx) => (
                    <div key={idx} className="item-product">
                      <span className="product-name">{product.product_name}</span>
                      <span className="product-qty">{product.quantity} {product.unit}</span>
                    </div>
                  ))}
                </div>
                <button className="remove-item" onClick={() => removeItem(item.id)}>
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="batch-footer">
        <button className="finish-btn" onClick={closeCamera}>
          <CheckCircle size={20} />
          Finish & Save Batch
        </button>
      </div>
    </div>
  )
}

export default BatchScanner
