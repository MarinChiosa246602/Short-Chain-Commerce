import React, { useState, useCallback } from 'react'
import { Upload, Camera, X, Check, AlertCircle, Loader2, Download } from 'lucide-react'
import api from '../services/api'

function Extraction() {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [sourceFarm, setSourceFarm] = useState('')
  const [destination, setDestination] = useState('')
  const [processingSteps, setProcessingSteps] = useState([])

  const handleFileSelect = (file) => {
    if (!file) return

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if (!validTypes.includes(file.type)) {
      setError('Please select a valid image file (JPEG, PNG, or WEBP)')
      return
    }

    setSelectedFile(file)
    setError(null)
    setResult(null)

    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target.result)
    reader.readAsDataURL(file)
  }

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }, [])

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const clearSelection = () => {
    setSelectedFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
  }

  const processImage = async () => {
    if (!selectedFile) {
      setError('Please select an image first')
      return
    }

    setLoading(true)
    setError(null)
    setProcessingSteps([])

    const steps = [
      { name: 'Uploading image...', status: 'pending' },
      { name: 'Running object detection...', status: 'pending' },
      { name: 'Extracting text with OCR...', status: 'pending' },
      { name: 'Validating results...', status: 'pending' },
      { name: 'Finalizing extraction...', status: 'pending' },
    ]

    // Update steps as we progress
    for (let i = 0; i < steps.length; i++) {
      steps[i].status = 'processing'
      setProcessingSteps([...steps])

      // Simulate step delay
      await new Promise(resolve => setTimeout(resolve, 800))
      steps[i].status = 'complete'
      setProcessingSteps([...steps])
    }

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      if (sourceFarm) formData.append('source_farm', sourceFarm)
      if (destination) formData.append('destination', destination)

      const response = await api.extractData(formData)
      setResult(response)
    } catch (err) {
      setError(err.message || 'Failed to process image')
    } finally {
      setLoading(false)
    }
  }

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

  return (
    <div className="extraction">
      <div className="page-header">
        <h1>New Extraction</h1>
        <p className="subtitle">Upload an image to extract logistics data</p>
      </div>

      <div className="extraction-grid">
        {/* Upload Section */}
        <div className="upload-section">
          <div
            className={`dropzone ${dragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {selectedFile ? (
              <div className="file-preview">
                <img src={preview} alt="Preview" className="preview-image" />
                <div className="file-info">
                  <span className="file-name">{selectedFile.name}</span>
                  <span className="file-size">{(selectedFile.size / 1024).toFixed(1)} KB</span>
                </div>
                <button className="remove-file" onClick={clearSelection}>
                  <X size={20} />
                </button>
              </div>
            ) : (
              <div className="dropzone-content">
                <Upload size={48} className="upload-icon" />
                <h3>Drop your image here</h3>
                <p>or click to browse files</p>
                <p className="file-hint">Supports: JPEG, PNG, WEBP</p>
              </div>
            )}
            <input
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/webp"
              onChange={handleFileInput}
              className="file-input"
            />
          </div>

          {/* Metadata Inputs */}
          <div className="metadata-inputs">
            <div className="form-group">
              <label htmlFor="sourceFarm">Source Farm (Optional)</label>
              <input
                id="sourceFarm"
                type="text"
                value={sourceFarm}
                onChange={(e) => setSourceFarm(e.target.value)}
                placeholder="e.g., Farm-A"
              />
            </div>
            <div className="form-group">
              <label htmlFor="destination">Destination (Optional)</label>
              <input
                id="destination"
                type="text"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="e.g., Warehouse-B"
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {/* Process Button */}
          <button
            className="process-btn"
            onClick={processImage}
            disabled={!selectedFile || loading}
          >
            {loading ? (
              <>
                <Loader2 className="spin" size={20} />
                Processing...
              </>
            ) : (
              <>
                <Check size={20} />
                Process Image
              </>
            )}
          </button>
        </div>

        {/* Results Section */}
        <div className="results-section">
          {loading && (
            <div className="processing-steps">
              <h3>Processing</h3>
              {processingSteps.map((step, idx) => (
                <div key={idx} className={`step ${step.status}`}>
                  <div className="step-icon">
                    {step.status === 'complete' && <Check size={16} />}
                    {step.status === 'processing' && <Loader2 size={16} className="spin" />}
                    {step.status === 'pending' && <div className="step-dot" />}
                  </div>
                  <span>{step.name}</span>
                </div>
              ))}
            </div>
          )}

          {result && (
            <div className="result-display">
              <div className="result-header">
                <h3>Extraction Results</h3>
                <div className="result-status">
                  {result.status === 'success' && (
                    <span className="status-badge success">Success</span>
                  )}
                  {result.status === 'partial' && (
                    <span className="status-badge warning">Partial</span>
                  )}
                  <button className="download-btn" onClick={downloadResult}>
                    <Download size={16} />
                    Download JSON
                  </button>
                </div>
              </div>

              {result.data && (
                <div className="result-content">
                  <div className="result-meta">
                    <span className="meta-item">
                      <strong>Image ID:</strong> {result.data.image_id}
                    </span>
                    <span className="meta-item">
                      <strong>Time:</strong> {new Date(result.data.timestamp).toLocaleString()}
                    </span>
                    <span className="meta-item">
                      <strong>Duration:</strong> {result.processing_time_ms?.toFixed(0)}ms
                    </span>
                  </div>

                  {result.data.products && result.data.products.length > 0 && (
                    <div className="products-list">
                      <h4>Products Detected ({result.data.products.length})</h4>
                      {result.data.products.map((product, idx) => (
                        <div key={idx} className="product-card">
                          <div className="product-header">
                            <span className="product-name">{product.product_name}</span>
                            <span className="product-id">{product.product_id}</span>
                          </div>
                          <div className="product-details">
                            <span>Quantity: {product.quantity} {product.unit}</span>
                            {product.expiry_date && (
                              <span>Expires: {new Date(product.expiry_date).toLocaleDateString()}</span>
                            )}
                            {product.condition && (
                              <span>Condition: {product.condition}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {result.data.metadata && (
                    <div className="metadata-section">
                      <h4>Metadata</h4>
                      <div className="metadata-grid">
                        <span><strong>Source:</strong> {result.data.metadata.source_farm}</span>
                        <span><strong>Destination:</strong> {result.data.metadata.destination}</span>
                        {result.data.metadata.temperature && (
                          <span><strong>Temperature:</strong> {result.data.metadata.temperature}°C</span>
                        )}
                        {result.data.metadata.humidity && (
                          <span><strong>Humidity:</strong> {result.data.metadata.humidity}%</span>
                        )}
                      </div>
                    </div>
                  )}

                  {(result.data.missing_fields?.length > 0 || result.data.low_confidence_fields?.length > 0) && (
                    <div className="warnings-section">
                      {result.data.missing_fields?.length > 0 && (
                        <div className="warning-item">
                          <AlertCircle size={16} />
                          <span>Missing fields: {result.data.missing_fields.join(', ')}</span>
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
              <h3>No Results Yet</h3>
              <p>Upload an image and click "Process Image" to see extraction results</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Extraction
