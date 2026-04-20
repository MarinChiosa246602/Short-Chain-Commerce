"""Additional end-to-end tests to cover remaining branches."""

from __future__ import annotations

import argparse
import runpy
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from pipeline.end_to_end import BatchProcessor, EndToEndPipeline, ErrorRecovery, process_batch, process_image


def _image() -> np.ndarray:
    return np.zeros((32, 32, 3), dtype=np.uint8)


def _extraction():
    return SimpleNamespace(
        image_id="img-1",
        timestamp=SimpleNamespace(isoformat=lambda: "2026-01-01T00:00:00"),
        products=[SimpleNamespace(product_id="SKU-1", product_name="Tomato", quantity=3, unit=SimpleNamespace(value="piece"), expiry_date=None, storage_location=None, condition=None)],
        metadata=SimpleNamespace(source_farm="Farm-A", destination="Depot-B", temperature=None, humidity=None),
        missing_fields=[],
        low_confidence_fields=[],
    )


def _pipeline():
    with patch("pipeline.end_to_end.CVPipeline"), patch("pipeline.end_to_end.OCRPipeline"), patch("pipeline.end_to_end.ExtractionProcessor"):
        return EndToEndPipeline()


def test_process_success_with_ocr_fallback(monkeypatch):
    pipeline = _pipeline()
    pipeline.cv_pipeline.process = MagicMock(return_value={"detections": [{"class_name": "crate"}], "enhanced_image": _image(), "processing_time_ms": 1})
    pipeline.ocr_pipeline.process = MagicMock(side_effect=RuntimeError("ocr failed"))
    pipeline.processor.process = MagicMock(return_value={"extraction": _extraction(), "is_valid": True, "errors": []})

    monkeypatch.setattr(pipeline.preprocessor, "load_image", lambda source: _image())

    result = pipeline.process("image.jpg", source_farm="Farm-A", destination="Depot-B")

    assert result["status"] == "success"
    assert result["ocr_results"]["texts_found"] == 0
    assert result["is_valid"] is True


def test_process_recovery_path(monkeypatch):
    pipeline = _pipeline()
    pipeline.cv_pipeline.process = MagicMock(side_effect=ValueError("cv failed"))
    pipeline.processor.process = MagicMock(return_value={"extraction": _extraction(), "is_valid": True, "errors": []})

    monkeypatch.setattr(pipeline.preprocessor, "load_image", lambda source: _image())
    monkeypatch.setattr(pipeline.error_recovery, "retry_with_preprocessing", lambda image: [_image(), _image()])
    monkeypatch.setattr("pipeline.end_to_end.extract_text", lambda image, config: {"all_texts": ["recovered"], "processing_time_ms": 1})

    result = pipeline.process("image.jpg", retry_on_failure=True)

    assert result["status"] == "recovered"
    assert result["recovery_method"] == "image_preprocessing"


def test_process_returns_error_without_retry(monkeypatch):
    pipeline = _pipeline()
    pipeline.cv_pipeline.process = MagicMock(side_effect=ValueError("cv failed"))
    monkeypatch.setattr(pipeline.preprocessor, "load_image", lambda source: _image())

    result = pipeline.process("image.jpg", retry_on_failure=False)

    assert result["status"] == "error"
    assert "cv failed" in result["error"]


def test_process_from_cv_only_error(monkeypatch):
    pipeline = _pipeline()
    pipeline.cv_pipeline.process = MagicMock(side_effect=ValueError("cv failed"))
    monkeypatch.setattr(pipeline.preprocessor, "load_image", lambda source: _image())

    result = pipeline.process_from_cv_only("image.jpg")

    assert result["status"] == "error"
    assert result["mode"] == "cv_only"


def test_batch_processor_process_batch_mixed_results():
    processor = BatchProcessor()
    processor.pipeline = MagicMock()
    processor.pipeline.process.side_effect = [
        {"status": "success", "extraction": {"products": [{"product_name": "Tomato", "quantity": 2}]}, "is_valid": True},
        {"status": "partial", "extraction": {"products": [{"product_name": "Lettuce", "quantity": 1}]}, "is_valid": False, "missing_fields": ["product_id"]},
        RuntimeError("boom"),
    ]

    result = processor.process_batch(["img-1", "img-2", "img-3"], source_farm="Farm-A", destination="Depot-B")

    assert result["total_images"] == 3
    assert result["successful"] == 1
    assert result["failed"] == 1
    assert result["success_rate"] == 1 / 3
    assert result["aggregation"]["total_products_detected"] == 2
    assert len(result["anomalies"]) == 2


def test_error_recovery_single_variant_and_convenience_functions(monkeypatch):
    image = _image()
    assert len(ErrorRecovery.retry_with_preprocessing(image, max_retries=1)) == 1
    assert len(ErrorRecovery.retry_with_preprocessing(image, max_retries=4)) == 4

    with patch("pipeline.end_to_end.EndToEndPipeline") as mock_pipeline_class:
        mock_pipeline = MagicMock()
        mock_pipeline.process.return_value = {"status": "success", "is_valid": True}
        mock_pipeline_class.return_value = mock_pipeline

        single = process_image("img.jpg", source_farm="Farm", destination="Depot")
        assert single["status"] == "success"

    with patch("pipeline.end_to_end.BatchProcessor") as mock_batch_class:
        mock_batch = MagicMock()
        mock_batch.process_batch.return_value = {"total_images": 1, "successful": 1}
        mock_batch_class.return_value = mock_batch

        batch = process_batch(["img.jpg"], source_farm="Farm", destination="Depot")
        assert batch["total_images"] == 1


def test_module_entrypoint_image_batch_and_help(monkeypatch, tmp_path):
    import models.cv_pipeline as cv_module
    import models.ocr_pipeline as ocr_module
    import utils.parser as parser_module

    class FakePreprocessor:
        def load_image(self, source):
            return _image()

    class FakeCVPipeline:
        def __init__(self, config=None):
            self.config = config or {}

        def process(self, image):
            return {"detections": [{"class_name": "crate"}], "enhanced_image": _image(), "processing_time_ms": 1}

    class FakeOCRPipeline:
        def __init__(self, config=None):
            self.config = config or {}

        def process(self, image):
            return {"all_texts": ["Tomato"], "processing_time_ms": 1, "expiry_date": None, "product_code": None, "quantity": None}

    class FakeProcessor:
        def __init__(self, config=None):
            self.config = config or {}

        def process(self, cv_result, ocr_result, source_farm=None, destination=None):
            return {"extraction": _extraction(), "is_valid": True, "errors": []}

    class FakeBatchProcessor:
        def __init__(self, config=None):
            self.config = config or {}

        def process_batch(self, image_paths, source_farm=None, destination=None):
            return {"total_images": len(image_paths), "successful": len(image_paths), "failed": 0}

    monkeypatch.setattr(cv_module, "CVPipeline", FakeCVPipeline)
    monkeypatch.setattr(cv_module, "ImagePreprocessor", FakePreprocessor)
    monkeypatch.setattr(ocr_module, "OCRPipeline", FakeOCRPipeline)
    monkeypatch.setattr(parser_module, "ExtractionProcessor", FakeProcessor)
    monkeypatch.setattr("pipeline.end_to_end.BatchProcessor", FakeBatchProcessor)
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=lambda *args, **kwargs: None))

    monkeypatch.setattr(
        argparse.ArgumentParser,
        "parse_args",
        lambda self: SimpleNamespace(image="image.jpg", batch=None, source_farm="Farm-A", destination="Depot-B"),
    )
    runpy.run_module("pipeline.end_to_end", run_name="__main__")

    monkeypatch.setattr(
        argparse.ArgumentParser,
        "parse_args",
        lambda self: SimpleNamespace(image=None, batch=str(tmp_path), source_farm="Farm-A", destination="Depot-B"),
    )
    runpy.run_module("pipeline.end_to_end", run_name="__main__")

    monkeypatch.setattr(
        argparse.ArgumentParser,
        "parse_args",
        lambda self: SimpleNamespace(image=None, batch=None, source_farm="Farm-A", destination="Depot-B"),
    )
    runpy.run_module("pipeline.end_to_end", run_name="__main__")
