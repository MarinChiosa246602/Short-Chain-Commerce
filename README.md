# Short Chain Commerce - Automatic Logistics Data Extraction

**Automatic extraction of logistics data from visual inputs for efficient short food supply chain management.**

---

## Project Overview

This project automatically extracts logistics data (product types, quantities, expiry dates, condition assessments) from images of food crates, packaged products, and storage environments. The goal is to eliminate manual data entry for farmers, coordinators, and consumers in short food supply chains.

**Target Users:**
- **Farmers** - Upload shipment photos, get structured inventory data
- **Coordinators** - Track multi-farm logistics, monitor freshness
- **Consumers** - Verify product sourcing and quality

---

## Current Status: Phase 1 Complete

**Date:** April 19, 2026

### What's Implemented

| Component | Status | Description |
|-----------|--------|-------------|
| **Data Schema** | Complete | Pydantic models with full validation rules |
| **CV Pipeline** | Complete | YOLOv8-based object detection & condition assessment |
| **OCR Pipeline** | Complete | PaddleOCR integration for text extraction |
| **Parser & Validator** | Complete | Converts CV+OCR outputs to structured JSON |
| **API Layer** | Complete | FastAPI with REST endpoints |
| **Testing** | 155+ tests | Comprehensive unit & integration tests |
| **CI/CD** | Complete | GitHub Actions workflow configured |
| **Docker** | Complete | Containerization with GPU support |

### What's In Progress

| Component | Status | Next Steps |
|-----------|--------|------------|
| **Mock Dataset Generation** | Ready to run | Generate 500+ labeled images |
| **Model Training** | Pending | Train YOLOv8 on dataset |
| **Pipeline Testing** | Pending | End-to-end validation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│                    Pipeline Orchestration                        │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Image Input  │→ │   CV + OCR   │→ │  Parse & Validate│   │
│  └────────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                       Core Modules                               │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │   YOLOv8     │  │ PaddleOCR   │  │  Condition Assessor  │  │
│  │ Detection    │  │ Text Extract│  │  (damage/freshness)  │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Data Layer                                  │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │   Pydantic   │  │  PostgreSQL │  │    Error Logging     │  │
│  │   Validation │  │   (JSONB)   │  │    (monitoring)      │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Schema

### Output Format

```json
{
  "image_id": "uuid",
  "timestamp": "2026-04-19T14:30:00Z",
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
    "temperature": 5.0,
    "humidity": 85.0
  }
}
```

### Validation Rules

| Field | Rules |
|-------|-------|
| **Quantity** | 1 - 99,999 |
| **Temperature** | -40 to 50°C |
| **Humidity** | 0 - 100% |
| **Expiry Date** | Must be future date, YYYY-MM-DD format |
| **Units** | crate, box, kg, lb, piece, carton, pallet |
| **Conditions** | excellent, good, fair, poor, damaged |

---

## API Endpoints

### Process Single Image
```http
POST /api/v1/extract
Content-Type: multipart/form-data

file: <image_file>
source_farm: "Farm-001"
destination: "Market-X"
```

### Batch Processing
```http
POST /api/v1/extract/batch
Content-Type: multipart/form-data

files: <image1> <image2> ... <imageN>
source_farm: "Farm-001"
```

### Health Check
```http
GET /health
GET /api/v1/metrics
```

---

## Project Structure

```
Short-Chain-Commerce/
├── .github/workflows/
│   └── ci.yml                      # CI/CD pipeline
├── data/
│   ├── raw/                        # Raw images (to be generated)
│   ├── processed/                  # Processed data
│   └── yolo_dataset/              # YOLO training dataset
├── docs/
│   └── DATA_SCHEMA.md             # Schema documentation
├── reports/                        # Analysis reports (OCR, errors)
├── scripts/
│   ├── generate_mock_data.py      # Dataset generator
│   ├── train_model.py             # Model training script
│   └── test_ocr.py                # OCR testing utilities
├── src/
│   ├── api/
│   │   └── main.py                # FastAPI application
│   ├── models/
│   │   ├── schemas.py             # Pydantic data models
│   │   ├── cv_pipeline.py         # Computer Vision pipeline
│   │   ├── ocr_pipeline.py        # OCR pipeline
│   │   └── condition_assessment.py# Condition assessment module
│   ├── utils/
│   │   └── parser.py              # Data parsing & validation
│   └── pipeline/
│       └── end_to_end.py          # End-to-end pipeline
├── tests/
│   ├── test_schemas.py            # Schema validation tests
│   ├── test_parser.py             # Parser tests
│   ├── test_ocr_pipeline.py       # OCR tests
│   ├── test_condition_assessment.py# Condition tests
│   └── test_end_to_end.py         # Integration tests
├── .env.example                    # Environment template
├── .gitignore
├── Dockerfile                      # Container image
├── docker-compose.yml              # Local development
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- CUDA 11.8+ (for GPU acceleration, optional)
- Docker & Docker Compose

### Installation

1. **Clone and setup environment:**
   ```bash
   git clone <repo-url>
   cd Short-Chain-Commerce
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate mock dataset:**
   ```bash
   python scripts/generate_mock_data.py --num_images 500 --output_dir data/raw
   ```

4. **Train YOLOv8 model:**
   ```bash
   python scripts/train_model.py --data data/yolo_dataset --epochs 100
   ```

5. **Run tests:**
   ```bash
   pytest --cov=src --cov-report=html
   ```

6. **Start API server:**
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

7. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## Usage Examples

### Python SDK

```python
from src.pipeline import process_image, process_batch

# Single image
result = process_image(
    "data/raw/images/img_0001.jpg",
    source_farm="Farm-001",
    destination="Market-X"
)

print(f"Products: {len(result['extraction'].products)}")
print(f"Valid: {result['is_valid']}")
```

### Batch Processing

```python
import glob
from src.pipeline import process_batch

images = glob.glob("data/raw/images/*.jpg")
result = process_batch(images[:10], source_farm="Farm-001")

print(f"Success: {result['successful']}/{result['total_images']}")
print(f"Total products: {result['aggregation']['total_products_detected']}")
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -F "file=@image.jpg" \
  -F "source_farm=Farm-001" \
  -F "destination=Market-X"
```

---

## Core Features

### Computer Vision Pipeline

- **Object Detection** - YOLOv8 for crate and product detection
- **Multi-product Recognition** - Handle mixed crates with multiple product types
- **Condition Assessment** - Damage detection, freshness estimation, texture analysis
- **Scoring System** - 0-100 score with condition categorization

### OCR Pipeline

- **Text Extraction** - PaddleOCR integration with image enhancement
- **Date Parsing** - Multiple date format support (DD-MM-YYYY, MM-DD-YYYY, YYYY-MM-DD)
- **Product Code Extraction** - SKU, PROD pattern recognition
- **Quantity Extraction** - Units (pieces, kg, lbs) from text
- **Confidence Filtering** - 70% default threshold with manual review flagging

### Data Validation

- **Schema Validation** - Pydantic models with type safety
- **Field Validation** - Date formats, quantity bounds, enum values
- **Error Handling** - Detailed error reporting with field-level granularity
- **Missing Field Tracking** - Automatic flagging for manual input

---

## Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_schemas.py` | 20+ | Schema validation |
| `test_parser.py` | 45+ | Parsing & validation |
| `test_ocr_pipeline.py` | 40+ | OCR components |
| `test_condition_assessment.py` | 35+ | Condition assessment |
| `test_end_to_end.py` | 15+ | Pipeline integration |
| **Total** | **155+** | **80%+ target** |

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI (Python 3.10+) |
| **Object Detection** | YOLOv8 (ultralytics) |
| **OCR** | PaddleOCR |
| **Image Processing** | OpenCV, scikit-image |
| **Data Validation** | Pydantic |
| **Database** | PostgreSQL (JSONB) |
| **Queue** | Redis + Celery |
| **Containerization** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |
| **GPU Support** | CUDA 11.8+ |

---

## Development Roadmap

### Phase 1: Data Extraction & Analysis ✅ Complete
- [x] Infrastructure setup
- [x] Data schema definition
- [x] CV pipeline implementation
- [x] OCR pipeline implementation
- [x] Parser & validator
- [x] Testing framework
- [ ] Mock dataset generation
- [ ] Model training & validation

### Phase 2: Integration & Deployment (Up Next)
- [ ] End-to-end pipeline testing
- [ ] Quality assurance & refinement
- [ ] Containerization hardening
- [ ] Staging deployment
- [ ] Monitoring & logging

### Phase 3: Dashboard & UX
- [ ] UI/UX design
- [ ] Frontend development
- [ ] User testing
- [ ] Refinement sprint

### Phase 4: Production Rollout
- [ ] Security & compliance
- [ ] Performance optimization
- [ ] Production deployment
- [ ] Training & documentation

---

## Success Metrics

### Phase 1 Targets
- [x] Data schema defined & documented
- [x] CV pipeline implemented
- [x] OCR pipeline implemented
- [ ] Mock dataset: 500+ labeled images
- [ ] Object detection: ≥85% mAP50
- [ ] OCR accuracy: ≥80% character-level
- [ ] Test coverage: ≥80%

### Phase 2 Targets
- [ ] End-to-end accuracy: ≥85%
- [ ] API response time: <5s (CPU) / <2s (GPU)
- [ ] Field completeness: ≥90%

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

Copyright © 2026 Short Chain Commerce Team. All rights reserved.

---

## Contact

For questions or support, please open an issue in the repository.
