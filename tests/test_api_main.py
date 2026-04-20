"""Tests for the FastAPI application entrypoints."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
import runpy
import sys

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import api.main as api_main


def _jpeg_bytes() -> bytes:
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".jpg", image)
    assert success
    return encoded.tobytes()


def _make_extraction():
    product = SimpleNamespace(
        product_id="SKU-1",
        product_name="Tomato",
        quantity=3,
        unit=SimpleNamespace(value="piece"),
        expiry_date=datetime(2026, 12, 31),
        storage_location="Shelf-A",
        condition=SimpleNamespace(value="good"),
    )
    metadata = SimpleNamespace(
        source_farm="Farm-A",
        destination="Depot-B",
        temperature=4.0,
        humidity=80.0,
    )
    return SimpleNamespace(
        image_id="00000000-0000-0000-0000-000000000001",
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
        products=[product],
        metadata=metadata,
        missing_fields=["product_id"],
        low_confidence_fields=["expiry_date"],
    )


@pytest.fixture()
def client():
    api_main._extraction_pipeline = None
    api_main._batch_processor = None
    api_main.metrics.update(
        {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time_ms": 0,
            "requests_by_status": {},
        }
    )
    return TestClient(api_main.app)


def test_root_and_health(client):
    root = client.get("/")
    health = client.get("/health")

    assert root.status_code == 200
    assert root.json()["status"] == "running"
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


def test_metrics_endpoint_and_helper_updates(client):
    api_main.update_metrics("success", 10.0)
    api_main.update_metrics("partial", 5.0)
    api_main.update_metrics("error", 7.0)

    response = client.get("/api/v1/metrics")
    payload = response.json()

    assert response.status_code == 200
    assert payload["total_requests"] == 3
    assert payload["successful_requests"] == 2
    assert payload["failed_requests"] == 1
    assert payload["requests_by_status"]["success"] == 1
    assert payload["requests_by_status"]["partial"] == 1
    assert payload["requests_by_status"]["error"] == 1


def test_extract_success_response(client, monkeypatch):
    pipeline = SimpleNamespace(
        process=lambda **kwargs: {
            "status": "success",
            "is_valid": True,
            "errors": [],
            "extraction": _make_extraction(),
        }
    )
    monkeypatch.setattr(api_main, "get_pipeline", lambda: pipeline)

    response = client.post(
        "/api/v1/extract",
        files={"file": ("test.jpg", _jpeg_bytes(), "image/jpeg")},
        data={"source_farm": "Farm-A", "destination": "Depot-B"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["data"]["products"][0]["product_id"] == "SKU-1"
    assert body["data"]["metadata"]["source_farm"] == "Farm-A"


def test_extract_partial_and_error_paths(client, monkeypatch):
    partial_pipeline = SimpleNamespace(
        process=lambda **kwargs: {
            "status": "partial",
            "is_valid": False,
            "errors": [{"field": "product_id", "code": "MISSING_REQUIRED"}],
            "extraction": _make_extraction(),
        }
    )
    monkeypatch.setattr(api_main, "get_pipeline", lambda: partial_pipeline)

    partial_response = client.post(
        "/api/v1/extract",
        files={"file": ("test.jpg", _jpeg_bytes(), "image/jpeg")},
    )

    assert partial_response.status_code == 200
    assert partial_response.json()["status"] == "partial"

    error_pipeline = SimpleNamespace(
        process=lambda **kwargs: {"status": "error", "error": "boom"}
    )
    monkeypatch.setattr(api_main, "get_pipeline", lambda: error_pipeline)

    error_response = client.post(
        "/api/v1/extract",
        files={"file": ("test.jpg", _jpeg_bytes(), "image/jpeg")},
    )

    assert error_response.status_code == 500
    assert error_response.json()["status"] == "error"


def test_extract_validates_file_type_and_image(client):
    bad_type = client.post(
        "/api/v1/extract",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    invalid_image = client.post(
        "/api/v1/extract",
        files={"file": ("test.jpg", b"not-an-image", "image/jpeg")},
    )

    assert bad_type.status_code == 400
    assert invalid_image.status_code == 400


def test_batch_and_detailed_health(client, monkeypatch):
    batch_result = {
        "total_images": 2,
        "successful": 2,
        "failed": 0,
        "success_rate": 1.0,
        "processing_time_ms": 12.5,
        "aggregation": {"total_products_detected": 2},
        "results": [{"status": "success"}, {"status": "success"}],
        "anomalies": [],
    }
    batch_processor = SimpleNamespace(process_batch=lambda **kwargs: batch_result)
    monkeypatch.setattr(api_main, "get_batch_processor", lambda: batch_processor)

    batch_response = client.post(
        "/api/v1/extract/batch",
        files=[
            ("files", ("a.jpg", _jpeg_bytes(), "image/jpeg")),
            ("files", ("b.jpg", _jpeg_bytes(), "image/jpeg")),
        ],
        data={"source_farm": "Farm-A", "destination": "Depot-B"},
    )

    assert batch_response.status_code == 200
    assert batch_response.json()["batch_summary"]["successful"] == 2

    pipeline = SimpleNamespace(cv_pipeline=True, ocr_pipeline=True, processor=True)
    monkeypatch.setattr(api_main, "get_pipeline", lambda: pipeline)
    detailed = client.get("/api/v1/health/detailed")

    assert detailed.status_code == 200
    assert detailed.json()["components"]["cv_pipeline"] == "initialized"


def test_batch_rejects_too_many_files(client):
    files = [("files", (f"img_{i}.jpg", _jpeg_bytes(), "image/jpeg")) for i in range(51)]
    response = client.post("/api/v1/extract/batch", files=files)

    assert response.status_code == 400


def test_get_pipeline_and_batch_processor_helpers(monkeypatch):
    api_main._extraction_pipeline = None
    api_main._batch_processor = None

    fake_pipeline = SimpleNamespace()
    fake_batch = SimpleNamespace()
    monkeypatch.setattr(api_main, "EndToEndPipeline", lambda config=None: fake_pipeline)
    monkeypatch.setattr(api_main, "BatchProcessor", lambda config=None: fake_batch)

    assert api_main.get_pipeline() is fake_pipeline
    assert api_main.get_pipeline() is fake_pipeline
    assert api_main.get_batch_processor() is fake_batch
    assert api_main.get_batch_processor() is fake_batch


def test_batch_endpoint_error_path(client, monkeypatch):
    batch_processor = SimpleNamespace(process_batch=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("batch failed")))
    monkeypatch.setattr(api_main, "get_batch_processor", lambda: batch_processor)

    response = client.post(
        "/api/v1/extract/batch",
        files=[("files", ("a.jpg", _jpeg_bytes(), "image/jpeg"))],
    )

    assert response.status_code == 500


def test_schemas_endpoint(client):
    response = client.get("/api/v1/schemas")

    assert response.status_code == 200
    assert "extraction_request" in response.json()


def test_module_entrypoint_calls_uvicorn(monkeypatch):
    called = {"count": 0}

    def fake_run(*args, **kwargs):
        called["count"] += 1

    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=fake_run))
    runpy.run_module("api.main", run_name="__main__")

    assert called["count"] == 1
