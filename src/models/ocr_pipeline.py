"""
OCR Pipeline for text extraction from logistics images.

This module handles:
- Text detection and recognition (PaddleOCR)
- Expiry date extraction
- Product code/barcode reading
- Confidence filtering
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
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
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced_l = clahe.apply(l)

        # Merge and convert back
        enhanced_lab = cv2.merge((enhanced_l, a, b))
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        # Apply denoising
        denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)

        # Sharpen to improve text edges
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
        return image[max(0, y1) : min(image.shape[0], y2), max(0, x1) : min(image.shape[1], x2)]  # noqa: E203

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

    # Date patterns for extraction
    DATE_PATTERNS = [
        (r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", "%d-%m-%Y"),  # DD-MM-YYYY
        (r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", "%m-%d-%Y"),  # MM-DD-YYYY
        (r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b", "%Y-%m-%d"),  # YYYY-MM-DD
        (r"\b((?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*\s+\d{1,2},?\s+\d{4})\b", "%B %d, %Y"),
        (r"\b(BEST\s*BY|EXP|EXPIRY|USE\s*BY|BEST\s*BEFORE)?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", None),
    ]

    # Product code patterns
    PRODUCT_CODE_PATTERNS = [
        r"\b([A-Z]{2,5}-?\d{3,6})\b",  # SKU-12345
        r"\b(SKU|Sku|sku)\s*:?\s*([A-Z0-9-]+)\b",  # SKU: ABC-123
        r"\b(PROD|PRODID|PID)-?\d+\b",  # PROD-12345
    ]

    # Quantity patterns
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

        device = "gpu" if use_gpu else "cpu"
        self.ocr = PaddleOCR(use_textline_orientation=True, lang=lang, device=device)
        self.preprocessor = OCRPreprocessor()

    def extract_text(self, image: Any, enhance: bool = True) -> List[Dict[str, Any]]:
        """
        Extract text from an image.

        Args:
            image: Image source (path, array, or PIL Image)
            enhance: Whether to preprocess for better OCR

        Returns:
            List of text detections with bounding boxes and confidence
        """
        # Convert to numpy array if needed
        if isinstance(image, str):
            if image.startswith(("http://", "https://")):
                import requests

                response = requests.get(image)
                response.raise_for_status()
                image = np.array(Image.open(np.io.BytesIO(response.content)))
            else:
                image = cv2.imread(image)
        elif isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Preprocess if requested
        if enhance:
            image = self.preprocessor.enhance_for_ocr(image)

        # Run OCR
        result = self.ocr.ocr(image, cls=True)

        texts = []
        if result and result[0]:
            for line in result[0]:
                bbox, (text, confidence) = line
                texts.append(
                    {
                        "text": text.strip(),
                        "confidence": confidence,
                        "bbox": bbox,
                    }
                )

        return texts

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
        """
        Parse expiry date from extracted text.

        Args:
            texts: List of extracted text detections

        Returns:
            Parsed expiry date info or None
        """
        full_text = " ".join([t["text"] for t in texts])

        for pattern, date_format in self.DATE_PATTERNS:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                try:
                    # Try to parse the date
                    parsed = datetime.strptime(date_str, date_format) if date_format else None
                    if parsed and parsed > datetime.now():
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
        full_text = " ".join([t["text"] for t in texts])

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
        full_text = " ".join([t["text"] for t in texts])

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
        self.extractor = TextExtractor(lang=self.config.get("language", "en"), use_gpu=self.config.get("use_gpu", False))
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

        # Load image
        if isinstance(image, str):
            if image.startswith(("http://", "https://")):
                import requests

                response = requests.get(image)
                response.raise_for_status()
                image = np.array(Image.open(np.io.BytesIO(response.content)))
            else:
                image = cv2.imread(image)
        elif isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Extract all text
        all_texts = self.extractor.extract_text(image, enhance=True)

        # Filter by confidence
        confidence_threshold = self.config.get("confidence_threshold", 0.7)
        high_confidence_texts = [t for t in all_texts if t["confidence"] >= confidence_threshold]

        # Parse specific fields
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
        return {
            "texts": roi_texts,
            "bbox": bbox,
        }


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
