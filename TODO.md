# Short Chain Commerce - TODO & Implementation Gaps

**Last Updated:** 2026-05-09  
**Project:** Automated Logistics Data Extraction for Short Food Supply Chains

---

## Quick Summary

| Phase | Implementation Status | Remaining Work |
|-------|----------------------|----------------|
| **Phase 1: Base Features** | ~70% complete | ~30% |
| **Phase 2: Advanced Features** | ~10% complete | ~90% |

**Critical Path:** Before any meaningful deployment, the model MUST be trained on real farm data and accuracy validated.

---

## 🔴 CRITICAL - Must Do First

### 1. Model Training & Validation (2-3 weeks)
**Why:** Without a trained model, accuracy cannot be validated and the PoC cannot prove value.

| Task | Effort | Details |
|------|--------|---------|
| Collect 500+ real farm images | 1 week | Partner with local farmers, visit markets/warehouses |
| Annotate images with bounding boxes | 1 week | Use Roboflow or LabelImg for YOLO format |
| Train YOLOv8 model | 3-5 days | Use Google Colab free T4 GPU |
| Calculate accuracy metrics | 2-3 days | mAP@50, mAP@50-95, precision, recall per class |
| Document accuracy report | 1 day | Create `reports/accuracy_report.md` |

**Files involved:** `scripts/train_model.py`, `data/yolo_dataset/`, `runs/detect/`

### 2. GPS/Geolocation Integration (1 week)
**Why:** Required for traceability and automatic farm identification.

| Task | Effort | Details |
|------|--------|---------|
| Extract GPS from image EXIF | 2-3 days | Use `exifread` or `PIL` library |
| Build farm location database | 2 days | Create geofencing boundaries |
| Auto-detect source farm | 2-3 days | Match GPS coordinates to known farms |

**Files to create/modify:** `src/database/db_manager.py`, `src/models/schemas.py` (add GPS fields)

### 3. Yield Estimation Integration (2 weeks)
**Why:** Core requirement for supply foresight and planning.

| Task | Effort | Details |
|------|--------|---------|
| Identify/Build yield estimation API | 1 week | Integrate with existing Project 3 or build stub |
| Connect to logistics pipeline | 3-4 days | Add upcoming supply to extraction records |
| Build upcoming supply display | 2-3 days | Dashboard component showing projected inventory |
| Create seasonal planning calendar | 3-4 days | Seasonal availability visualization |

---

## 🟠 HIGH PRIORITY - Core Features

### 4. Multi-Tenant Architecture (3 weeks)
**Why:** Essential for multiple farmers to use the system simultaneously.

| Task | Effort | Details |
|------|--------|---------|
| Complete JWT authentication | 1 week | `src/api/security.py` has partial implementation |
| Implement user registration/login | 3-4 days | Farmer and organization accounts |
| Data isolation per user | 3-4 days | All queries filtered by user ID |
| API key management for stakeholders | 3-4 days | Generate/revoke keys for partners |

**Files involved:** `src/api/security.py`, `src/database/db_manager.py`

### 5. Mobile Camera Capture (2 days)
**Why:** Field workers need to capture images directly, not upload from gallery.

| Task | Effort | Details |
|------|--------|---------|
| Integrate device camera API | 2 days | Use `<input type="file" capture>` or Camera API |

**Files to create/modify:** `web/src/components/Extraction.jsx`, `web/src/components/CameraDashboard.jsx`

### 6. Image Quality Validation (1 day)
**Why:** Prevent processing of unusable images (blur, too dark, wrong angle).

| Task | Effort | Details |
|------|--------|---------|
| Implement blur detection | 4 hours | Laplacian variance method |
| Implement lighting validation | 4 hours | Check histogram/brightness |
| Show quality feedback before upload | 4 hours | User prompt to retake if needed |

**Files to create:** `src/utils/image_quality.py`

### 7. Handwritten OCR Support (2 weeks)
**Why:** Many farm labels are handwritten, current PaddleOCR primarily handles printed text.

| Task | Effort | Details |
|------|--------|---------|
| Evaluate handwritten OCR solutions | 1 week | TrOCR, Google Vision API, Azure Computer Vision |
| Integrate handwritten OCR | 1 week | Fallback for low-confidence printed text |

### 8. Route Optimization (3 weeks)
**Why:** Major value proposition for logistics efficiency.

| Task | Effort | Details |
|------|--------|---------|
| Implement vehicle routing algorithm | 2 weeks | OR-Tools or similar |
| Add delivery scheduling | 1 week | Time windows, capacity constraints |
| Build route visualization | 1 week | Map-based display |

**Files to create:** `src/logistics/routing.py`, `web/src/components/RouteOptimizer.jsx`

### 9. Storage Suggestions (2 weeks)
**Why:** Intelligent warehouse placement reduces handling and spoilage.

| Task | Effort | Details |
|------|--------|---------|
| Build cold chain requirement database | 1 week | Product-specific storage rules |
| Implement warehouse capacity tracking | 3-4 days | Real-time storage monitoring |
| Create placement algorithm | 3-4 days | Optimize based on product/temperature/expiry |

---

## 🟡 MEDIUM PRIORITY - Important Features

### 10. Real-World Testing & Validation (1 week)
**Why:** Must prove the system works outside controlled conditions.

| Task | Effort | Details |
|------|--------|---------|
| Field test with partner farmers | 3-4 days | Deploy to 2-3 actual farms |
| Test in varied lighting conditions | 2 days | Morning, afternoon, warehouse lighting |
| Document failure modes | 1 day | Create failure analysis report |
| Calculate real-world accuracy | 1 day | Compare extracted vs actual data |

### 11. Passive Collection Workflow (2-3 weeks)
**Why:** Key differentiator - hands-free data collection.

| Task | Effort | Details |
|------|--------|---------|
| Fixed camera integration | 1 week | Warehouse/loading dock camera feeds |
| Automatic image triggering | 3-4 days | Motion sensors, weight scales integration |
| Edge device deployment | 1 week | Raspberry Pi/Jetson Nano setup |

### 12. Consumer-Facing Features (2-3 weeks)
**Why:** End consumers want traceability and transparency.

| Task | Effort | Details |
|------|--------|---------|
| Build consumer API access | 1 week | Limited read-only endpoints |
| Create consumer dashboard | 1 week | Product origin, quality history |
| Implement QR code generation | 3-4 days | Traceability codes on products |

### 13. Real-Time Notifications (2 weeks)
**Why:** Immediate alerts for critical events.

| Task | Effort | Details |
|------|--------|---------|
| Implement WebSocket/SSE | 1 week | Real-time updates |
| Create alert types | 3-4 days | Expiry warnings, stock low, quality issues |
| Build notification preferences | 3-4 days | User-configurable alerts |

### 14. Cold Chain Optimization (2 weeks)
**Why:** Temperature management is critical for food safety.

| Task | Effort | Details |
|------|--------|---------|
| Build temperature monitoring | 1 week | IoT sensor integration |
| Create cold chain alerts | 3-4 days | Breach detection and notifications |
| Implement temperature recommendations | 3-4 days | Storage condition suggestions |

---

## 🟢 LOW PRIORITY - Nice to Have

### 15. Expand Product Categories (1 week)
| Task | Effort | Details |
|------|--------|---------|
| Add support for more product types | 1 week | Beyond current 8 classes |

### 16. Batch Scanner (3-4 days)
| Task | Effort | Details |
|------|--------|---------|
| Multi-image batch processing | 3-4 days | Process entire pallet at once |

**Files:** `web/src/components/BatchScanner.jsx` (exists, may need implementation)

### 17. Analytics Dashboard (3-4 days)
| Task | Effort | Details |
|------|--------|---------|
| Build advanced analytics | 3-4 days | Trends, forecasts, insights |

**Files:** `web/src/components/AnalyticsDashboard.jsx` (exists, may need implementation)

### 18. Reports Generation (2-3 days)
| Task | Effort | Details |
|------|--------|---------|
| Create PDF reports | 2-3 days | Daily/weekly/monthly summaries |

**Files:** `web/src/components/Reports.jsx` (exists, may need implementation)

### 19. Consumer Feedback Integration (1 week)
| Task | Effort | Details |
|------|--------|---------|
| Quality reporting system | 1 week | Consumer can report issues |

---

## 📋 Technical Debt & Cleanup

### Code Quality
| Task | Effort | Priority |
|------|--------|----------|
| Migrate from Pydantic V1 to V2 validators | 3-4 days | Medium |
| Add proper type hints throughout | 1 week | Low |
| Increase test coverage to 75%+ | 1 week | Medium |
| Document all public APIs | 3-4 days | Low |

### Current Coverage: 58.97% (Target: 55% minimum)

### Known Issues
1. **Pydantic deprecation warnings** - `@validator` should be `@field_validator`
2. **datetime.utcnow() deprecation** - Use `datetime.now(timezone.utc)`
3. **PaddleOCR `use_angle_cls` deprecation** - Use `use_textline_orientation`

### Missing Documentation
- [ ] API usage examples
- [ ] Model training guide
- [ ] Deployment checklist
- [ ] Troubleshooting guide

---

## 📊 Success Criteria (Not Yet Achieved)

| Criterion | Target | Current Status |
|-----------|--------|----------------|
| OCR Accuracy | 80%+ | NOT MEASURED |
| Object Detection Accuracy | 85%+ | NOT MEASURED |
| Zero manual data entry | 100% | PARTIAL (metadata still manual) |
| Real-world validation | Demonstrated | NOT DONE |
| Food waste reduction evidence | Quantified | NOT DONE |

---

## 🗓️ Recommended Sprint Plan

### Sprint 1-2: Model Training & Validation (4 weeks)
1. Collect and annotate 500+ real farm images
2. Train YOLOv8 model on custom dataset
3. Calculate and document accuracy metrics
4. Implement GPS metadata capture

### Sprint 3-4: Core Integration (4 weeks)
1. Complete user authentication (JWT)
2. Build multi-tenant data layer
3. Integrate yield estimation API
4. Add mobile camera capture

### Sprint 5-6: Advanced Features (4 weeks)
1. Implement route optimization
2. Build passive collection prototype
3. Add handwritten OCR support
4. Create consumer API

### Sprint 7-8: Polish & Demo (4 weeks)
1. Mobile optimization and testing
2. Real-world field testing
3. Complete documentation
4. Prepare PoC demonstration

---

## 📁 Files Reference

### Core Implementation
| Component | Primary Files |
|-----------|---------------|
| CV Pipeline | `src/models/cv_pipeline.py`, `src/models/condition_assessment.py` |
| OCR | `src/models/ocr_pipeline.py` |
| API | `src/api/main.py`, `src/database/db_manager.py` |
| Pipeline | `src/pipeline/end_to_end.py` |
| Schemas | `src/models/schemas.py` |

### Frontend
| Component | Primary Files |
|-----------|---------------|
| Dashboard | `web/src/components/Dashboard.jsx` |
| Extraction | `web/src/components/Extraction.jsx` |
| History | `web/src/components/History.jsx` |
| API Service | `web/src/services/api.js` |

### Data & Scripts
| Component | Primary Files |
|-----------|---------------|
| Mock Data | `scripts/generate_mock_data.py` |
| Model Training | `scripts/train_model.py` |
| YOLO Dataset | `data/yolo_dataset/` |

### DevOps
| Component | Primary Files |
|-----------|---------------|
| Docker | `Dockerfile`, `docker-compose.yml` |
| CI/CD | `.github/workflows/deploy.yml` |
| Monitoring | `monitoring/prometheus.yml` |

---

## 📞 Getting Help

For questions about specific components:
- **CV/ML Issues**: Check `reports/ocr_error_analysis.md`
- **API Issues**: Review `docs/DATA_SCHEMA.md`
- **Frontend Issues**: See `web/README.md`
- **General Progress**: See `docs/IMPLEMENTATION_STATUS.md`

---

*This document should be updated after each sprint to reflect completed work and changing priorities.*
