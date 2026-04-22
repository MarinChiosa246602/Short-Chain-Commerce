"""
OCR Pipeline for text extraction from logistics images.

This module handles:
- Text detection and recognition (PaddleOCR)
- Expiry date extraction
- Product code/barcode reading
- Confidence filtering
"""

from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

try:
    from paddleocr import PaddleOCR

    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False


class OCRPreprocessor:
    """Preprocess images for optimal OCR performance."""

    @staticmethod
    def enhance_for_ocr(image: np.ndarray) -> np.ndarray:
        """
        Enhance image specifically for OCR.

        Args:
            image: Input BGR image

        Returns:
            Enhanced image optimized for text recognition
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced_l = clahe.apply(l)

        enhanced_lab = cv2.merge((enhanced_l, a, b))
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)

        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)

        return sharpened

    @staticmethod
    def extract_roi(image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Extract a region of interest from an image.

        Args:
            image: Source image
            bbox: (x1, y1, x2, y2) bounding box

        Returns:
            Cropped ROI image
        """
        x1, y1, x2, y2 = bbox
        return image[max(0, y1):min(image.shape[0], y2), max(0, x1):min(image.shape[1], x2)]

    @staticmethod
    def rotate_for_ocr(image: np.ndarray, angle: float = 0) -> np.ndarray:
        """
        Rotate image to improve text alignment.

        Args:
            image: Input image
            angle: Rotation angle in degrees

        Returns:
            Rotated image
        """
        if angle == 0:
            return image

        h, w = image.shape[:2]
        center = (w / 2, h / 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)


class TextExtractor:
    """Extract and parse text from images using OCR."""

    DATE_PATTERNS = [
        r"(?:EXP(?:IRY)?|BEST\s*(?:BEFORE|BY)?|USE\s*BY|BB)[:\s.]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"(?:EXP(?:IRY)?|BEST\s*(?:BEFORE|BY)?|USE\s*BY|BB)[:\s.]*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b",
        r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
    ]

    DATE_FORMATS = [
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
    ]

    PRODUCT_CODE_PATTERNS = [
        r"\b([A-Z]{2,5}-?\d{3,6})\b",
        r"\b(SKU|Sku|sku)\s*:?\s*([A-Z0-9-]+)\b",
        r"\b(PROD|PRODID|PID)-?\d+\b",
    ]

    QUANTITY_PATTERNS = [
        r"\b(\d+)\s*(?:pcs?|pieces?|units?|items?)\b",
        r"\b(\d+)\s*(?:kg|lbs?|g|oz|lb)\b",
        r"\bqty[:\s]+(\d+)\b",
    ]

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        """
        Initialize the text extractor.

        Args:
            lang: Language for OCR (default: English)
            use_gpu: Whether to use GPU acceleration
        """
        if not PADDLEOCR_AVAILABLE:
            raise ImportError("paddleocr package is required. Install with: pip install paddleocr paddlepaddle")

        # PaddleOCR argument names vary between versions.
        try:
            self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=use_gpu)
        except (TypeError, ValueError):
            kwargs: Dict[str, Any] = {"use_angle_cls": True, "lang": lang}
            if use_gpu:
                kwargs["device"] = "gpu"
            self.ocr = PaddleOCR(**kwargs)
        self.preprocessor = OCRPreprocessor()

    def _normalize_ocr_result(self, raw_result: Any) -> List[Dict[str, Any]]:
        """Normalize PaddleOCR output into a common list-of-dicts shape."""
        texts: List[Dict[str, Any]] = []

        # Most common PaddleOCR result shape from `ocr`:
        # [[ [bbox], (text, confidence) ], ...]
        if isinstance(raw_result, list) and raw_result:
            first = raw_result[0]
            if isinstance(first, list):
                for line in first:
                    if isinstance(line, (list, tuple)) and len(line) >= 2:
                        bbox = line[0]
                        payload = line[1]
                        if isinstance(payload, (list, tuple)) and len(payload) >= 2:
                            text, confidence = payload[0], float(payload[1])
                            texts.append({"text": str(text).strip(), "confidence": confidence, "bbox": bbox})
                if texts:
                    return texts

        # Some versions return dict-like records from `predict`.
        if isinstance(raw_result, list):
            for item in raw_result:
                if isinstance(item, dict):
                    text = item.get("rec_text") or item.get("text")
                    confidence = item.get("rec_score") or item.get("confidence")
                    bbox = item.get("dt_polys") or item.get("bbox")
                    if text is not None and confidence is not None:
                        texts.append(
                            {
                                "text": str(text).strip(),
                                "confidence": float(confidence),
                                "bbox": bbox,
                            }
                        )

        return texts

    def extract_text(self, image: Any, enhance: bool = True) -> List[Dict[str, Any]]:
        """
        Extract text from an image.

        Args:
            image: Image source (path, array, or PIL Image)
            enhance: Whether to preprocess for better OCR

        Returns:
            List of text detections with bounding boxes and confidence
        """
        if isinstance(image, str):
            if image.startswith(("http://", "https://")):
                import requests

                response = requests.get(image)
                response.raise_for_status()
                image = np.array(Image.open(io.BytesIO(response.content)))
            else:
                image = cv2.imread(image)
        elif isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        if image is None:
            return []

        if enhance:
            image = self.preprocessor.enhance_for_ocr(image)

        if hasattr(self.ocr, "ocr"):
            try:
                raw_result = self.ocr.ocr(image, cls=True)
            except TypeError:
                raw_result = self.ocr.ocr(image)
        else:
            raw_result = self.ocr.predict(image)

        return self._normalize_ocr_result(raw_result)

    def extract_from_roi(
        self, image: np.ndarray, bbox: Tuple[int, int, int, int], enhance: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract text from a specific region of interest.

        Args:
            image: Source image
            bbox: ROI bounding box (x1, y1, x2, y2)
            enhance: Whether to preprocess

        Returns:
            List of text detections in the ROI
        """
        roi = self.preprocessor.extract_roi(image, bbox)
        return self.extract_text(roi, enhance=enhance)

    def parse_expiry_date(self, texts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract and normalize an expiry date from OCR text list."""
        full_text = " ".join([t.get("text", "") for t in texts])
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                date_str = match.group(1).replace("/", "-")
                for fmt in self.DATE_FORMATS:
                    try:
                        parsed = datetime.strptime(date_str, fmt)
                        if parsed > datetime.now():
                            return {
                                "raw": date_str,
                                "parsed": parsed.strftime("%Y-%m-%d"),
                                "confidence": "high",
                            }
                    except ValueError:
                        continue
        return None

    def parse_product_code(self, texts: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract product code/SKU from text.

        Args:
            texts: List of extracted text detections

        Returns:
            Product code or None
        """
        full_text = " ".join([t.get("text", "") for t in texts])

        for pattern in self.PRODUCT_CODE_PATTERNS:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def parse_quantity(self, texts: List[Dict[str, Any]]) -> Optional[int]:
        """
        Extract quantity from text.

        Args:
            texts: List of extracted text detections

        Returns:
            Quantity or None
        """
        full_text = " ".join([t.get("text", "") for t in texts])

        for pattern in self.QUANTITY_PATTERNS:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None


class OCRPipeline:
    """
    Main OCR Pipeline.

    Chains together text extraction and parsing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the OCR pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or {}
        self.extractor = TextExtractor(
            lang=self.config.get("language", "en"),
            use_gpu=self.config.get("use_gpu", False),
        )
        self.preprocessor = OCRPreprocessor()

    def process(self, image: Any, detect_regions: bool = True) -> Dict[str, Any]:
        """
        Run full OCR pipeline on an image.

        Args:
            image: Image to process
            detect_regions: Whether to detect text regions automatically

        Returns:
            Dictionary with extracted text and parsed fields
        """
        import time

        start_time = time.time()

        if isinstance(image, str):
            if image.startswith(("http://", "https://")):
                import requests

                response = requests.get(image)
                response.raise_for_status()
                image = np.array(Image.open(io.BytesIO(response.content)))
            else:
                image = cv2.imread(image)
        elif isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        all_texts = self.extractor.extract_text(image, enhance=True)

        confidence_threshold = self.config.get("confidence_threshold", 0.7)
        high_confidence_texts = [t for t in all_texts if t["confidence"] >= confidence_threshold]

        expiry_date = self.extractor.parse_expiry_date(all_texts)
        product_code = self.extractor.parse_product_code(all_texts)
        quantity = self.extractor.parse_quantity(all_texts)

        processing_time = (time.time() - start_time) * 1000

        return {
            "all_texts": all_texts,
            "high_confidence_texts": high_confidence_texts,
            "expiry_date": expiry_date,
            "product_code": product_code,
            "quantity": quantity,
            "processing_time_ms": processing_time,
        }

    def process_roi(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """
        Process a specific region of interest.

        Args:
            image: Source image
            bbox: ROI bounding box

        Returns:
            Extracted text for the ROI
        """
        roi_texts = self.extractor.extract_from_roi(image, bbox)
        return {"texts": roi_texts, "bbox": bbox}


# Convenience function
def extract_text(image: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Quick function to extract text from an image.

    Args:
        image: Image source
        config: Optional configuration

    Returns:
        Extraction results
    """
    pipeline = OCRPipeline(config)
    return pipeline.process(image)
