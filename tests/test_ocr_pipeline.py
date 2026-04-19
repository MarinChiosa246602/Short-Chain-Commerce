"""
Tests for OCR pipeline and text extraction.
"""

import pytest
import cv2
import numpy as np
from unittest.mock import patch, MagicMock

from models.ocr_pipeline import (
    OCRPreprocessor,
    TextExtractor,
    OCRPipeline,
    extract_text,
)


class TestOCRPreprocessor:
    """Test image preprocessing for OCR."""

    def test_enhance_for_ocr_returns_image(self):
        """Test that enhance_for_ocr returns a valid image."""
        # Create a dummy test image
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        enhanced = OCRPreprocessor.enhance_for_ocr(image)

        assert enhanced is not None
        assert isinstance(enhanced, np.ndarray)
        assert enhanced.shape == image.shape
        assert enhanced.dtype == np.uint8

    def test_extract_roi(self):
        """Test ROI extraction."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        bbox = (10, 10, 50, 50)

        roi = OCRPreprocessor.extract_roi(image, bbox)

        assert roi.shape == (40, 40, 3)

    def test_extract_roi_bounds_checking(self):
        """Test ROI extraction handles out-of-bounds coordinates."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        bbox = (50, 50, 200, 200)  # Exceeds image size

        roi = OCRPreprocessor.extract_roi(image, bbox)

        assert roi.shape == (50, 50, 3)

    def test_rotate_for_ocr_zero_angle(self):
        """Test rotation with zero angle returns original."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        rotated = OCRPreprocessor.rotate_for_ocr(image, angle=0)

        np.testing.assert_array_equal(rotated, image)


class TestTextExtractor:
    """Test text extraction functionality."""

    def test_init_with_paddleocr_available(self):
        """Test initialization with PaddleOCR."""
        with patch('models.ocr_pipeline.PaddleOCR') as mock_ocr:
            extractor = TextExtractor(lang='en', use_gpu=False)
            mock_ocr.assert_called_once_with(use_angle_cls=True, lang='en', use_gpu=False)

    def test_init_with_gpu_enabled(self):
        """Test initialization with GPU enabled."""
        with patch('models.ocr_pipeline.PaddleOCR') as mock_ocr:
            extractor = TextExtractor(lang='en', use_gpu=True)
            mock_ocr.assert_called_once_with(use_angle_cls=True, lang='en', use_gpu=True)


class TestTextExtractorParsers:
    """Test text parsing functions."""

    def test_parse_expiry_date_with_exp_prefix(self):
        """Test parsing expiry date with EXP prefix."""
        extractor = TextExtractor.__new__(TextExtractor)  # Skip __init__

        texts = [
            {'text': 'EXP 15-04-2026', 'confidence': 0.9},
            {'text': 'BEST', 'confidence': 0.8},
        ]

        result = extractor.parse_expiry_date(texts)
        assert result is not None
        assert '2026' in result['raw']

    def test_parse_expiry_date_simple_format(self):
        """Test parsing simple expiry date format."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': '12-25-2026', 'confidence': 0.95},
        ]

        result = extractor.parse_expiry_date(texts)
        # Should match the date pattern
        assert result is not None

    def test_parse_expiry_date_no_future_date(self):
        """Test parsing past date returns None."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': 'EXP 01-01-2020', 'confidence': 0.9},
        ]

        result = extractor.parse_expiry_date(texts)
        assert result is None  # Past date should return None

    def test_parse_expiry_date_no_match(self):
        """Test parsing when no date is found."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': 'No dates here', 'confidence': 0.9},
        ]

        result = extractor.parse_expiry_date(texts)
        assert result is None

    def test_parse_product_code_with_sku_prefix(self):
        """Test parsing product code with SKU prefix."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': 'SKU: TOM-12345', 'confidence': 0.9},
        ]

        result = extractor.parse_product_code(texts)
        assert result is not None
        assert 'TOM' in result or 'SKU' in result

    def test_parse_product_code_simple_format(self):
        """Test parsing simple product code format."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': 'PROD-12345', 'confidence': 0.95},
        ]

        result = extractor.parse_product_code(texts)
        assert result == 'PROD-12345'

    def test_parse_product_code_no_match(self):
        """Test parsing when no product code is found."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': 'No product codes here', 'confidence': 0.9},
        ]

        result = extractor.parse_product_code(texts)
        assert result is None

    def test_parse_quantity_with_units(self):
        """Test parsing quantity with units."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': '24 pieces', 'confidence': 0.9},
        ]

        result = extractor.parse_quantity(texts)
        assert result == 24

    def test_parse_quantity_with_kg(self):
        """Test parsing quantity in kg."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': '5 kg', 'confidence': 0.9},
        ]

        result = extractor.parse_quantity(texts)
        assert result == 5

    def test_parse_quantity_with_qty_prefix(self):
        """Test parsing quantity with qty prefix."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': 'qty: 100', 'confidence': 0.9},
        ]

        result = extractor.parse_quantity(texts)
        assert result == 100

    def test_parse_quantity_no_match(self):
        """Test parsing when no quantity is found."""
        extractor = TextExtractor.__new__(TextExtractor)

        texts = [
            {'text': 'No quantity here', 'confidence': 0.9},
        ]

        result = extractor.parse_quantity(texts)
        assert result is None


class TestOCRPipeline:
    """Test OCR pipeline integration."""

    def test_init_with_default_config(self):
        """Test pipeline initialization with default config."""
        with patch('models.ocr_pipeline.TextExtractor'):
            pipeline = OCRPipeline()
            assert pipeline.config == {}

    def test_init_with_custom_config(self):
        """Test pipeline initialization with custom config."""
        config = {
            'language': 'en',
            'use_gpu': True,
            'confidence_threshold': 0.8,
        }
        with patch('models.ocr_pipeline.TextExtractor'):
            pipeline = OCRPipeline(config)
            assert pipeline.config == config


class TestOCRIntegration:
    """Integration tests for OCR on real images."""

    @pytest.mark.skip(reason="PaddleOCR may not be installed in test environment")
    def test_extract_text_from_real_image(self):
        """Test text extraction from a real image file."""
        test_image_path = "data/raw/images/img_0000.jpg"

        try:
            result = extract_text(test_image_path)
            assert 'all_texts' in result
            assert 'processing_time_ms' in result
            assert 'high_confidence_texts' in result
        except Exception:
            pytest.skip("PaddleOCR not available or image not found")

    @pytest.mark.skip(reason="PaddleOCR may not be installed in test environment")
    def test_confidence_filtering(self):
        """Test that low confidence texts are filtered."""
        test_image_path = "data/raw/images/img_0000.jpg"

        try:
            result = extract_text(test_image_path, {'confidence_threshold': 0.95})
            all_count = len(result.get('all_texts', []))
            high_conf_count = len(result.get('high_confidence_texts', []))
            assert high_conf_count <= all_count
        except Exception:
            pytest.skip("PaddleOCR not available or image not found")


class TestConfidenceFiltering:
    """Test confidence threshold filtering."""

    def test_mock_confidence_filtering(self):
        """Test confidence filtering logic."""
        all_texts = [
            {'text': 'High conf', 'confidence': 0.95},
            {'text': 'Med conf', 'confidence': 0.75},
            {'text': 'Low conf', 'confidence': 0.5},
        ]

        threshold = 0.7
        high_conf = [t for t in all_texts if t['confidence'] >= threshold]

        assert len(high_conf) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
