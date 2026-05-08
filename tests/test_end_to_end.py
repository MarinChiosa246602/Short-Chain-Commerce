"""
Tests for end-to-end pipeline.
"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from datetime import datetime, timedelta

from src.pipeline.end_to_end import (
    EndToEndPipeline,
    BatchProcessor,
    ErrorRecovery,
    process_image,
    process_batch,
)


class TestErrorRecovery:
    """Test error recovery mechanisms."""

    def test_retry_with_preprocessing_returns_variants(self):
        """Test that preprocessing generates image variants."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        variants = ErrorRecovery.retry_with_preprocessing(image, max_retries=3)

        assert len(variants) >= 2
        assert all(isinstance(v, np.ndarray) for v in variants)
        assert all(v.shape == image.shape for v in variants)

    def test_log_anomaly_creates_record(self):
        """Test anomaly logging creates proper record."""
        result = ErrorRecovery.log_anomaly(
            extraction_id="test-123",
            error_type="TEST_ERROR",
            details={"field": "test", "value": "value"}
        )

        assert result["extraction_id"] == "test-123"
        assert result["error_type"] == "TEST_ERROR"
        assert "timestamp" in result


class TestBatchProcessor:
    """Test batch processing functionality."""

    def test_init_creates_pipeline(self):
        """Test batch processor initialization."""
        with patch('src.pipeline.end_to_end.EndToEndPipeline'):
            processor = BatchProcessor({"test": "config"})
            assert processor.config == {"test": "config"}

    def test_aggregate_results_calculates_stats(self):
        """Test result aggregation statistics."""
        processor = BatchProcessor()

        results = [
            {
                "extraction": {
                    "products": [
                        {"product_name": "Tomato", "quantity": 10, "expiry_date": datetime(2026, 12, 1)},
                        {"product_name": "Lettuce", "quantity": 5, "expiry_date": datetime(2026, 11, 1)},
                    ]
                }
            },
            {
                "extraction": {
                    "products": [
                        {"product_name": "Tomato", "quantity": 20, "expiry_date": datetime(2026, 12, 15)},
                    ]
                }
            },
        ]

        aggregation = processor._aggregate_results(results)

        assert aggregation["total_products_detected"] == 3
        assert aggregation["total_quantity"] == 35
        assert aggregation["product_types"]["Tomato"] == 2
        assert aggregation["product_types"]["Lettuce"] == 1


class TestEndToEndPipeline:
    """Test end-to-end pipeline integration."""

    def test_init_creates_components(self):
        """Test pipeline initialization creates all components."""
        with patch('src.pipeline.end_to_end.CVPipeline'), \
             patch('src.pipeline.end_to_end.OCRPipeline'), \
             patch('src.pipeline.end_to_end.ExtractionProcessor'):
            pipeline = EndToEndPipeline({"test": "config"})
            assert pipeline.config == {"test": "config"}

    def test_process_from_cv_only_mode(self):
        """Test processing with CV-only mode."""
        with patch('pipeline.end_to_end.CVPipeline') as mock_cv:
            mock_cv.return_value.process.return_value = {
                "detections": [{"class_name": "crate", "confidence": 0.9}],
                "enhanced_image": None,
                "processing_time_ms": 100,
            }

            pipeline = EndToEndPipeline()

            with patch.object(pipeline, 'preprocessor') as mock_pre:
                mock_pre.load_image.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

                result = pipeline.process_from_cv_only("dummy_image.jpg")

                assert result["mode"] == "cv_only"
                assert result["status"] in ["success", "error"]


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch('src.pipeline.end_to_end.EndToEndPipeline')
    def test_process_image(self, mock_pipeline_class):
        """Test process_image convenience function."""
        mock_pipeline = MagicMock()
        mock_pipeline.process.return_value = {"status": "success", "is_valid": True}
        mock_pipeline_class.return_value = mock_pipeline

        result = process_image("image.jpg", source_farm="Farm-A", destination="Dest-B")

        assert result["status"] == "success"
        mock_pipeline.process.assert_called_once()

    @patch('src.pipeline.end_to_end.BatchProcessor')
    def test_process_batch(self, mock_processor_class):
        """Test process_batch convenience function."""
        mock_processor = MagicMock()
        mock_processor.process_batch.return_value = {"total_images": 5, "successful": 5}
        mock_processor_class.return_value = mock_processor

        result = process_batch(["img1.jpg", "img2.jpg"], source_farm="Farm-A")

        assert result["total_images"] == 5
        mock_processor.process_batch.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios with mocked components."""

    def test_full_pipeline_with_mocked_components(self):
        """Test full pipeline with all components mocked."""
        with patch('src.pipeline.end_to_end.CVPipeline') as mock_cv, \
             patch('src.pipeline.end_to_end.OCRPipeline') as mock_ocr, \
             patch('src.pipeline.end_to_end.ExtractionProcessor') as mock_parser:

            # Setup CV mock
            mock_cv.return_value.process.return_value = {
                "detections": [{"class_name": "crate", "confidence": 0.85}],
                "enhanced_image": np.zeros((100, 100, 3), dtype=np.uint8),
                "processing_time_ms": 150,
            }

            # Setup OCR mock
            mock_ocr_instance = MagicMock()
            mock_ocr.return_value = mock_ocr_instance

            # Setup parser mock
            mock_parser_instance = MagicMock()
            mock_parser_instance.process.return_value = {
                "extraction": MagicMock(),
                "is_valid": True,
                "errors": [],
            }
            mock_parser.return_value = mock_parser_instance

            pipeline = EndToEndPipeline()

            with patch.object(pipeline, 'preprocessor') as mock_pre:
                mock_pre.load_image.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

                result = pipeline.process("test.jpg", source_farm="Farm", destination="Dest")

                assert "extraction_id" in result
                assert "processing_time_ms" in result


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_image_list_batch(self):
        """Test batch processing with empty image list."""
        processor = BatchProcessor()

        with patch.object(processor, 'pipeline'):
            result = processor.process_batch([])

            assert result["total_images"] == 0
            assert result["successful"] == 0
            assert result["failed"] == 0

    def test_partial_failure_in_batch(self):
        """Test batch processing with partial failures."""
        processor = BatchProcessor()

        # Mock results with mixed success/failure
        results = [
            {"status": "success", "extraction": {"products": []}, "is_valid": True},
            {"status": "error", "error": "Test error"},
            {"status": "success", "extraction": {"products": []}, "is_valid": True},
        ]

        aggregation = processor._aggregate_results(results)
        assert aggregation["total_products_detected"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
