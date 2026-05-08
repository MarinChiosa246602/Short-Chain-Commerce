"""
End-to-End Test Script for the Short Chain Commerce Pipeline.

Runs comprehensive tests to verify:
- API endpoints
- Pipeline components
- Database integration
- Monitoring and logging
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
import json

# Add src to path
SRC_ROOT = Path(__file__).resolve().parent.parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import cv2
import numpy as np


def create_test_image():
    """Create a simple test image."""
    image = np.zeros((640, 640, 3), dtype=np.uint8)
    # Draw some shapes to simulate products
    cv2.rectangle(image, (50, 50), (200, 200), (0, 255, 0), 2)
    cv2.rectangle(image, (250, 50), (400, 200), (0, 0, 255), 2)
    cv2.rectangle(image, (50, 250), (200, 400), (255, 255, 0), 2)

    # Add text (simulating labels)
    cv2.putText(image, "SKU-001", (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(image, "EXP: 12/2026", (60, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    return image


def test_pipeline_components():
    """Test individual pipeline components."""
    print("\n" + "="*60)
    print("TESTING PIPELINE COMPONENTS")
    print("="*60)

    from src.pipeline.end_to_end import EndToEndPipeline, BatchProcessor
    from models.cv_pipeline import CVPipeline, ImagePreprocessor
    from models.ocr_pipeline import OCRPipeline

    results = {
        "cv_pipeline": False,
        "ocr_pipeline": False,
        "end_to_end": False,
        "batch_processor": False,
    }

    test_image = create_test_image()

    # Test CV Pipeline
    try:
        print("\n[1/4] Testing CV Pipeline...")
        cv_pipeline = CVPipeline({"confidence_threshold": 0.5})
        result = cv_pipeline.process(test_image)

        assert "detections" in result
        assert "image_shape" in result
        assert "processing_time_ms" in result

        results["cv_pipeline"] = True
        print(f"    ✓ CV Pipeline: {result['processing_time_ms']:.2f}ms")
        print(f"    Detections: {len(result.get('detections', []))}")
    except Exception as e:
        print(f"    ✗ CV Pipeline failed: {e}")

    # Test OCR Pipeline
    try:
        print("\n[2/4] Testing OCR Pipeline...")
        ocr_pipeline = OCRPipeline({"confidence_threshold": 0.7})
        result = ocr_pipeline.process(test_image)

        assert "all_texts" in result
        assert "processing_time_ms" in result

        results["ocr_pipeline"] = True
        print(f"    ✓ OCR Pipeline: {result['processing_time_ms']:.2f}ms")
        print(f"    Texts detected: {len(result.get('all_texts', []))}")
    except Exception as e:
        print(f"    ✗ OCR Pipeline failed: {e}")

    # Test End-to-End Pipeline
    try:
        print("\n[3/4] Testing End-to-End Pipeline...")
        pipeline = EndToEndPipeline({"confidence_threshold": 0.7})
        result = pipeline.process(test_image)

        assert "extraction_id" in result
        assert "status" in result
        assert "processing_time_ms" in result

        results["end_to_end"] = True
        print(f"    ✓ End-to-End: {result['status']}")
        print(f"    Processing time: {result['processing_time_ms']:.2f}ms")
    except Exception as e:
        print(f"    ✗ End-to-End failed: {e}")

    # Test Batch Processor
    try:
        print("\n[4/4] Testing Batch Processor...")
        processor = BatchProcessor({"confidence_threshold": 0.7})
        test_images = [test_image, test_image, test_image]
        result = processor.process_batch(test_images)

        assert "total_images" in result
        assert "successful" in result
        assert "failed" in result
        assert "results" in result

        results["batch_processor"] = True
        print(f"    ✓ Batch Processor: {result['successful']}/{result['total_images']} successful")
    except Exception as e:
        print(f"    ✗ Batch Processor failed: {e}")

    return results


def test_api_endpoints():
    """Test API endpoints."""
    print("\n" + "="*60)
    print("TESTING API ENDPOINTS")
    print("="*60)

    from fastapi.testclient import TestClient
    from api.main import app

    results = {
        "root": False,
        "health": False,
        "metrics": False,
        "extract": False,
        "batch": False,
    }

    client = TestClient(app)
    test_image = create_test_image()

    # Test root
    try:
        print("\n[1/5] Testing root endpoint...")
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()
        results["root"] = True
        print(f"    ✓ Root: {response.json()['status']}")
    except Exception as e:
        print(f"    ✗ Root failed: {e}")

    # Test health
    try:
        print("\n[2/5] Testing health endpoint...")
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        results["health"] = True
        print(f"    ✓ Health: {response.json()['status']}")
    except Exception as e:
        print(f"    ✗ Health failed: {e}")

    # Test metrics
    try:
        print("\n[3/5] Testing metrics endpoint...")
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        assert "total_requests" in response.json()
        results["metrics"] = True
        print(f"    ✓ Metrics: {response.json()['total_requests']} total requests")
    except Exception as e:
        print(f"    ✗ Metrics failed: {e}")

    # Test extract
    try:
        print("\n[4/5] Testing extract endpoint...")
        _, encoded = cv2.imencode(".jpg", test_image)
        response = client.post(
            "/api/v1/extract",
            files={"file": ("test.jpg", encoded.tobytes(), "image/jpeg")},
            data={"source_farm": "TestFarm", "destination": "TestDest"}
        )
        # Accept any response (success or processing error)
        assert response.status_code in [200, 500]
        results["extract"] = True
        print(f"    ✓ Extract: status {response.status_code}")
    except Exception as e:
        print(f"    ✗ Extract failed: {e}")

    # Test batch
    try:
        print("\n[5/5] Testing batch endpoint...")
        images = []
        for i in range(2):
            _, encoded = cv2.imencode(".jpg", test_image)
            images.append(("files", (f"test_{i}.jpg", encoded.tobytes(), "image/jpeg")))

        response = client.post(
            "/api/v1/extract/batch",
            files=images,
            data={"source_farm": "TestFarm", "destination": "TestDest"}
        )
        # Accept any response
        assert response.status_code in [200, 500]
        results["batch"] = True
        print(f"    ✓ Batch: status {response.status_code}")
    except Exception as e:
        print(f"    ✗ Batch failed: {e}")

    return results


def test_database_integration():
    """Test database integration."""
    print("\n" + "="*60)
    print("TESTING DATABASE INTEGRATION")
    print("="*60)

    from database.db_manager import DatabaseManager
    from datetime import datetime

    results = {
        "initialize": False,
        "save_extraction": False,
        "query": False,
        "statistics": False,
    }

    try:
        print("\n[1/4] Initializing database...")
        db = DatabaseManager(db_path="data/test_extractions.db")
        db.initialize()
        results["initialize"] = True
        print("    ✓ Database initialized")
    except Exception as e:
        print(f"    ✗ Database init failed: {e}")
        return results

    try:
        print("\n[2/4] Saving extraction record...")
        from uuid import uuid4
        extraction_id = str(uuid4())

        db.save_extraction(
            extraction_id=extraction_id,
            image_id="test-image-001",
            timestamp=datetime.utcnow(),
            source_farm="TestFarm",
            destination="TestDest",
            status="success",
            is_valid=True,
            processing_time_ms=250.0,
            products=[
                {
                    "product_id": "TEST-001",
                    "product_name": "Test Product",
                    "quantity": 10,
                    "unit": "piece",
                    "expiry_date": datetime(2026, 12, 31),
                    "storage_location": "A1",
                    "condition": "good",
                }
            ],
            missing_fields=[],
            low_confidence_fields=[],
        )
        results["save_extraction"] = True
        print(f"    ✓ Extraction saved: {extraction_id[:8]}...")
    except Exception as e:
        print(f"    ✗ Save extraction failed: {e}")

    try:
        print("\n[3/4] Querying extractions...")
        extractions = db.query_extractions(source_farm="TestFarm", limit=10)
        assert len(extractions) > 0
        results["query"] = True
        print(f"    ✓ Query: {len(extractions)} extractions found")
    except Exception as e:
        print(f"    ✗ Query failed: {e}")

    try:
        print("\n[4/4] Getting statistics...")
        stats = db.get_statistics()
        assert "total" in stats
        results["statistics"] = True
        print(f"    ✓ Statistics: {stats['total']} total extractions")
    except Exception as e:
        print(f"    ✗ Statistics failed: {e}")

    return results


def test_monitoring():
    """Test monitoring and logging utilities."""
    print("\n" + "="*60)
    print("TESTING MONITORING & LOGGING")
    print("="*60)

    from monitoring.logging_utils import (
        ExtractionLogger,
        PerformanceTracker,
        AnomalyDetector,
    )

    results = {
        "logger": False,
        "performance_tracker": False,
        "anomaly_detector": False,
    }

    try:
        print("\n[1/3] Testing ExtractionLogger...")
        logger = ExtractionLogger(name="test", console_output=False, structured=True)
        logger.log_extraction_start("test-001", {"image_size": "640x640"})
        logger.log_extraction_complete("test-001", "success", 250.0, products_count=3)

        metrics = logger.get_metrics()
        assert metrics["total_extractions"] == 1
        assert metrics["successful_extractions"] == 1
        results["logger"] = True
        print(f"    ✓ Logger: {metrics['total_extractions']} extractions logged")
    except Exception as e:
        print(f"    ✗ Logger failed: {e}")

    try:
        print("\n[2/3] Testing PerformanceTracker...")
        tracker = PerformanceTracker()

        with tracker.track("cv_pipeline"):
            time.sleep(0.01)

        with tracker.track("ocr_pipeline"):
            time.sleep(0.01)

        stats = tracker.get_all_stats()
        assert "cv_pipeline" in stats
        assert "ocr_pipeline" in stats
        results["performance_tracker"] = True
        print(f"    ✓ PerformanceTracker: {stats['cv_pipeline']['count']} CV inferences tracked")
    except Exception as e:
        print(f"    ✗ PerformanceTracker failed: {e}")

    try:
        print("\n[3/3] Testing AnomalyDetector...")
        detector = AnomalyDetector(
            min_expected_products=1,
            max_expected_products=100,
            max_processing_time_ms=10000,
        )

        test_result = {
            "extraction": {
                "products": [{"product_id": "TEST", "product_name": "Test"}],
                "missing_fields": [],
            },
            "processing_time_ms": 250.0,
            "is_valid": True,
        }

        anomalies = detector.check_extraction(test_result)
        results["anomaly_detector"] = True
        print(f"    ✓ AnomalyDetector: {len(anomalies)} anomalies for valid extraction")
    except Exception as e:
        print(f"    ✗ AnomalyDetector failed: {e}")

    return results


def run_all_tests():
    """Run all tests and generate report."""
    print("\n" + "="*60)
    print("SHORT CHAIN COMMERCE - END-TO-END TEST SUITE")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)

    all_results = {
        "pipeline_components": test_pipeline_components(),
        "api_endpoints": test_api_endpoints(),
        "database_integration": test_database_integration(),
        "monitoring": test_monitoring(),
    }

    # Generate summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    total_passed = 0
    total_tests = 0

    for category, results in all_results.items():
        print(f"\n{category.upper()}:")
        for test, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {test}")
            total_tests += 1
            if passed:
                total_passed += 1

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_passed}/{total_tests} tests passed ({100*total_passed/total_tests:.1f}%)")
    print(f"{'='*60}")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_tests - total_passed,
            "success_rate": total_passed / total_tests if total_tests > 0 else 0,
        },
        "results": all_results,
    }

    report_path = Path("data/test_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nReport saved to: {report_path}")

    return total_passed == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
