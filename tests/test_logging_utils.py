"""Tests for monitoring and logging utilities."""

from __future__ import annotations

import json
import logging
import sys
import runpy
from types import SimpleNamespace

import pytest

import monitoring.logging_utils as logmod


def test_log_formatter_handles_extra_and_exception():
    formatter = logmod.LogFormatter()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.extra_data = {"request_id": "abc123"}
    formatted = formatter.format(record)
    payload = json.loads(formatted)

    assert payload["logger"] == "test_logger"
    assert payload["request_id"] == "abc123"

    try:
        raise ValueError("boom")
    except ValueError:
        record.exc_info = sys.exc_info()

    exception_payload = json.loads(formatter.format(record))
    assert "exception" in exception_payload


def test_extraction_logger_updates_metrics():
    logger = logmod.ExtractionLogger(name="test_extraction", console_output=False)

    logger.log_extraction_start("ext-1", {"image_size": "640x480"})
    logger.log_extraction_complete("ext-1", status="success", processing_time_ms=100.0, products_count=2)
    logger.log_extraction_complete("ext-2", status="partial", processing_time_ms=50.0, products_count=1)
    logger.log_extraction_complete("ext-3", status="error", processing_time_ms=25.0, products_count=0)
    logger.log_anomaly("ext-1", "TEST", {"field": "value"})
    logger.log_anomaly("ext-2", "TEST_ERROR", {"field": "value"}, severity="error")
    logger.log_batch_start("batch-1", 3)
    logger.log_batch_complete("batch-1", total=3, successful=2, failed=1, processing_time_ms=250.0)

    metrics = logger.get_metrics()
    assert metrics["total_extractions"] == 3
    assert metrics["successful_extractions"] == 1
    assert metrics["partial_extractions"] == 1
    assert metrics["failed_extractions"] == 1
    assert metrics["anomalies_detected"] == 2
    assert metrics["avg_processing_time_ms"] == pytest.approx(58.333, rel=1e-3)

    logger.reset_metrics()
    assert logger.get_metrics()["total_extractions"] == 0


def test_performance_tracker_tracks_and_resets():
    tracker = logmod.PerformanceTracker()

    with tracker.track("cv_pipeline"):
        pass

    stats = tracker.get_stats("cv_pipeline")
    assert stats["count"] == 1
    assert stats["avg_ms"] >= 0
    assert tracker.get_stats("missing") == {"count": 0}
    assert "cv_pipeline" in tracker.get_all_stats()

    tracker.reset()
    assert tracker.get_stats("cv_pipeline") == {"count": 0}


def test_anomaly_detector_reports_anomalies_and_rate():
    detector = logmod.AnomalyDetector(
        min_expected_products=2,
        max_expected_products=3,
        max_processing_time_ms=100,
    )

    low_result = {
        "extraction": {"products": [], "missing_fields": ["product_id"], "low_confidence_fields": ["expiry_date"]},
        "processing_time_ms": 200,
        "is_valid": False,
    }
    low_anomalies = detector.check_extraction(low_result)
    low_types = {item["type"] for item in low_anomalies}

    assert "LOW_PRODUCT_COUNT" in low_types
    assert "SLOW_PROCESSING" in low_types
    assert "MISSING_FIELDS" in low_types
    assert "LOW_CONFIDENCE_FIELDS" in low_types

    high_result = {
        "extraction": {"products": [{}, {}, {}, {}]},
        "processing_time_ms": 1,
        "is_valid": True,
    }
    high_types = {item["type"] for item in detector.check_extraction(high_result)}
    assert "HIGH_PRODUCT_COUNT" in high_types

    assert detector.get_recent_anomaly_rate() > 0


def test_anomaly_detector_empty_rate():
    detector = logmod.AnomalyDetector()
    assert detector.get_recent_anomaly_rate() == 0.0


def test_logging_helpers_return_singletons_and_configure_logging():
    logmod._extraction_logger = None
    first = logmod.get_extraction_logger(structured=False)
    second = logmod.get_extraction_logger(structured=False)

    assert first is second
    assert logmod.get_performance_tracker() is logmod.get_performance_tracker()
    assert logmod.get_anomaly_detector() is logmod.get_anomaly_detector()

    logmod.setup_logging(level="WARNING")


def test_logging_file_handler_and_history_trimming(tmp_path, monkeypatch):
    logger = logmod.ExtractionLogger(name="file_logger", log_file=str(tmp_path / "extraction.log"), console_output=False)
    logger.log_extraction_start("ext-1", {"image_size": "640x480"})
    logger.log_extraction_complete("ext-1", status="success", processing_time_ms=10.0)

    tracker = logmod.PerformanceTracker()
    tracker._timings["cv_pipeline"] = list(range(1001))
    with tracker.track("cv_pipeline"):
        pass

    detector = logmod.AnomalyDetector()
    for index in range(101):
        detector.check_extraction({"extraction": {"products": []}, "processing_time_ms": 0, "is_valid": index % 2 == 0})

    logmod.setup_logging(log_file=str(tmp_path / "app.log"), level="INFO")

    assert len(tracker._timings["cv_pipeline"]) == 1000
    assert len(detector._recent_results) == 100


def test_module_entrypoint_runs_example(monkeypatch):
    monkeypatch.setattr(logmod.time, "sleep", lambda seconds: None)
    runpy.run_module("monitoring.logging_utils", run_name="__main__")
