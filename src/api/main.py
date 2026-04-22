"""
FastAPI application for the Short Chain Commerce logistics data extraction API.

Full implementation with CV pipeline, OCR, and monitoring integration.
"""

import logging
import os
import time
from datetime import datetime
from typing import List, Optional

import cv2
import numpy as np
from pipeline.end_to_end import EndToEndPipeline, BatchProcessor
from database.db_manager import get_database_manager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, Response

from monitoring.logging_utils import setup_logging

# Performance monitoring
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    from prometheus_client import CollectorRegistry

    PROMETHEUS_AVAILABLE = True
    registry = CollectorRegistry()
    api_requests = Counter("api_requests_total", "Total API requests", ["endpoint", "status"], registry=registry)
    api_duration = Histogram("api_request_duration_seconds", "API request duration", ["endpoint"], registry=registry)
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Initialize logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

# Configure logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Short Chain Commerce - Logistics Data Extraction API",
    description="Automatic extraction of logistics data from visual inputs for short food supply chain management",
    version="1.0.0",
)


# Middleware for performance monitoring
@app.middleware("http")
async def monitor_performance(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Record metrics
    if PROMETHEUS_AVAILABLE:
        api_requests.labels(endpoint=request.url.path, status=str(response.status_code)).inc()
        api_duration.labels(endpoint=request.url.path).observe(duration)

    return response


# Global pipeline instance (initialized on first request)
_extraction_pipeline = None
_batch_processor = None


def get_pipeline():
    """Get or create pipeline instance."""
    global _extraction_pipeline
    if _extraction_pipeline is None:
        _extraction_pipeline = EndToEndPipeline(
            {
                "confidence_threshold": 0.7,
                "detection_confidence": 0.5,
            }
        )
    return _extraction_pipeline


def get_batch_processor():
    """Get or create batch processor instance."""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor(
            {
                "confidence_threshold": 0.7,
            }
        )
    return _batch_processor


# Monitoring metrics
metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_processing_time_ms": 0,
    "requests_by_status": {},
}


# Prometheus metrics endpoint
@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    if PROMETHEUS_AVAILABLE:
        return Response(content=generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
    return Response(content="Prometheus not available", status_code=503)


def update_metrics(status: str, processing_time_ms: float):
    """Update API metrics."""
    metrics["total_requests"] += 1
    metrics["total_processing_time_ms"] += processing_time_ms

    if status == "success":
        metrics["successful_requests"] += 1
    elif status == "partial":
        metrics["successful_requests"] += 1  # Partial is still success
    else:
        metrics["failed_requests"] += 1

    status_key = status
    metrics["requests_by_status"][status_key] = metrics["requests_by_status"].get(status_key, 0) + 1


@app.get("/")
async def root():
    """API root endpoint - health check."""
    return {"service": "Short Chain Commerce API", "status": "running", "version": "1.0.0", "documentation": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "pipeline_initialized": _extraction_pipeline is not None,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/metrics")
def get_metrics():
    """Get API performance metrics."""
    avg_time = metrics["total_processing_time_ms"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0
    return {
        "total_requests": metrics["total_requests"],
        "successful_requests": metrics["successful_requests"],
        "failed_requests": metrics["failed_requests"],
        "success_rate": (metrics["successful_requests"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0),
        "avg_processing_time_ms": avg_time,
        "requests_by_status": metrics["requests_by_status"],
    }


@app.post("/api/v1/extract")
async def extract_data(
    file: UploadFile = File(..., description="Image file to process"),
    source_farm: Optional[str] = Form(None, description="Origin farm identifier"),
    destination: Optional[str] = Form(None, description="Destination identifier"),
):
    """
    Extract logistics data from an uploaded image.

    - **file**: Image file (JPEG, PNG, WEBP)
    - **source_farm**: (Optional) Override source farm identifier
    - **destination**: (Optional) Override destination identifier

    Returns extracted product data in structured JSON format.
    """
    start_time = time.time()

    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}")

    try:
        # Read image data
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Run pipeline
        pipeline = get_pipeline()
        result = pipeline.process(
            image_source=image,
            source_farm=source_farm,
            destination=destination,
        )

        processing_time = (time.time() - start_time) * 1000
        update_metrics(result.get("status", "error"), processing_time)

        if result.get("status") == "error":
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "error": result.get("error", "Processing failed"),
                    "processing_time_ms": processing_time,
                },
            )

        # Build response
        extraction = result.get("extraction")
        if extraction:
            if result.get("is_valid"):
                return JSONResponse(
                    content={
                        "status": "success",
                        "data": {
                            "image_id": str(extraction.image_id),
                            "timestamp": extraction.timestamp.isoformat(),
                            "products": [
                                {
                                    "product_id": p.product_id,
                                    "product_name": p.product_name,
                                    "quantity": p.quantity,
                                    "unit": p.unit.value,
                                    "expiry_date": p.expiry_date.isoformat() if p.expiry_date else None,
                                    "storage_location": p.storage_location,
                                    "condition": p.condition.value if p.condition else None,
                                }
                                for p in extraction.products
                            ],
                            "metadata": {
                                "source_farm": extraction.metadata.source_farm,
                                "destination": extraction.metadata.destination,
                                "temperature": extraction.metadata.temperature,
                                "humidity": extraction.metadata.humidity,
                            },
                            "missing_fields": extraction.missing_fields,
                            "low_confidence_fields": extraction.low_confidence_fields,
                        },
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return JSONResponse(
                    content={
                        "status": "partial",
                        "data": {
                            "image_id": str(extraction.image_id),
                            "timestamp": extraction.timestamp.isoformat(),
                            "products": [
                                {
                                    "product_id": p.product_id,
                                    "product_name": p.product_name,
                                    "quantity": p.quantity,
                                    "unit": p.unit.value,
                                    "expiry_date": p.expiry_date.isoformat() if p.expiry_date else None,
                                    "storage_location": p.storage_location,
                                    "condition": p.condition.value if p.condition else None,
                                }
                                for p in extraction.products
                            ],
                            "metadata": {
                                "source_farm": extraction.metadata.source_farm,
                                "destination": extraction.metadata.destination,
                                "temperature": extraction.metadata.temperature,
                                "humidity": extraction.metadata.humidity,
                            },
                            "missing_fields": extraction.missing_fields,
                            "low_confidence_fields": extraction.low_confidence_fields,
                        },
                        "errors": result.get("errors", []),
                        "processing_time_ms": processing_time,
                    }
                )

        return JSONResponse(status_code=500, content={"status": "error", "error": "Unexpected response format"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        processing_time = (time.time() - start_time) * 1000
        update_metrics("error", processing_time)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/extract/batch")
async def extract_batch(
    files: List[UploadFile] = File(..., description="Image files to process"),
    source_farm: Optional[str] = Form(None, description="Source farm identifier"),
    destination: Optional[str] = Form(None, description="Destination identifier"),
):
    """
    Extract data from multiple images in a single request.

    - **files**: List of image files
    - **source_farm**: Source farm identifier
    - **destination**: Destination identifier

    Returns aggregated results for all images.
    """
    start_time = time.time()

    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 files per batch request")

    try:
        # Process images and return batch results
        processor = get_batch_processor()

        # Convert files to numpy arrays
        images = []
        for file in files:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is not None:
                images.append(image)

        # Process batch
        batch_result = processor.process_batch(
            image_sources=images,
            source_farm=source_farm,
            destination=destination,
        )

        processing_time = (time.time() - start_time) * 1000

        return JSONResponse(
            content={
                "status": "success",
                "batch_summary": {
                    "total_images": batch_result.get("total_images", 0),
                    "successful": batch_result.get("successful", 0),
                    "failed": batch_result.get("failed", 0),
                    "success_rate": batch_result.get("success_rate", 0),
                    "processing_time_ms": batch_result.get("processing_time_ms", 0),
                },
                "aggregation": batch_result.get("aggregation", {}),
                "results": batch_result.get("results", []),
                "anomalies": batch_result.get("anomalies", []),
                "processing_time_ms": processing_time,
            }
        )

    except Exception as e:
        logger.error(f"Batch extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health/detailed")
async def detailed_health():
    """Detailed health check with component status."""
    pipeline = get_pipeline()

    return {
        "status": "healthy",
        "components": {
            "cv_pipeline": "initialized" if hasattr(pipeline, "cv_pipeline") and pipeline.cv_pipeline else "pending",
            "ocr_pipeline": "initialized" if hasattr(pipeline, "ocr_pipeline") and pipeline.ocr_pipeline else "pending",
            "extraction_processor": (
                "initialized" if hasattr(pipeline, "extraction_processor") and pipeline.extraction_processor else "pending"
            ),
        },
        "metrics": get_metrics(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/schemas")
async def get_schemas():
    """Return the API schema documentation."""
    return {
        "extraction_request": {
            "source_farm": "string (optional)",
            "destination": "string (optional)",
            "file": "image file (multipart/form-data)",
        },
        "extraction_response": {
            "status": "success | partial | error",
            "data": {
                "image_id": "UUID",
                "timestamp": "ISO8601 datetime",
                "products": [
                    {
                        "product_id": "string",
                        "product_name": "string",
                        "quantity": "integer",
                        "unit": "crate | box | kg | lb | piece | carton | pallet",
                        "expiry_date": "YYYY-MM-DD (optional)",
                        "storage_location": "string (optional)",
                        "condition": "excellent | good | fair | poor | damaged (optional)",
                    }
                ],
                "metadata": {
                    "source_farm": "string",
                    "destination": "string",
                    "temperature": "float (optional)",
                    "humidity": "float (optional)",
                },
            },
            "processing_time_ms": "float",
        },
        "batch_response": {
            "status": "success",
            "batch_summary": {
                "total_images": "integer",
                "successful": "integer",
                "failed": "integer",
                "success_rate": "float (0-1)",
            },
            "aggregation": {
                "total_products_detected": "integer",
                "total_quantity": "integer",
                "product_types": "object",
                "earliest_expiry": "ISO8601 (optional)",
                "latest_expiry": "ISO8601 (optional)",
            },
            "results": "array of individual extraction results",
            "anomalies": "array of detected anomalies",
        },
    }


# Database integration endpoint (optional - requires database configuration)
@app.get("/api/v1/extractions")
async def get_extractions(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
):
    """
    Get extraction history from database.
    Returns mock data if database is not configured.
    """
    try:
        db = get_database_manager()
        db.initialize()

        # Query extractions from database
        extractions = db.query_extractions(
            status=status if status and status != "all" else None,
            limit=limit,
            offset=offset,
        )

        # Convert to response format
        results = []
        for ext in extractions:
            results.append(
                {
                    "extraction_id": ext.get("id"),
                    "status": ext.get("status"),
                    "timestamp": ext.get("timestamp"),
                    "processing_time_ms": ext.get("processing_time_ms"),
                    "extraction": {
                        "products": ext.get("products", []),
                        "metadata": {
                            "source_farm": ext.get("source_farm"),
                            "destination": ext.get("destination"),
                        },
                    },
                }
            )

        return {
            "results": results,
            "total": len(results),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        # Return empty results if database not available
        logger.warning(f"Database query failed: {e}")
        return {
            "results": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }


@app.get("/api/v1/extractions/{extraction_id}")
async def get_extraction(extraction_id: str):
    """Get a specific extraction by ID."""
    try:
        db = get_database_manager()
        db.initialize()

        extraction = db.get_extraction(extraction_id)

        if extraction:
            return {
                "extraction_id": extraction.get("id"),
                "status": extraction.get("status"),
                "timestamp": extraction.get("timestamp"),
                "processing_time_ms": extraction.get("processing_time_ms"),
                "extraction": {
                    "products": extraction.get("products", []),
                    "metadata": {
                        "source_farm": extraction.get("source_farm"),
                        "destination": extraction.get("destination"),
                    },
                },
            }
        else:
            raise HTTPException(status_code=404, detail="Extraction not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/summary")
async def get_analytics_summary(
    days: int = 7,
):
    """
    Get analytics summary for the dashboard.
    Returns aggregated statistics for the specified number of days.
    """
    try:
        from datetime import datetime, timedelta

        db = get_database_manager()
        db.initialize()

        start_date = datetime.utcnow() - timedelta(days=days)
        stats = db.get_statistics(start_date=start_date)

        return {
            "period_days": days,
            "total_extractions": stats.get("total", 0),
            "successful": stats.get("successful", 0),
            "partial": stats.get("partial", 0),
            "failed": stats.get("failed", 0),
            "avg_processing_time_ms": stats.get("avg_processing_time_ms", 0),
            "period_start": stats.get("first_extraction"),
            "period_end": stats.get("last_extraction"),
        }

    except Exception as e:
        logger.warning(f"Analytics query failed: {e}")
        # Return default values
        return {
            "period_days": days,
            "total_extractions": 0,
            "successful": 0,
            "partial": 0,
            "failed": 0,
            "avg_processing_time_ms": 0,
            "period_start": None,
            "period_end": None,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
