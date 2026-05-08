# Project 1 — Automatic Logistics Data Generation from Visual Inputs

> **In short:** An AI pipeline that turns photos of food crates and products into structured logistics data — automatically, without any manual input from the user.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Build Plan](#build-plan)
  - [Phase 1 — Foundation & Proof of Concept (Weeks 1–3)](#phase-1--foundation--proof-of-concept-weeks-13)
  - [Phase 2 — AI Vision Pipeline (Weeks 4–7)](#phase-2--ai-vision-pipeline-weeks-47)
  - [Phase 3 — API & Dashboard (Weeks 8–10)](#phase-3--api--dashboard-weeks-810)
  - [Phase 4 — Advanced Features (Weeks 11–14)](#phase-4--advanced-features-weeks-1114)
- [Output Data Format](#output-data-format)
- [Risks & Mitigations](#risks--mitigations)
- [Project Connections](#project-connections)

---

## Problem Statement

Short food supply chains (local farmers → local consumers) are extremely difficult to organize, manage, and optimize because **logistical data is almost entirely missing or entered manually**. This makes efficient, effective, and sustainable management of these chains nearly impossible.

The goal of this project is to automatically generate all necessary logistics data from **photos and visual inputs** — without users having to actively do anything. If achieved, this would represent a critical turning point in the viability of short food supply chain initiatives.

---

## Solution Overview

The system works in four steps:

1. **Capture** — A farmer or logistics worker takes a photo of a food crate or product (via phone or web app).
2. **Detect & Analyze** — An AI vision pipeline detects product types, counts items, and reads labels/expiry dates using OCR.
3. **Structure** — All visual outputs are converted into a structured JSON record and stored in a database.
4. **Visualize** — A dashboard displays current stock levels, upcoming expiries, and per-supplier quantities.

No manual data entry required.

---

## Architecture

```
[Phone / Web UI]
      │
      │  image upload
      ▼
[FastAPI Backend]
      │
      ├──► [YOLOv8 Model]        → product type + bounding boxes
      ├──► [YOLOv8-seg / SAM]    → item count per crate
      └──► [EasyOCR + Regex]     → labels, expiry dates, product codes
      │
      │  assembled JSON record
      ▼
[SQLite / PostgreSQL Database]
      │
      ▼
[Streamlit Dashboard]           → stock overview, expiry alerts, charts
      │
      ▼
[Project 2 Chatbot API]         → supply/demand matching (future integration)
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Object Detection | YOLOv8 (Ultralytics) | Detect and classify food products |
| Segmentation | YOLOv8-seg / SAM | Count individual items in a crate |
| OCR | EasyOCR / Tesseract | Extract text from labels and packaging |
| ML Framework | PyTorch | Model training and inference |
| Training GPU | Google Colab (free T4) | Fine-tune models without local hardware |
| Data Labeling | Roboflow | Annotate training images |
| Backend API | FastAPI + Uvicorn | Serve the pipeline as a REST API |
| Data Validation | Pydantic | Validate JSON records against schema |
| Database | SQLite (PoC) → PostgreSQL (prod) | Store all logistics records |
| Authentication | JWT | Multi-user / multi-farmer accounts |
| PoC Dashboard | Streamlit + Plotly | Visualize data quickly |
| Mobile App | React PWA | Camera-based image capture on mobile |
| Deployment | Docker + docker-compose | Run the full stack with one command |

---

## Build Plan

### Phase 1 — Foundation & Proof of Concept (Weeks 1–3)

**Goal:** A running skeleton with mock data, before touching any real AI.

#### Tasks

**Task 01 — Set up the project repo & environment** (~0.5 day)

Create a Git repository and set up a Python virtual environment. Define the folder structure:

```
/api          → FastAPI backend
/models       → YOLOv8 weights and training scripts
/dashboard    → Streamlit app
/data         → images, database, mock records
```

---

**Task 02 — Collect & label a mock image dataset** (~2 days)

Download ~200 food crate and product images from [Roboflow Universe](https://universe.roboflow.com) or Google's Open Images dataset. Annotate them with bounding boxes and class names using Roboflow's free annotation tool.

---

**Task 03 — Run a first YOLOv8 inference on test images** (~1 day)

Install Ultralytics and validate the environment:

```bash
pip install ultralytics
yolo predict model=yolov8n.pt source=data/test_images/
```

This gives a visual confidence check that detection is working before any custom training.

---

**Task 04 — Define the output JSON schema** (~0.5 day)

This schema drives everything downstream. Agree on all fields early:

```json
{
  "product": "tomatoes",
  "quantity": 48,
  "unit": "items",
  "expiry_date": "2025-05-15",
  "supplier_id": "farmer_007",
  "timestamp": "2025-05-08T09:30:00",
  "location": "depot_B",
  "confidence": 0.91
}
```

Implement it as a Pydantic model for automatic validation.

---

**Task 05 — Generate mock logistics records** (~1 day)

Use the Faker library to create ~500 fake orders matching the schema above. This lets you build and test the dashboard before the AI pipeline is ready.

```bash
pip install faker
python data/generate_mock.py --count 500
```

#### Phase 1 Deliverables
- Working repo with clear folder structure
- Labeled image dataset (200+ images)
- First YOLOv8 inference working locally
- Defined JSON schema & 500 mock records in SQLite

---

### Phase 2 — AI Vision Pipeline (Weeks 4–7)

**Goal:** Image in → structured JSON out, end-to-end.

#### Tasks

**Task 06 — Fine-tune YOLOv8 on your labeled dataset** (~3 days)

Train a custom model to detect your specific food products. Use Google Colab's free T4 GPU if you don't have local hardware:

```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
model.train(data="data/dataset.yaml", epochs=50, imgsz=640)
```

Export the trained weights as `models/food_detector.pt`.

---

**Task 07 — Add item counting with instance segmentation** (~2 days)

Use YOLOv8-seg to count individual items inside a crate. The output is a per-class count:

```python
results = model("data/crate_apple.jpg")
count = len(results[0].masks)  # number of detected instances
```

Alternatively, use Meta's Segment Anything Model (SAM) for more robust segmentation on unseen objects.

---

**Task 08 — Integrate OCR for label & expiry date extraction** (~2 days)

Run EasyOCR on each image to extract printed text, then parse expiry dates with regex:

```python
import easyocr
import re

reader = easyocr.Reader(['en'])
text_results = reader.readtext("data/label.jpg")
raw_text = " ".join([r[1] for r in text_results])

# Extract expiry date
match = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', raw_text)
expiry = match.group(1) if match else None
```

---

**Task 09 — Build the data-assembly module** (~2 days)

Combine all three outputs (detection + counting + OCR) into a single validated JSON record and write it to the database:

```python
from pydantic import BaseModel
from datetime import date

class LogisticsRecord(BaseModel):
    product: str
    quantity: int
    expiry_date: date | None
    supplier_id: str
    timestamp: str
    location: str
    confidence: float
```

---

**Task 10 — End-to-end pipeline test** (~2 days)

Feed 20 real photos through the full pipeline. Measure accuracy manually and fix the most common failure modes. Document results in a `tests/accuracy_report.md`.

#### Phase 2 Deliverables
- Trained YOLOv8 model (`food_detector.pt`) for food product detection
- OCR module extracting labels and expiry dates
- Pipeline script: `python pipeline/run.py --image path/to/photo.jpg`
- Accuracy report on 20 test images

---

### Phase 3 — API & Dashboard (Weeks 8–10)

**Goal:** Users can upload a photo and see results in a browser.

#### Tasks

**Task 11 — Build a FastAPI backend** (~3 days)

Expose the pipeline as a REST API with two core endpoints:

```python
# POST /analyze  →  accepts image, returns JSON record
# GET  /records  →  returns all stored logistics records

@app.post("/analyze")
async def analyze(file: UploadFile):
    result = run_pipeline(file)
    db.save(result)
    return result

@app.get("/records")
async def get_records():
    return db.fetch_all()
```

Run with: `uvicorn api.main:app --reload`

---

**Task 12 — Build a Streamlit dashboard** (~3 days)

Create a simple UI with three sections:

- **Upload** — drag-and-drop image, show detected result
- **Stock Overview** — table of current stock by product and location
- **Expiry Alerts** — products expiring within 3 days highlighted in red

```bash
streamlit run dashboard/app.py
```

---

**Task 13 — Add expiry date alerts** (~1 day)

Query the database daily for records expiring within 3 days and surface them on the dashboard. Optionally send an email alert via SMTP.

---

**Task 14 — Containerize with Docker** (~1 day)

Write a `docker-compose.yml` so the full stack launches with one command:

```bash
docker-compose up
# API running at  http://localhost:8000
# Dashboard at    http://localhost:8501
```

#### Phase 3 Deliverables
- FastAPI server with `/analyze` and `/records` endpoints
- Streamlit dashboard: upload → results → stock overview
- Expiry date alert system
- Docker container running the whole stack

---

### Phase 4 — Advanced Features (Weeks 11–14)

**Goal:** Multi-farmer support, mobile-ready, and integration with Project 2.

#### Tasks

**Task 15 — Multi-farmer / multi-user accounts** (~3 days)

Add JWT authentication so different farmers see only their own data:

```
POST /auth/login   →  returns JWT token
POST /analyze      →  requires Authorization: Bearer <token>
```

Each record in the database includes a `supplier_id` linked to the authenticated user.

---

**Task 16 — Mobile-friendly image capture** (~4 days)

Replace Streamlit with a React PWA that uses the phone camera directly. On capture, the image is compressed and sent to the FastAPI backend automatically.

---

**Task 17 — Improve model accuracy with real data** (~4 days)

Collect real images from partner farmers. Re-label them in Roboflow and retrain the YOLOv8 model on this domain-specific data. Compare mAP (mean Average Precision) before and after retraining and document the improvement.

---

**Task 18 — API integration with Project 2 (Chatbot)** (~2 days)

Expose a webhook or polling endpoint so the Project 2 AI chatbot can query current stock and expiry data in real time:

```
GET /records?supplier_id=farmer_007&expiring_within_days=3
```

This feeds the chatbot's supply/demand matching logic.

#### Phase 4 Deliverables
- Multi-user system with JWT auth
- Mobile PWA with camera capture
- Retrained model on real farm images
- Integration API ready for Project 2

---

## Output Data Format

Every image processed by the pipeline produces a record like this:

```json
{
  "id": "rec_20250508_001",
  "product": "tomatoes",
  "quantity": 48,
  "unit": "items",
  "expiry_date": "2025-05-15",
  "supplier_id": "farmer_007",
  "timestamp": "2025-05-08T09:30:00Z",
  "location": "depot_B",
  "confidence": 0.91,
  "ocr_raw": "Best before 15/05/2025 | Lot 7A",
  "image_path": "data/images/20250508_093000.jpg"
}
```

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| OCR fails on handwritten labels | 🔴 High | Fall back to manual entry; flag low-confidence results in the UI |
| Model underperforms on real farm images | 🔴 High | Collect and label real farm photos early; retrain in Phase 4 |
| No GPU available for training | 🟡 Medium | Use Google Colab free T4 GPU or Roboflow cloud training |
| JSON schema changes mid-project | 🟢 Low | Define schema in Phase 1 and use Pydantic for easy extension |
| Poor lighting / angle in field photos | 🟡 Medium | Add image preprocessing (contrast boost, rotation correction) before inference |

---

## Project Connections

This project is the **data foundation** for the other projects in the short food supply chain initiative:

- **Project 2 (Proactive AI Chatbot)** — uses the stock and expiry data from this system to negotiate supply/demand matching and optimize transport and storage sharing.
- **Project 3 (Forecasting Tool)** — can use the historical records generated by this pipeline (product type, quantities, dates) as training data for order volume forecasting.

Building this project first unlocks the data layer the other two projects depend on.

---

*Short Food Supply Chain Logistics — Project 1 Build Plan*