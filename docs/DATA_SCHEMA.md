# Data Schema Documentation

## Overview

This document defines the JSON output structure for extracted logistics data from visual inputs.

## Main Output Schema

```json
{
  "image_id": "uuid",
  "timestamp": "ISO8601",
  "products": [
    {
      "product_id": "SKU-123",
      "product_name": "Tomato",
      "quantity": 24,
      "unit": "crate",
      "expiry_date": "2026-04-20",
      "storage_location": "Fridge A",
      "condition": "excellent"
    }
  ],
  "metadata": {
    "source_farm": "Farm-001",
    "destination": "Market-X",
    "temperature": 5,
    "humidity": 85
  }
}
```

---

## Field Definitions

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_id` | string (UUID) | Yes | Unique identifier for the source image |
| `timestamp` | string (ISO8601) | Yes | Timestamp of image capture/processing |
| `products` | array | Yes | List of detected products |
| `metadata` | object | Yes | Contextual information about the shipment |

---

### Product Object Fields

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `product_id` | string | Yes | SKU or unique product identifier | Format: alphanumeric, max 50 chars |
| `product_name` | string | Yes | Human-readable product name | Min 1 char, max 200 chars |
| `quantity` | number | Yes | Number of items/units | Positive integer (1-99999) |
| `unit` | string | Yes | Unit of measurement | Enum: crate, box, kg, lb, piece, carton, pallet |
| `expiry_date` | string | No | Expiration date | Format: YYYY-MM-DD |
| `storage_location` | string | No | Physical storage location | Max 100 chars |
| `condition` | string | No | Quality assessment | Enum: excellent, good, fair, poor, damaged |

---

### Metadata Object Fields

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `source_farm` | string | Yes | Origin farm identifier | Format: alphanumeric, max 50 chars |
| `destination` | string | Yes | Destination identifier | Max 100 chars |
| `temperature` | number | No | Storage temperature in Celsius | Range: -40 to 50 |
| `humidity` | number | No | Humidity percentage | Range: 0-100 |

---

## Validation Rules

### Date Validation
- Dates must be in ISO 8601 format: `YYYY-MM-DD`
- Expiry dates must be in the future
- Timestamps must include timezone: `2026-04-15T14:30:00Z`

### Quantity Bounds
- Quantity must be a positive integer
- Maximum quantity: 99,999
- Default unit: piece (if not specified)

### Enum Values

**Units:**
- `crate` - Standard crate
- `box` - Cardboard box
- `kg` - Kilograms
- `lb` - Pounds
- `piece` - Individual pieces
- `carton` - Carton packaging
- `pallet` - Full pallet

**Conditions:**
- `excellent` - No visible damage, optimal freshness
- `good` - Minor imperfections, fresh
- `fair` - Noticeable wear, still usable
- `poor` - Significant damage, nearing expiry
- `damaged` - Visible damage, may require rejection

---

## Error Handling

### Validation Errors

```json
{
  "errors": [
    {
      "field": "expiry_date",
      "code": "INVALID_FORMAT",
      "message": "Date must be in YYYY-MM-DD format"
    },
    {
      "field": "quantity",
      "code": "OUT_OF_BOUNDS",
      "message": "Quantity must be between 1 and 99999"
    }
  ]
}
```

### Missing Fields

When required fields are missing:
1. Set field to `null`
2. Add to `missing_fields` array in response
3. Flag for manual review

---

## API Endpoint Specifications

### POST /api/v1/extract

**Request:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "image_data": "base64_encoded_data",
  "source_farm": "Farm-001",
  "destination": "Market-X"
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "data": { /* extracted data */ },
  "processing_time_ms": 1250
}
```

**Response (Partial Success - 206):**
```json
{
  "status": "partial",
  "data": { /* extracted data */ },
  "missing_fields": ["expiry_date", "condition"],
  "low_confidence_fields": ["quantity"],
  "processing_time_ms": 1250
}
```

**Response (Error - 400/422):**
```json
{
  "status": "error",
  "errors": [ /* validation errors */ ],
  "processing_time_ms": 150
}
```

---

## Data Versioning

- Schema Version: `1.0.0`
- Last Updated: 2026-04-15
- Backward Compatible: Yes
