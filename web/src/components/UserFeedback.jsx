import React, { useState } from 'react'
import { MessageSquare, ThumbsUp, ThumbsDown, X } from 'lucide-react'

function UserFeedback({ extractionId }) {
  const [open, setOpen] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [feedback, setFeedback] = useState({
    rating: 0,
    accuracy: 0,
    comment: '',
    issues: [],
  })

  const issueTypes = [
    { id: 'missing_items', label: 'Missing items' },
    { id: 'wrong_quantity', label: 'Incorrect quantity' },
    { id: 'wrong_product', label: 'Wrong product detected' },
    { id: 'ocr_error', label: 'Text recognition error' },
    { id: 'other', label: 'Other issue' },
  ]

  const handleSubmit = async () => {
    // Send feedback to analytics/logging system
    console.log('Feedback submitted:', { extractionId, feedback })

    // Store locally for testing purposes
    const existing = JSON.parse(localStorage.getItem('userFeedback') || '[]')
    existing.push({
      extractionId,
      feedback,
      timestamp: new Date().toISOString(),
    })
    localStorage.setItem('userFeedback', JSON.stringify(existing))

    setSubmitted(true)
    setTimeout(() => {
      setOpen(false)
      setSubmitted(false)
      setFeedback({ rating: 0, accuracy: 0, comment: '', issues: [] })
    }, 2000)
  }

  const toggleIssue = (issueId) => {
    setFeedback((prev) => ({
      ...prev,
      issues: prev.issues.includes(issueId)
        ? prev.issues.filter((i) => i !== issueId)
        : [...prev.issues, issueId],
    }))
  }

  if (!open) {
    return (
      <button className="feedback-btn" onClick={() => setOpen(true)}>
        <MessageSquare size={18} />
        Provide Feedback
      </button>
    )
  }

  return (
    <div className="feedback-overlay" onClick={() => setOpen(false)}>
      <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
        <div className="feedback-header">
          <h3>Feedback on Extraction</h3>
          <button className="close-btn" onClick={() => setOpen(false)}>
            <X size={20} />
          </button>
        </div>

        {submitted ? (
          <div className="feedback-success">
            <ThumbsUp size={48} />
            <h4>Thank you for your feedback!</h4>
            <p>Your input helps improve our extraction accuracy.</p>
          </div>
        ) : (
          <>
            <div className="feedback-content">
              <div className="feedback-section">
                <label>Overall Rating</label>
                <div className="rating-buttons">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      className={`rating-btn ${feedback.rating >= star ? 'active' : ''}`}
                      onClick={() => setFeedback({ ...feedback, rating: star })}
                    >
                      {star === 1 && <ThumbsDown size={24} />}
                      {star >= 2 && star <= 4 && <MessageSquare size={24} />}
                      {star === 5 && <ThumbsUp size={24} />}
                    </button>
                  ))}
                </div>
                <small>1 = Poor, 5 = Excellent</small>
              </div>

              <div className="feedback-section">
                <label>Extraction Accuracy</label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={feedback.accuracy}
                  onChange={(e) =>
                    setFeedback({ ...feedback, accuracy: parseInt(e.target.value) })
                  }
                />
                <div className="accuracy-value">{feedback.accuracy}%</div>
              </div>

              <div className="feedback-section">
                <label>Issues Detected (Optional)</label>
                <div className="issue-checkboxes">
                  {issueTypes.map((issue) => (
                    <label key={issue.id} className="issue-checkbox">
                      <input
                        type="checkbox"
                        checked={feedback.issues.includes(issue.id)}
                        onChange={() => toggleIssue(issue.id)}
                      />
                      <span>{issue.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="feedback-section">
                <label>Additional Comments (Optional)</label>
                <textarea
                  value={feedback.comment}
                  onChange={(e) =>
                    setFeedback({ ...feedback, comment: e.target.value })
                  }
                  placeholder="Share any additional details about the extraction..."
                  rows={3}
                />
              </div>
            </div>

            <div className="feedback-footer">
              <button className="btn-secondary" onClick={() => setOpen(false)}>
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={handleSubmit}
                disabled={feedback.rating === 0}
              >
                Submit Feedback
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default UserFeedback
