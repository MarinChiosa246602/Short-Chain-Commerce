"""
Data models for the Short Chain Commerce logistics data extraction system.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum


class UnitType(str, Enum):
    """Supported unit types for product quantities."""
    CRATE = "crate"
    BOX = "box"
    KG = "kg"
    LB = "lb"
    PIECE = "piece"
    CARTON = "carton"
    PALLET = "pallet"


class ConditionType(str, Enum):
    """Product condition assessment types."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED = "damaged"


class Product(BaseModel):
    """Represents a detected product in the image."""

    product_id: str = Field(..., description="SKU or unique product identifier", max_length=50)
    product_name: str = Field(..., description="Human-readable product name", min_length=1, max_length=200)
    quantity: int = Field(..., description="Number of items/units", ge=1, le=99999)
    unit: UnitType = Field(..., description="Unit of measurement")
    expiry_date: Optional[datetime] = Field(None, description="Expiration date")
    storage_location: Optional[str] = Field(None, description="Physical storage location", max_length=100)
    condition: Optional[ConditionType] = Field(None, description="Quality assessment")

    @validator('product_id')
    def validate_product_id(cls, v):
        if not v or not v.strip():
            raise ValueError('product_id cannot be empty')
        return v.strip()

    @validator('expiry_date')
    def validate_expiry_date(cls, v):
        if v and v <= datetime.now():
            raise ValueError('expiry_date must be in the future')
        return v


class Metadata(BaseModel):
    """Contextual information about the shipment."""

    source_farm: str = Field(..., description="Origin farm identifier", max_length=50)
    destination: str = Field(..., description="Destination identifier", max_length=100)
    temperature: Optional[float] = Field(None, description="Storage temperature in Celsius", ge=-40, le=50)
    humidity: Optional[float] = Field(None, description="Humidity percentage", ge=0, le=100)

    @validator('source_farm')
    def validate_source_farm(cls, v):
        if not v or not v.strip():
            raise ValueError('source_farm cannot be empty')
        return v.strip()

    @validator('destination')
    def validate_destination(cls, v):
        if not v or not v.strip():
            raise ValueError('destination cannot be empty')
        return v.strip()


class ExtractionResponse(BaseModel):
    """Main response schema for data extraction."""

    image_id: UUID = Field(default_factory=uuid4, description="Unique identifier for the source image")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of processing")
    products: List[Product] = Field(..., description="List of detected products")
    metadata: Metadata = Field(..., description="Contextual information")

    # Optional fields for partial success
    missing_fields: List[str] = Field(default_factory=list, description="Fields that could not be extracted")
    low_confidence_fields: List[str] = Field(default_factory=list, description="Fields with low extraction confidence")


class ValidationErrorDetail(BaseModel):
    """Details about a validation error."""

    field: str
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""

    status: str = "error"
    errors: List[ValidationErrorDetail]
    processing_time_ms: float


class PartialSuccessResponse(BaseModel):
    """Partial success response schema."""

    status: str = "partial"
    data: ExtractionResponse
    missing_fields: List[str]
    low_confidence_fields: List[str]
    processing_time_ms: float


class SuccessResponse(BaseModel):
    """Success response schema."""

    status: str = "success"
    data: ExtractionResponse
    processing_time_ms: float


class ImageUploadRequest(BaseModel):
    """Request schema for image upload and extraction."""

    image_url: Optional[HttpUrl] = Field(None, description="URL of the image to process")
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    source_farm: Optional[str] = Field(None, description="Override source farm identifier")
    destination: Optional[str] = Field(None, description="Override destination identifier")

    @validator('image_url', 'image_data', pre=True)
    def check_at_least_one(cls, v, values):
        if not v and not values.get('image_url'):
            if not values.get('image_data'):
                raise ValueError('Either image_url or image_data must be provided')
        return v
