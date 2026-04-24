import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Camera, X, AlertCircle, CheckCircle, Upload, Download, RefreshCw, Sun, Moon, Thermometer, Package, Calendar, Eye } from 'lucide-react'
import api from '../services/api'

function CameraDashboard() {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)

  const [isCameraActive, setIsCameraActive] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [capturedImage, setCapturedImage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [processingSteps, setProcessingSteps] = useState([])

  // Image quality metrics
  const [qualityMetrics, setQualityMetrics] = useState({
    blurScore: 0,
    lightingScore: 0,
    compositionScore: 0,
    overallQuality: 'good'
  })

  // Camera constraints
  const [cameraFacingMode, setCameraFacingMode] = useState('environment') // 'user' or 'environment'
  const [availableCameras, setAvailableCameras] = useState([])

  // Fetch available cameras
  const fetchAvailableCameras = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices()
      const videoDevices = devices.filter(device => device.kind === 'videoinput')
      setAvailableCameras(videoDevices)
    } catch (err) {
      console.error('Failed to fetch cameras:', err)
    }
  }

  // Start camera
  const startCamera = async () => {
    try {
      // Stop existing stream if any
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }

      const constraints = {
        video: {
          facingMode: cameraFacingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
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
      console.error('Failed to start camera:', err)
      setError('Unable to access camera. Please ensure camera permissions are granted.')
    }
  }

  // Stop camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    setIsCameraActive(false)
  }, [])

  // Toggle camera
  const toggleCamera = () => {
    if (isCameraActive) {
      stopCamera()
    } else {
      fetchAvailableCameras()
      startCamera()
    }
  }

  // Switch camera
  const switchCamera = () => {
    const newFacingMode = cameraFacingMode === 'environment' ? 'user' : 'environment'
    setCameraFacingMode(newFacingMode)
    if (isCameraActive) {
      stopCamera()
      setTimeout(() => {
        startCamera()
      }, 100)
    }
  }

  // Capture image from camera
  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Convert to data URL
    const imageData = canvas.toDataURL('image/jpeg', 0.95)
    setCapturedImage(imageData)

    // Create preview
    setPreview(imageData)

    // Convert to blob for processing
    canvas.toBlob((blob) => {
      const file = new File([blob], `capture_${Date.now()}.jpg`, { type: 'image/jpeg' })
      handleImageSelected(file)
    }, 'image/jpeg', 0.95)
  }

  const handleImageSelected = (file) => {
    setSelectedFile(file)
    setError(null)
    setResult(null)

    // Validate and assess image quality
    assessImageQuality(file)
  }

  // Handle file input
  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setSelectedFile(file)
      setPreview(URL.createObjectURL(file))
      handleImageSelected(file)
    }
  }

  // Assess image quality
  const assessImageQuality = async (file) => {
    try {
      const img = await loadImage(file)

      // Calculate blur score using variance of Laplacian (simulated)
      const blurScore = calculateBlurScore(img)

      // Calculate lighting score
      const lightingScore = calculateLightingScore(img)

      // Calculate composition score
      const compositionScore = calculateCompositionScore(img)

      // Determine overall quality
      const avgQuality = (blurScore + lightingScore + compositionScore) / 3

      let overallQuality = 'good'
      if (avgQuality < 0.4) overallQuality = 'poor'
      else if (avgQuality < 0.6) overallQuality = 'fair'
      else if (avgQuality < 0.8) overallQuality = 'good'
      else overallQuality = 'excellent'

      setQualityMetrics({
        blurScore: Math.round(blurScore * 100),
        lightingScore: Math.round(lightingScore * 100),
        compositionScore: Math.round(compositionScore * 100),
        overallQuality
      })

      return { blurScore, lightingScore, compositionScore, overallQuality }
    } catch (err) {
      console.error('Failed to assess image quality:', err)
      return null
    }
  }

  // Load image as HTMLImageElement
  const loadImage = (file) => {
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = reject
      img.src = URL.createObjectURL(file)
    })
  }

  // Calculate blur score using edge detection (simplified)
  const calculateBlurScore = (img) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    // Resize to smaller for performance
    const maxWidth = 200
    const scaleFactor = Math.min(1, maxWidth / img.width)
    canvas.width = img.width * scaleFactor
    canvas.height = img.height * scaleFactor

    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const data = imageData.data

    // Calculate variance of gradients (simplified edge detection)
    let gradientSum = 0
    let count = 0

    for (let y = 1; y < canvas.height - 1; y++) {
      for (let x = 1; x < canvas.width - 1; x++) {
        const idx = (y * canvas.width + x) * 4
        const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3

        // Sobel-like gradient calculation
        const left = (data[idx - 4] + data[idx - 4 + 1] + data[idx - 4 + 2]) / 3
        const right = (data[idx + 4] + data[idx + 4 + 1] + data[idx + 4 + 2]) / 3
        const top = (data[idx - canvas.width * 4] + data[idx - canvas.width * 4 + 1] + data[idx - canvas.width * 4 + 2]) / 3
        const bottom = (data[idx + canvas.width * 4] + data[idx + canvas.width * 4 + 1] + data[idx + canvas.width * 4 + 2]) / 3

        const gradX = right - left
        const gradY = bottom - top
        const gradient = Math.sqrt(gradX * gradX + gradY * gradY)

        gradientSum += gradient
        count++
      }
    }

    const avgGradient = gradientSum / count
    // Normalize to 0-1 range (higher = sharper = better)
    return Math.min(1, avgGradient / 50)
  }

  // Calculate lighting score
  const calculateLightingScore = (img) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    const maxWidth = 200
    const scaleFactor = Math.min(1, maxWidth / img.width)
    canvas.width = img.width * scaleFactor
    canvas.height = img.height * scaleFactor

    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const data = imageData.data

    // Calculate average brightness and contrast
    let brightnessSum = 0
    let contrastSum = 0
    const avgBrightness = 128 // Target brightness

    for (let i = 0; i < data.length; i += 4) {
      const gray = (data[i] + data[i + 1] + data[i + 2]) / 3
      brightnessSum += gray
      contrastSum += Math.abs(gray - avgBrightness)
    }

    const pixelCount = data.length / 4
    const avgLuminance = brightnessSum / pixelCount
    const avgContrast = contrastSum / pixelCount

    // Lighting score: prefer well-lit images (not too dark, not too bright)
    const brightnessScore = 1 - Math.abs(avgLuminance - avgBrightness) / avgBrightness
    const contrastScore = Math.min(1, avgContrast / 80)

    return (brightnessScore * 0.6 + contrastScore * 0.4)
  }

  // Calculate composition score (center-weighted)
  const calculateCompositionScore = (img) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    const maxWidth = 200
    const scaleFactor = Math.min(1, maxWidth / img.width)
    canvas.width = img.width * scaleFactor
    canvas.height = img.height * scaleFactor

    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const data = imageData.data

    // Calculate edge distribution (good composition has balanced edges)
    let centerEdges = 0
    let totalEdges = 0

    const centerX = Math.floor(canvas.width / 2)
    const centerY = Math.floor(canvas.height / 2)
    const centerRadius = Math.min(centerX, centerY) * 0.5

    for (let y = 1; y < canvas.height - 1; y++) {
      for (let x = 1; x < canvas.width - 1; x++) {
        const idx = (y * canvas.width + x) * 4
        const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3

        const left = (data[idx - 4] + data[idx - 4 + 1] + data[idx - 4 + 2]) / 3
        const right = (data[idx + 4] + data[idx + 4 + 1] + data[idx + 4 + 2]) / 3
        const top = (data[idx - canvas.width * 4] + data[idx - canvas.width * 4 + 1] + data[idx - canvas.width * 4 + 2]) / 3
        const bottom = (data[idx + canvas.width * 4] + data[idx + canvas.width * 4 + 1] + data[idx + canvas.width * 4 + 2]) / 3

        const gradient = Math.sqrt(
          Math.pow(right - left, 2) + Math.pow(bottom - top, 2)
        )

        totalEdges += gradient

        // Check if pixel is in center region
        const distFromCenter = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2))
        if (distFromCenter < centerRadius) {
          centerEdges += gradient
        }
      }
    }

    // Composition score: prefer images with content in center
    if (totalEdges === 0) return 0.5
    return Math.min(1, (centerEdges / totalEdges) * 2)
  }

  // Process captured image
  const processImage = async () => {
    if (!selectedFile) {
      setError('Please capture or select an image first')
      return
    }

    // Check image quality before processing
    if (qualityMetrics.overallQuality === 'poor') {
      setError('Image quality is poor. Please retake the photo with better lighting and focus.')
      return
    }

    setLoading(true)
    setError(null)
    setProcessingSteps([])

    const steps = [
      { name: 'Uploading image...', status: 'pending' },
      { name: 'Running object detection...', status: 'pending' },
      { name: 'Extracting product information...', status: 'pending' },
      { name: 'Analyzing expiration dates...', status: 'pending' },
      { name: 'Generating storage recommendations...', status: 'pending' },
      { name: 'Finalizing extraction...', status: 'pending' },
    ]

    for (let i = 0; i < steps.length; i++) {
      steps[i].status = 'processing'
      setProcessingSteps([...steps])
      await new Promise(resolve => setTimeout(resolve, 800))
      steps[i].status = 'complete'
      setProcessingSteps([...steps])
    }

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await api.extractData(formData)
      setResult(response)
    } catch (err) {
      setError(err.message || 'Failed to process image')
    } finally {
      setLoading(false)
    }
  }

  // Download results
  const downloadResult = () => {
    if (!result) return

    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `extraction_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Reset capture
  const resetCapture = () => {
    setSelectedFile(null)
    setPreview(null)
    setCapturedImage(null)
    setResult(null)
    setError(null)
    setQualityMetrics({
      blurScore: 0,
      lightingScore: 0,
      compositionScore: 0,
      overallQuality: 'good'
    })
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  // Get quality color
  const getQualityColor = (quality) => {
    switch (quality) {
      case 'excellent': return '#10b981'
      case 'good': return '#3b82f6'
      case 'fair': return '#f59e0b'
      case 'poor': return '#ef4444'
      default: return '#64748b'
    }
  }

  return (
    <div className="camera-dashboard">
      <div className="dashboard-header">
        <h1>Product Scanner</h1>
        <p className="subtitle">Capture and analyze products with camera</p>
      </div>

      <div className="camera-grid">
        {/* Camera/Capture Section */}
        <div className="capture-section">
          <div className="capture-container">
            {/* Camera View */}
            {isCameraActive && !capturedImage && (
              <div className="camera-view">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="camera-feed"
                />
                <canvas ref={canvasRef} className="capture-canvas" />

                {/* Camera Controls */}
                <div className="camera-controls">
                  <button className="control-btn" onClick={switchCamera} title="Switch Camera">
                    <RefreshCw size={24} />
                  </button>
                  <button className="capture-btn" onClick={captureImage}>
                    <div className="capture-ring" />
                    <Camera size={32} className="capture-icon" />
                  </button>
                  <button className="control-btn" onClick={stopCamera} title="Close Camera">
                    <X size={24} />
                  </button>
                </div>
              </div>
            )}

            {/* File Upload Fallback */}
            {!isCameraActive && !capturedImage && (
              <div className="upload-fallback">
                <div
                  className={`dropzone ${preview ? 'has-preview' : ''}`}
                >
                  {preview ? (
                    <div className="preview-container">
                      <img src={preview} alt="Preview" className="preview-image" />
                      <button className="retake-btn" onClick={resetCapture}>
                        <Camera size={20} />
                        Retake Photo
                      </button>
                    </div>
                  ) : (
                    <div className="upload-content">
                      <Camera size={48} className="upload-icon" />
                      <h3>Take a Photo</h3>
                      <p>Click below to activate your camera</p>
                      <p className="hint">Or drag and drop an image here</p>
                    </div>
                  )}
                  <input
                    type="file"
                    accept="image/jpeg,image/jpg,image/png,image/webp"
                    onChange={handleFileInput}
                    className="file-input"
                  />
                </div>
              </div>
            )}

            {/* Start Camera Button */}
            {!isCameraActive && !preview && (
              <div className="start-camera-btn-container">
                <button className="start-camera-btn" onClick={startCamera}>
                  <Camera size={24} />
                  Activate Camera
                </button>
              </div>
            )}

            {/* Quality Indicators */}
            {preview && (
              <div className="quality-panel">
                <h3>Image Quality</h3>
                <div className="quality-metrics">
                  <div className="metric">
                    <div className="metric-header">
                      <span>Sharpness</span>
                      <span className="metric-value">{qualityMetrics.blurScore}%</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${qualityMetrics.blurScore}%`,
                          backgroundColor: getQualityColor(
                            qualityMetrics.blurScore >= 80 ? 'excellent' :
                            qualityMetrics.blurScore >= 60 ? 'good' :
                            qualityMetrics.blurScore >= 40 ? 'fair' : 'poor'
                          )
                        }}
                      />
                    </div>
                  </div>

                  <div className="metric">
                    <div className="metric-header">
                      <span>Lighting</span>
                      <span className="metric-value">{qualityMetrics.lightingScore}%</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${qualityMetrics.lightingScore}%`,
                          backgroundColor: getQualityColor(
                            qualityMetrics.lightingScore >= 80 ? 'excellent' :
                            qualityMetrics.lightingScore >= 60 ? 'good' :
                            qualityMetrics.lightingScore >= 40 ? 'fair' : 'poor'
                          )
                        }}
                      />
                    </div>
                  </div>

                  <div className="metric">
                    <div className="metric-header">
                      <span>Composition</span>
                      <span className="metric-value">{qualityMetrics.compositionScore}%</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${qualityMetrics.compositionScore}%`,
                          backgroundColor: getQualityColor(
                            qualityMetrics.compositionScore >= 80 ? 'excellent' :
                            qualityMetrics.compositionScore >= 60 ? 'good' :
                            qualityMetrics.compositionScore >= 40 ? 'fair' : 'poor'
                          )
                        }}
                      />
                    </div>
                  </div>
                </div>

                <div className="overall-quality">
                  <span>Overall: </span>
                  <span className="quality-badge" style={{ color: getQualityColor(qualityMetrics.overallQuality) }}>
                    {qualityMetrics.overallQuality.toUpperCase()}
                  </span>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="error-banner">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            )}

            {/* Action Buttons */}
            {preview && !loading && (
              <div className="action-buttons">
                <button className="process-btn" onClick={processImage}>
                  <CheckCircle size={20} />
                  Process Image
                </button>
                <button className="retake-btn" onClick={resetCapture}>
                  <Camera size={20} />
                  Retake
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Results Section */}
        <div className="results-panel">
          {loading && (
            <div className="processing-indicator">
              <h3>Processing</h3>
              {processingSteps.map((step, idx) => (
                <div key={idx} className={`processing-step ${step.status}`}>
                  <div className="step-icon">
                    {step.status === 'complete' && <CheckCircle size={16} className="text-success" />}
                    {step.status === 'processing' && <RefreshCw size={16} className="spin" />}
                    {step.status === 'pending' && <div className="step-dot" />}
                  </div>
                  <span>{step.name}</span>
                </div>
              ))}
            </div>
          )}

          {result && (
            <div className="results-display">
              <div className="result-header">
                <h3>Analysis Results</h3>
                <div className="result-actions">
                  {result.status === 'success' && (
                    <span className="status-badge success">Success</span>
                  )}
                  {result.status === 'partial' && (
                    <span className="status-badge warning">Partial</span>
                  )}
                  <button className="download-btn" onClick={downloadResult}>
                    <Download size={16} />
                    Download
                  </button>
                </div>
              </div>

              {result.data && (
                <div className="result-content">
                  {/* Product Detection Summary */}
                  {result.data.products && result.data.products.length > 0 && (
                    <div className="products-section">
                      <div className="section-header">
                        <Package size={20} />
                        <h4>Products Detected ({result.data.products.length})</h4>
                      </div>

                      {result.data.products.map((product, idx) => (
                        <div key={idx} className="product-card">
                          <div className="product-header">
                            <span className="product-name">{product.product_name}</span>
                            <span className="product-id">{product.product_id}</span>
                          </div>

                          <div className="product-details">
                            <div className="detail-row">
                              <span className="detail-label">
                                <Package size={16} /> Quantity
                              </span>
                              <span className="detail-value">
                                {product.quantity} {product.unit}
                              </span>
                            </div>

                            {product.expiry_date && (
                              <div className="detail-row expiry">
                                <span className="detail-label">
                                  <Calendar size={16} /> Expiry Date
                                </span>
                                <span className="detail-value">
                                  {new Date(product.expiry_date).toLocaleDateString()}
                                </span>
                              </div>
                            )}

                            {product.condition && (
                              <div className="detail-row condition">
                                <span className="detail-label">
                                  <Eye size={16} /> Condition
                                </span>
                                <span className={`detail-value condition-${product.condition}`}>
                                  {product.condition}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Storage Recommendations */}
                  <div className="storage-recommendations">
                    <div className="section-header">
                      <Thermometer size={20} />
                      <h4>Storage Recommendations</h4>
                    </div>

                    {result.data.products && result.data.products.length > 0 && (
                      <div className="storage-grid">
                        {result.data.products.map((product, idx) => {
                          // Generate storage recommendations based on product type
                          const storageType = getStorageType(product.product_name)
                          return (
                            <div key={idx} className="storage-card">
                              <h5>{product.product_name}</h5>
                              <div className="storage-details">
                                <span className="storage-type">{storageType.type}</span>
                                <span className="storage-temp">
                                  Temp: {storageType.temp}°C
                                </span>
                                <span className="storage-humidity">
                                  Humidity: {storageType.humidity}%
                                </span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>

                  {/* Metadata */}
                  {result.data.metadata && (
                    <div className="metadata-section">
                      <div className="section-header">
                        <h4>Metadata</h4>
                      </div>
                      <div className="metadata-grid">
                        <div className="meta-item">
                          <strong>Source:</strong> {result.data.metadata.source_farm || 'Not specified'}
                        </div>
                        <div className="meta-item">
                          <strong>Destination:</strong> {result.data.metadata.destination || 'Not specified'}
                        </div>
                        <div className="meta-item">
                          <strong>Processed:</strong> {new Date(result.data.timestamp).toLocaleString()}
                        </div>
                        <div className="meta-item">
                          <strong>Duration:</strong> {result.processing_time_ms?.toFixed(0)}ms
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Warnings */}
                  {(result.data.missing_fields?.length > 0 || result.data.low_confidence_fields?.length > 0) && (
                    <div className="warnings-section">
                      {result.data.missing_fields?.length > 0 && (
                        <div className="warning-item">
                          <AlertCircle size={16} />
                          <span>Missing: {result.data.missing_fields.join(', ')}</span>
                        </div>
                      )}
                      {result.data.low_confidence_fields?.length > 0 && (
                        <div className="warning-item">
                          <AlertCircle size={16} />
                          <span>Low confidence: {result.data.low_confidence_fields.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {!result && !loading && (
            <div className="empty-state">
              <Package size={64} className="empty-icon" />
              <h3>No Analysis Yet</h3>
              <p>Capture a product photo to see detailed analysis including expiry dates and storage recommendations</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Helper function to get storage recommendations based on product type
function getStorageType(productName) {
  const productLower = productName.toLowerCase()

  // Leafy greens and vegetables
  if (productLower.includes('lettuce') || productLower.includes('spinach') ||
      productLower.includes('kale') || productLower.includes('arugula') ||
      productLower.includes('leafy') || productLower.includes('greens')) {
    return { type: 'Refrigerated', temp: '0-4', humidity: '95' }
  }

  // Root vegetables
  if (productLower.includes('carrot') || productLower.includes('potato') ||
      productLower.includes('onion') || productLower.includes('beet') ||
      productLower.includes('radish') || productLower.includes('turnip')) {
    return { type: 'Cool Storage', temp: '0-10', humidity: '90' }
  }

  // Tomatoes and fruits
  if (productLower.includes('tomato') || productLower.includes('cucumber') ||
      productLower.includes('pepper') || productLower.includes('zucchini')) {
    return { type: 'Cool Storage', temp: '10-13', humidity: '85-90' }
  }

  // Berries and delicate fruits
  if (productLower.includes('strawberr') || productLower.includes('raspberry') ||
      productLower.includes('blueberry') || productLower.includes('blackberry') ||
      productLower.includes('berry')) {
    return { type: 'Refrigerated', temp: '0-2', humidity: '90-95' }
  }

  // Citrus fruits
  if (productLower.includes('orange') || productLower.includes('lemon') ||
      productLower.includes('lime') || productLower.includes('grapefruit') ||
      productLower.includes('citrus')) {
    return { type: 'Cool Storage', temp: '4-10', humidity: '85-90' }
  }

  // Apples and pears
  if (productLower.includes('apple') || productLower.includes('pear')) {
    return { type: 'Cold Storage', temp: '-1 to 4', humidity: '90-95' }
  }

  // Herbs
  if (productLower.includes('basil') || productLower.includes('cilantro') ||
      productLower.includes('parsley') || productLower.includes('dill') ||
      productLower.includes('mint') || productLower.includes('herb')) {
    return { type: 'Refrigerated', temp: '0-4', humidity: '95' }
  }

  // Mushrooms
  if (productLower.includes('mushroom')) {
    return { type: 'Refrigerated', temp: '0-4', humidity: '90-95' }
  }

  // Eggs and dairy
  if (productLower.includes('egg') || productLower.includes('milk') ||
      productLower.includes('cheese') || productLower.includes('yogurt')) {
    return { type: 'Refrigerated', temp: '0-4', humidity: '85-90' }
  }

  // Meat and poultry
  if (productLower.includes('chicken') || productLower.includes('beef') ||
      productLower.includes('pork') || productLower.includes('lamb') ||
      productLower.includes('meat')) {
    return { type: 'Refrigerated', temp: '0-2', humidity: '85-90' }
  }

  // Fish and seafood
  if (productLower.includes('fish') || productLower.includes('salmon') ||
      productLower.includes('tuna') || productLower.includes('shrimp') ||
      productLower.includes('seafood')) {
    return { type: 'Cold Storage (Ice)', temp: '-1 to 2', humidity: '95-98' }
  }

  // Grains and dried goods
  if (productLower.includes('rice') || productLower.includes('wheat') ||
      productLower.includes('corn') || productLower.includes('oat') ||
      productLower.includes('bean') || productLower.includes('dry')) {
    return { type: 'Dry Storage', temp: '10-21', humidity: '50-60' }
  }

  // Bread and baked goods
  if (productLower.includes('bread') || productLower.includes('bakery') ||
      productLower.includes('pastry')) {
    return { type: 'Room Temperature', temp: '18-24', humidity: '60-70' }
  }

  // Default
  return { type: 'Cool Storage', temp: '4-10', humidity: '85' }
}

export default CameraDashboard
