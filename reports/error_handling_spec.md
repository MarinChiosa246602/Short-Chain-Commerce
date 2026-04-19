# Error Handling Specification

**Date:** 2026-04-19  
**Task:** 1.6 - Data Parsing & Validation  
**Module:** `src/utils/parser.py`

---

## 1. Overview

This document specifies the error handling strategy for the data parsing and validation module. It defines:

- Validation rules and error codes
- Error handling workflows
- Missing field strategies
- Conflicting data resolution

---

## 2. Validation Rules

### 2.1 Date Validation

| Rule | Description | Error Code |
|------|---|---|
| Format Check | Must match supported date formats | `INVALID_FORMAT` |
| Future Date | Must be in the future | `PAST_DATE` |
| Parseability | Must be parseable to datetime | `PARSE_ERROR` |

**Supported Formats:**
- `YYYY-MM-DD` (e.g., 2026-12-25)
- `DD-MM-YYYY` (e.g., 25-12-2026)
- `MM-DD-YYYY` (e.g., 12-25-2026)
- `YYYY/MM/DD` (e.g., 2026/12/25)
- `DD/MM/YYYY` (e.g., 25/12/2026)
- `MM/DD/YYYY` (e.g., 12/25/2026)

### 2.2 Quantity Validation

| Rule | Description | Error Code |
|------|---|---|
| Minimum | Must be >= 1 | `BELOW_MINIMUM` |
| Maximum | Must be <= 99999 | `EXCEEDS_MAXIMUM` |
| Integer | Must be a whole number | `INVALID_TYPE` |

### 2.3 Unit Validation

| Rule | Description | Error Code |
|------|---|---|
| Valid Value | Must be in allowed list | `INVALID_UNIT` |
| Case Insensitive | Accepts any case variation | - |

**Valid Units:** crate, box, kg, lb, piece, carton, pallet

### 2.4 Product ID Validation

| Rule | Description | Error Code |
|------|---|---|
| Required | Cannot be empty | `MISSING_REQUIRED` |
| Format | Any non-empty string | - |
| Auto-generation | Generated if missing | `AUTO_GENERATED` |

### 2.5 Metadata Validation

| Field | Rule | Error Code |
|-------|------|---|
| source_farm | Required, non-empty | `MISSING_REQUIRED` |
| destination | Required, non-empty | `MISSING_REQUIRED` |
| temperature | Optional, -40 to 50 | `OUT_OF_BOUNDS` |
| humidity | Optional, 0 to 100 | `OUT_OF_BOUNDS` |

---

## 3. Error Handling Workflow

### 3.1 Parsing Workflow

```
┌─────────────────┐
│  CV + OCR Input │
└────────┬────────┘
         │
         v
┌─────────────────┐
│   Parse Data    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Validate Data  │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Valid?  │
    └────┬────┘
    Yes  │  No
    ┌────┴────┐
    │         │
    v         v
┌────────┐  ┌──────────────┐
│ Return │  │ Flag Errors  │
│ OK     │  │ Log Warnings │
└────────┘  └──────────────┘
```

### 3.2 Missing Field Handling

| Scenario | Action | Response |
|----------|--------|------|
| product_id missing | Generate UUID-based ID | Flag in `missing_fields` |
| product_name missing | Use "Unknown Product" | Flag in `missing_fields` |
| quantity missing | Default to 1 | Flag in `missing_fields` |
| expiry_date missing | Leave as null | Flag in `missing_fields` |
| condition missing | Leave as null | Flag in `missing_fields` |
| metadata missing | Use provided or "Unknown" | Return partial success |

### 3.3 Low Confidence Field Handling

| Field | Threshold | Action |
|-------|------|---|
| expiry_date | < 0.70 | Flag in `low_confidence_fields` |
| product_code | < 0.70 | Flag in `low_confidence_fields` |
| quantity | < 0.70 | Flag in `low_confidence_fields` |

---

## 4. Error Response Format

### 4.1 Validation Error Detail

```json
{
  "field": "products[0].product_id",
  "code": "MISSING_REQUIRED",
  "message": "Product ID is required"
}
```

### 4.2 Complete Error Response

```json
{
  "extraction": {
    "image_id": "uuid",
    "products": [...],
    "metadata": {...},
    "missing_fields": ["expiry_date", "condition"],
    "low_confidence_fields": []
  },
  "is_valid": false,
  "errors": [
    {
      "field": "metadata.source_farm",
      "code": "MISSING_REQUIRED",
      "message": "Source farm is required"
    }
  ],
  "processing_time_ms": 12.5
}
```

---

## 5. Conflict Resolution

### 5.1 Conflicting Data Sources

| Conflict | Resolution Priority |
|----------|--------------------|
| CV vs OCR for product type | CV detection (higher confidence) |
| Multiple product codes | First high-confidence match |
| Multiple quantities | Sum if from different regions |
| Different expiry dates | Earliest date (conservative) |

### 5.2 Logging Conflicts

Conflicts are logged with the following format:

```
[CONFLICT] Field: {field_name}
  Source A: {source_a} (confidence: {conf_a})
  Source B: {source_b} (confidence: {conf_b})
  Resolution: {chosen_value}
```

---

## 6. Test Coverage

### 6.1 Unit Tests

| Test Category | Coverage | File |
|---------------|----------|------|
| FieldValidator | 100% | `tests/test_parser.py` |
| DataParser | 100% | `tests/test_parser.py` |
| DataValidator | 100% | `tests/test_parser.py` |
| ExtractionProcessor | 100% | `tests/test_parser.py` |

### 6.2 Test Cases Summary

| Category | Tests | Status |
|----------|-------|--------|
| Valid inputs | 12 | ✅ |
| Invalid date formats | 4 | ✅ |
| Invalid quantity bounds | 6 | ✅ |
| Missing required fields | 8 | ✅ |
| Auto-generation | 2 | ✅ |
| Edge cases | 10 | ✅ |
| Conflict resolution | 3 | ✅ |

**Total:** 45+ test cases

---

## 7. Recovery Strategies

### 7.1 Automatic Recovery

| Error Type | Recovery Action |
|------------|----------------|
| Missing product_id | Generate UUID-based ID |
| Missing quantity | Default to 1 with warning |
| Invalid date format | Try alternative formats |
| Past expiry date | Reject with explanation |

### 7.2 Manual Review Triggers

Review required when:
- All confidence scores < 0.50
- Multiple conflicting interpretations
- Data out of expected bounds (e.g., 1000+ crates)
- Unparseable primary identifiers

---

## 8. Performance Requirements

| Metric | Target | Notes |
|--------|--------|-------|
| Parsing time | < 50ms | Per extraction |
| Validation time | < 10ms | Per response |
| Memory usage | < 100MB | Per request |

---

## 9. Future Enhancements

| Enhancement | Priority | Description |
|-------------|----------|-------------|
| Schema versioning | Medium | Support multiple schema versions |
| Custom validators | Low | Allow user-defined validation rules |
| Batch validation | Medium | Validate multiple extractions at once |
| Audit logging | Low | Track all parsing decisions |

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-19  
**Status:** Complete
