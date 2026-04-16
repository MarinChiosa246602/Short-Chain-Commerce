"""
FastAPI application for the Short Chain Commerce logistics data extraction API.
"""

import time
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from models.schemas import (
    SuccessResponse,
    PartialSuccessResponse,
    ErrorResponse,
    ValidationErrorDetail,
    ImageUploadRequest,
    ExtractionResponse,
)
from models import UnitType, ConditionType, Product, Metadata

app = FastAPI(
    title="Short Chain Commerce - Logistics Data Extraction API",
    description="Automatic extraction of logistics data from visual inputs for short food supply chain management",
    version="1.0.0",
)


@app.get("/")
async def root():
    """API root endpoint - health check."""
    return {
        "service": "Short Chain Commerce API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


@app.post("/api/v1/extract")
async def extract_data(
    source_farm: Optional[str] = Form(None, description="Origin farm identifier"),
    destination: Optional[str] = Form(None, description="Destination identifier"),
):
    """
    Extract logistics data from an uploaded image.

    - **source_farm**: (Optional) Override source farm identifier
    - **destination**: (Optional) Override destination identifier
    - **file**: Image file to process (multipart/form-data)

    Returns extracted product data in structured JSON format.
    """
    start_time = time.time()

    try:
        # TODO: Implement image processing pipeline
        # 1. Receive and validate image
        # 2. Run object detection (YOLOv8)
        # 3. Run OCR (PaddleOCR)
        # 4. Parse and validate extracted data
        # 5. Return structured response

        # Placeholder response for schema validation
        sample_data = ExtractionResponse(
            products=[
                Product(
                    product_id="TOM-001",
                    product_name="Tomato",
                    quantity=24,
                    unit=UnitType.CRATE,
                    condition=ConditionType.EXCELLENT,
                )
            ],
            metadata=Metadata(
                source_farm=source_farm or "Farm-001",
                destination=destination or "Market-X",
                temperature=5.0,
                humidity=85.0,
            ),
        )

        processing_time = (time.time() - start_time) * 1000

        return SuccessResponse(
            data=sample_data,
            processing_time_ms=processing_time,
        )

    except ValidationError as e:
        errors = [
            ValidationErrorDetail(
                field=str(err["loc"][0]),
                code=err["type"],
                message=err["msg"],
            )
            for err in e.errors()
        ]
        return ErrorResponse(errors=errors, processing_time_ms=(time.time() - start_time) * 1000)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/extract/file")
async def extract_from_file(file: UploadFile = File(...)):
    """
    Extract data from a file upload.

    Accepts image files (JPEG, PNG, WEBP) and returns structured logistics data.
    """
    start_time = time.time()

    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )

    try:
        # TODO: Process the file
        # - Read file content
        # - Run through CV pipeline
        # - Return extraction results

        processing_time = (time.time() - start_time) * 1000

        return {
            "status": "success",
            "message": f"File {file.filename} received. Processing pipeline to be implemented.",
            "processing_time_ms": processing_time,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/schemas")
async def get_schemas():
    """
    Return the API schema documentation.

    Use this to understand the expected input/output formats.
    """
    return {
        "extraction_request": {
            "source_farm": "string (optional)",
            "destination": "string (optional)",
            "file": "image file (multipart/form-data)"
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
                        "condition": "excellent | good | fair | poor | damaged (optional)"
                    }
                ],
                "metadata": {
                    "source_farm": "string",
                    "destination": "string",
                    "temperature": "float (optional)",
                    "humidity": "float (optional)"
                }
            },
            "processing_time_ms": "float"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
