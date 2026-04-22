# User Training Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Operations](#basic-operations)
3. [Advanced Features](#advanced-features)
4. [Troubleshooting](#troubleshooting)
5. [Best Practices](#best-practices)

## Getting Started

### First Time Setup

1. **Access the Dashboard**
   - Open your browser
   - Navigate to http://your-domain.com
   - The dashboard loads with an overview of recent activity

2. **Understanding the Interface**
   - **Sidebar**: Main navigation (Dashboard, New Extraction, History, Settings)
   - **Header**: User menu, notifications, theme toggle
   - **Main Content**: Current page content

3. **Your First Extraction**
   ```
   1. Click "New Extraction" in sidebar
   2. Drag & drop or click to upload an image
   3. Wait for processing (typically 2-5 seconds)
   4. Review results
   5. Download or save
   ```

### Navigation Guide

| Menu Item | Purpose | When to Use |
|-----------|---------|-------------|
| Dashboard | View metrics & trends | Daily overview |
| New Extraction | Process images | When you have images to process |
| History | Find past extractions | Looking for previous results |
| Settings | Configure preferences | Setting up defaults |

## Basic Operations

### Uploading Images

**Supported Formats:**
- JPEG/JPG
- PNG
- WEBP

**File Size:** Maximum 10MB

**Methods:**
1. Drag and drop onto the upload area
2. Click to open file browser
3. Select one or multiple files

### Processing Images

1. **Single Image**
   - Upload image
   - Add source farm/destination (optional)
   - Click "Process Image"
   - Wait for results

2. **Batch Processing**
   - Upload multiple images (up to 50)
   - Processing runs automatically
   - Results show summary + individual details

### Reviewing Results

**Extraction Results Include:**
- Product name and ID
- Quantity and units
- Expiry date (if detected)
- Condition assessment
- Confidence scores

**Actions Available:**
- Download as JSON
- View details
- Provide feedback
- Add to history

### Using History

**Search:**
- By extraction ID
- By source farm name
- By date range

**Filter:**
- Success / Partial / Error status
- Date ranges
- Product types

**Export:**
- CSV for spreadsheet analysis
- JSON for data integration

## Advanced Features

### Custom Settings

**Default Values**
Set default source farm and destination for faster processing:
1. Go to Settings
2. Enter default values
3. Click "Save Changes"

**Detection Parameters**
Adjust sensitivity:
- **High Confidence**: Fewer false positives, may miss some items
- **Low Confidence**: More detections, may include false positives

**GPU Acceleration**
Enable if available:
- Faster processing (2-5x speedup)
- Requires NVIDIA GPU
- Settings > Enable GPU

### Using Feedback System

After each extraction:
1. Click "Provide Feedback"
2. Rate accuracy (1-5 stars)
3. Select any issues found
4. Add comments if helpful
5. Submit

**Why Feedback Matters:**
- Improves model accuracy
- Helps identify edge cases
- Guides future improvements

### API Access (Advanced Users)

**Getting an API Key:**
```
Contact administrator to generate API key
```

**Example Request:**
```bash
curl -X POST https://api.your-domain.com/api/v1/extract \
  -H "X-API-Key: your-api-key" \
  -F "file=@image.jpg" \
  -F "source_farm=Farm-A"
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Upload fails | Check file size (<10MB) and format |
| Processing slow | Check system resources, enable GPU |
| Missing products | Try different image angle/lighting |
| OCR errors | Improve image quality, check language |
| No results | Check API connection, try health endpoint |

### Error Messages

**"Unsupported file type"**
- Only JPEG, PNG, WEBP are supported
- Convert your image and retry

**"Image too large"**
- Resize image to under 10MB
- Reduce resolution if needed

**"Processing failed"**
- Check server status
- Try again in a moment
- Contact support if persistent

### Getting Help

1. Check this guide
2. Review API docs at /docs
3. Contact support team

## Best Practices

### Image Quality

**Do:**
- Use good lighting
- Capture entire shipment
- Include labels clearly
- Use consistent angles

**Don't:**
- Use blurry images
- Cut off product edges
- Rely on very zoomed-in shots
- Use heavily compressed images

### Data Management

**Regular Maintenance:**
- Export history weekly
- Archive old extractions
- Review accuracy metrics
- Update default settings

**Data Security:**
- Don't share API keys
- Use strong passwords
- Enable 2FA if available
- Log out on shared computers

### Workflow Optimization

**Efficient Processing:**
- Batch similar images together
- Set up default values
- Use keyboard shortcuts
- Schedule large batches for off-peak

**Team Collaboration:**
- Share extraction templates
- Document your process
- Review team metrics
- Standardize naming conventions

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Quick search |
| `Ctrl/Cmd + E` | New extraction |
| `Ctrl/Cmd + H` | History |
| `Ctrl/Cmd + ,` | Settings |
| `Escape` | Close modal |

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│ QUICK START                                 │
├─────────────────────────────────────────────┤
│ 1. New Extraction → Upload image           │
│ 2. Review results → Download/Save          │
│ 3. History → Find past extractions         │
│ 4. Settings → Configure preferences        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ SUPPORT CONTACTS                            │
├─────────────────────────────────────────────┤
│ Technical Issues: support@company.com      │
│ API Access: api@company.com                │
│ Emergency: on-call@company.com             │
└─────────────────────────────────────────────┘
```

## Appendix: Glossary

**Extraction**: The process of analyzing an image to identify logistics data

**OCR**: Optical Character Recognition - reading text from images

**Confidence Score**: How certain the system is about a detection (0-100%)

**Source Farm**: Origin location of the shipment

**Destination**: Receiving location of the shipment

**Batch**: Processing multiple images in a single operation
