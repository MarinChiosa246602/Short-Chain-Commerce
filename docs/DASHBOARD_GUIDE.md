# Dashboard User Guide

## Overview

The Short Chain Commerce Dashboard provides a user-friendly interface for managing logistics data extraction operations.

## Getting Started

### Starting the Application

1. **Start the Backend API:**
   ```bash
   docker-compose up -d
   ```

2. **Start the Frontend:**
   ```bash
   cd web
   npm install
   npm run dev
   ```

3. **Access the Dashboard:**
   Open http://localhost:3000 in your browser

## Features

### Dashboard

The main dashboard provides:
- **Total Extractions**: Count of all processed images
- **Success Rate**: Percentage of successful extractions
- **Average Processing Time**: Mean time to process an image
- **Pending Alerts**: Number of extractions requiring attention
- **Extraction Trends**: Visual chart of activity over time
- **Recent Extractions**: Table of the latest processed images

### New Extraction

Upload and process images:
1. Click "New Extraction" in the sidebar
2. Drag and drop an image or click to browse
3. (Optional) Enter source farm and destination
4. Click "Process Image"
5. View results including detected products and metadata

**Supported Formats:**
- JPEG/JPG
- PNG
- WEBP

**Maximum File Size:** 10MB

### History

Browse past extractions:
- Search by extraction ID or source farm
- Filter by status (success/partial/error)
- Export to CSV
- View full extraction details

### Settings

Configure extraction preferences:
- **Default Source Farm**: Pre-fill source farm for new extractions
- **Default Destination**: Pre-fill destination for new extractions
- **Confidence Threshold**: Detection accuracy (0-1)
- **OCR Language**: Text recognition language
- **GPU Acceleration**: Use NVIDIA GPU if available

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl/Cmd + K` | Quick search |
| `Ctrl/Cmd + E` | New extraction |
| `Ctrl/Cmd + H` | View history |
| `Ctrl/Cmd + ,` | Open settings |

## Troubleshooting

### "Failed to process image"
- Check that the backend API is running
- Verify the image format is supported
- Try a smaller image file

### "Connection refused"
- Ensure the API is accessible at http://localhost:8000
- Check docker-compose status

### Dashboard not loading
- Clear browser cache
- Check browser console for errors
- Verify frontend is running on port 3000

## API Endpoints

The dashboard communicates with these API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/extract` | POST | Extract data from image |
| `/api/v1/extract/batch` | POST | Batch extract from multiple images |
| `/api/v1/metrics` | GET | Get performance metrics |
| `/health` | GET | Health check |
| `/api/v1/health/detailed` | GET | Detailed component status |

## Support

For issues or questions:
- Check the [README](../README.md)
- Review API docs at http://localhost:8000/docs
