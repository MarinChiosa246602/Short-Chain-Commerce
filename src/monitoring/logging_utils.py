"""
Monitoring and Logging Module for logistics data extraction.

Provides:
- Structured logging for all extraction operations
- Performance metrics tracking
- Anomaly detection and alerting
- Health check utilities
"""

import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional

import numpy as np


class LogFormatter(logging.Formatter):
    """Custom log formatter with structured output."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ExtractionLogger:
    """
    Specialized logger for extraction operations.

    Tracks:
    - Individual extraction performance
    - Success/failure rates
    - Anomaly patterns
    """

    def __init__(
        self,
        name: str = "extraction",
        log_file: Optional[str] = None,
        console_output: bool = True,
        structured: bool = True,
    ):
        """
        Initialize the extraction logger.

        Args:
            name: Logger name
            log_file: Optional file path for log output
            console_output: Whether to output to console
            structured: Whether to use JSON format
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []  # Clear existing handlers

        if structured:
            formatter = LogFormatter()
        else:
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Metrics tracking
        self._metrics = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "partial_extractions": 0,
            "total_processing_time_ms": 0,
            "anomalies_detected": 0,
        }
        self._metrics_lock = Lock()

    def log_extraction_start(self, extraction_id: str, image_info: Dict[str, Any]):
        """Log the start of an extraction."""
        self.logger.info(
            f"Extraction started: {extraction_id}",
            extra={
                "extra_data": {
                    "event": "extraction_start",
                    "extraction_id": extraction_id,
                    **image_info,
                }
            },
        )

    def log_extraction_complete(
        self,
        extraction_id: str,
        status: str,
        processing_time_ms: float,
        products_count: int = 0,
        missing_fields: Optional[List[str]] = None,
    ):
        """Log extraction completion."""
        with self._metrics_lock:
            self._metrics["total_extractions"] += 1
            self._metrics["total_processing_time_ms"] += processing_time_ms

            if status == "success":
                self._metrics["successful_extractions"] += 1
            elif status == "partial":
                self._metrics["partial_extractions"] += 1
            else:
                self._metrics["failed_extractions"] += 1

        self.logger.info(
            f"Extraction completed: {extraction_id} ({status})",
            extra={
                "extra_data": {
                    "event": "extraction_complete",
                    "extraction_id": extraction_id,
                    "status": status,
                    "processing_time_ms": processing_time_ms,
                    "products_count": products_count,
                    "missing_fields": missing_fields,
                }
            },
        )

    def log_anomaly(
        self,
        extraction_id: str,
        anomaly_type: str,
        details: Dict[str, Any],
        severity: str = "warning",
    ):
        """Log an anomaly."""
        with self._metrics_lock:
            self._metrics["anomalies_detected"] += 1

        log_level = logging.WARNING if severity == "warning" else logging.ERROR

        self.logger.log(
            log_level,
            f"Anomaly detected: {anomaly_type}",
            extra={
                "extra_data": {
                    "event": "anomaly",
                    "extraction_id": extraction_id,
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    **details,
                }
            },
        )

    def log_batch_start(self, batch_id: str, image_count: int):
        """Log the start of a batch processing."""
        self.logger.info(
            f"Batch processing started: {batch_id}",
            extra={
                "extra_data": {
                    "event": "batch_start",
                    "batch_id": batch_id,
                    "image_count": image_count,
                }
            },
        )

    def log_batch_complete(
        self,
        batch_id: str,
        total: int,
        successful: int,
        failed: int,
        processing_time_ms: float,
    ):
        """Log batch completion."""
        self.logger.info(
            f"Batch processing completed: {batch_id}",
            extra={
                "extra_data": {
                    "event": "batch_complete",
                    "batch_id": batch_id,
                    "total": total,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": successful / total if total > 0 else 0,
                    "processing_time_ms": processing_time_ms,
                }
            },
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        with self._metrics_lock:
            metrics = self._metrics.copy()

        metrics["avg_processing_time_ms"] = (
            metrics["total_processing_time_ms"] / metrics["total_extractions"] if metrics["total_extractions"] > 0 else 0
        )

        metrics["success_rate"] = (
            metrics["successful_extractions"] / metrics["total_extractions"] if metrics["total_extractions"] > 0 else 0
        )

        return metrics

    def reset_metrics(self):
        """Reset metrics counters."""
        with self._metrics_lock:
            self._metrics = {
                "total_extractions": 0,
                "successful_extractions": 0,
                "failed_extractions": 0,
                "partial_extractions": 0,
                "total_processing_time_ms": 0,
                "anomalies_detected": 0,
            }


class PerformanceTracker:
    """Track performance metrics for pipeline components."""

    def __init__(self):
        self._timings = {
            "cv_pipeline": [],
            "ocr_pipeline": [],
            "parsing": [],
            "total": [],
        }
        self._lock = Lock()

    @contextmanager
    def track(self, component: str):
        """
        Context manager to track component timing.

        Usage:
            with tracker.track('cv_pipeline'):
                # do something
        """
        start = time.time()
        try:
            yield
        finally:
            elapsed_ms = (time.time() - start) * 1000
            with self._lock:
                self._timings[component].append(elapsed_ms)
                # Keep only last 1000 entries
                if len(self._timings[component]) > 1000:
                    self._timings[component] = self._timings[component][-1000:]

    def get_stats(self, component: str) -> Dict[str, float]:
        """Get statistics for a component."""
        with self._lock:
            timings = self._timings.get(component, [])

        if not timings:
            return {"count": 0}

        return {
            "count": len(timings),
            "min_ms": min(timings),
            "max_ms": max(timings),
            "avg_ms": sum(timings) / len(timings),
            "p50_ms": np.percentile(timings, 50),
            "p95_ms": np.percentile(timings, 95),
            "p99_ms": np.percentile(timings, 99),
        }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all components."""
        return {k: self.get_stats(k) for k in self._timings.keys()}

    def reset(self):
        """Reset all timing data."""
        with self._lock:
            self._timings = {k: [] for k in self._timings.keys()}


class AnomalyDetector:
    """Detect anomalies in extraction results."""

    def __init__(
        self,
        min_expected_products: int = 1,
        max_expected_products: int = 100,
        min_success_rate: float = 0.7,
        max_processing_time_ms: float = 10000,
    ):
        """
        Initialize anomaly detector.

        Args:
            min_expected_products: Minimum expected products per image
            max_expected_products: Maximum expected products per image
            min_success_rate: Minimum acceptable success rate
            max_processing_time_ms: Maximum acceptable processing time
        """
        self.min_expected_products = min_expected_products
        self.max_expected_products = max_expected_products
        self.min_success_rate = min_success_rate
        self.max_processing_time_ms = max_processing_time_ms

        self._recent_results = []
        self._max_history = 100

    def check_extraction(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check an extraction result for anomalies.

        Args:
            result: Extraction result dictionary

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Track results
        self._recent_results.append(result)
        if len(self._recent_results) > self._max_history:
            self._recent_results.pop(0)

        # Check product count
        products = result.get("extraction", {}).get("products", [])
        if len(products) < self.min_expected_products:
            anomalies.append(
                {
                    "type": "LOW_PRODUCT_COUNT",
                    "severity": "warning",
                    "message": f"Expected at least {self.min_expected_products} products, got {len(products)}",
                    "details": {"products_found": len(products)},
                }
            )

        if len(products) > self.max_expected_products:
            anomalies.append(
                {
                    "type": "HIGH_PRODUCT_COUNT",
                    "severity": "warning",
                    "message": f"Expected at most {self.max_expected_products} products, got {len(products)}",
                    "details": {"products_found": len(products)},
                }
            )

        # Check processing time
        processing_time = result.get("processing_time_ms", 0)
        if processing_time > self.max_processing_time_ms:
            anomalies.append(
                {
                    "type": "SLOW_PROCESSING",
                    "severity": "warning",
                    "message": f"Processing time {processing_time:.0f}ms exceeds threshold {self.max_processing_time_ms}ms",
                    "details": {"processing_time_ms": processing_time},
                }
            )

        # Check for missing fields
        missing_fields = result.get("extraction", {}).get("missing_fields", [])
        if missing_fields:
            anomalies.append(
                {
                    "type": "MISSING_FIELDS",
                    "severity": "info",
                    "message": f"Missing fields: {', '.join(missing_fields)}",
                    "details": {"missing_fields": missing_fields},
                }
            )

        # Check for low confidence fields
        low_conf_fields = result.get("extraction", {}).get("low_confidence_fields", [])
        if low_conf_fields:
            anomalies.append(
                {
                    "type": "LOW_CONFIDENCE_FIELDS",
                    "severity": "info",
                    "message": f"Low confidence fields: {', '.join(low_conf_fields)}",
                    "details": {"low_confidence_fields": low_conf_fields},
                }
            )

        return anomalies

    def get_recent_anomaly_rate(self) -> float:
        """Get the anomaly rate for recent extractions."""
        if not self._recent_results:
            return 0.0

        anomalous = sum(1 for r in self._recent_results if not r.get("is_valid", True) or r.get("missing_fields"))

        return anomalous / len(self._recent_results)


# Global instances
_extraction_logger = None
_performance_tracker = PerformanceTracker()
_anomaly_detector = AnomalyDetector()


def get_extraction_logger(
    log_file: Optional[str] = None,
    structured: bool = True,
) -> ExtractionLogger:
    """Get or create the extraction logger."""
    global _extraction_logger
    if _extraction_logger is None:
        _extraction_logger = ExtractionLogger(
            log_file=log_file,
            structured=structured,
        )
    return _extraction_logger


def get_performance_tracker() -> PerformanceTracker:
    """Get the performance tracker."""
    return _performance_tracker


def get_anomaly_detector() -> AnomalyDetector:
    """Get the anomaly detector."""
    return _anomaly_detector


def setup_logging(log_file: Optional[str] = None, level: str = "INFO"):
    """
    Configure application logging.

    Args:
        log_file: Optional file path for log output
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


if __name__ == "__main__":
    # Example usage
    setup_logging(level="DEBUG")

    logger = get_extraction_logger()
    tracker = get_performance_tracker()

    # Simulate extraction
    extraction_id = "test-001"
    logger.log_extraction_start(extraction_id, {"image_size": "640x480"})

    with tracker.track("cv_pipeline"):
        time.sleep(0.1)

    with tracker.track("ocr_pipeline"):
        time.sleep(0.2)

    with tracker.track("parsing"):
        time.sleep(0.05)

    logger.log_extraction_complete(
        extraction_id,
        status="success",
        processing_time_ms=350,
        products_count=5,
    )

    print("\nPerformance stats:")
    print(json.dumps(tracker.get_all_stats(), indent=2))

    print("\nMetrics:")
    print(json.dumps(logger.get_metrics(), indent=2))
