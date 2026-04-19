"""
End-to-End Pipeline for logistics data extraction.

This module orchestrates the full pipeline:
- Image loading and preprocessing
- Computer Vision (YOLOv8) object detection
- OCR text extraction
- Data parsing and validation
- Error recovery and batch processing
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import cv2
import numpy as np

from models.cv_pipeline import CVPipeline, ImagePreprocessor
from models.ocr_pipeline import OCRPipeline
from utils.parser import ExtractionProcessor


class ErrorRecovery:
    """Handles error recovery and anomaly logging for the pipeline."""

    @staticmethod
    def retry_with_preprocessing(image: np.ndarray, max_retries: int = 3) -> List[np.ndarray]:
        """
        Retry failed OCR with different preprocessing variants.

        Args:
            image: Original image as numpy array
            max_retries: Maximum number of variants to generate

        Returns:
            List of preprocessed image variants (always includes the original)
        """
        variants = [image]

        # Variant 1: High contrast via CLAHE on LAB L-channel
        if len(variants) < max_retries:
            try:
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(16, 16))
                enhanced_l = clahe.apply(l)
                enhanced_lab = cv2.merge((enhanced_l, a, b))
                high_contrast = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
                variants.append(high_contrast)
            except Exception:
                # Fallback: simple histogram equalisation on grayscale
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                eq = cv2.equalizeHist(gray)
                variants.append(cv2.cvtColor(eq, cv2.COLOR_GRAY2BGR))

        # Variant 2: Denoised + sharpened
        if len(variants) < max_retries:
            try:
                denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
                kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                sharpened = cv2.filter2D(denoised, -1, kernel)
                variants.append(sharpened)
            except Exception:
                variants.append(image.copy())

        # Variant 3: Grayscale → back to BGR (strips colour noise)
        if len(variants) < max_retries:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            variants.append(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))

        return variants[:max_retries]

    @staticmethod
    def log_anomaly(
        extraction_id: str,
        error_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log an anomaly detected during extraction.

        Args:
            extraction_id: Unique ID for the extraction run
            error_type: Short error type code
            details: Additional context about the error

        Returns:
            Anomaly record dictionary
        """
        record = {
            "extraction_id": extraction_id,
            "error_type": error_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        return record


class EndToEndPipeline:
    """
    Orchestrates the full extraction pipeline.

    CV detection → OCR → parsing & validation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise all pipeline components.

        Args:
            config: Optional configuration dict shared across components
        """
        self.config = config or {}
        self.preprocessor = ImagePreprocessor()
        self.cv_pipeline = CVPipeline(self.config)
        self.ocr_pipeline = OCRPipeline(self.config)
        self.extraction_processor = ExtractionProcessor(self.config)

    def process(
        self,
        image_source: Any,
        source_farm: Optional[str] = None,
        destination: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the full end-to-end pipeline on a single image.

        Args:
            image_source: File path, URL, PIL Image, or numpy array
            source_farm: Origin farm identifier for metadata
            destination: Destination identifier for metadata

        Returns:
            Dictionary with extraction_id, extraction result, validation
            status, and processing_time_ms
        """
        pipeline_start = time.time()
        extraction_id = str(uuid4())

        try:
            # Load image
            image = self.preprocessor.load_image(image_source)

            # --- CV stage ---
            cv_result = self.cv_pipeline.process(image_source)

            # --- OCR stage ---
            enhanced = cv_result.get("enhanced_image", image)
            if enhanced is None:
                enhanced = image

            try:
                ocr_result = self.ocr_pipeline.process(enhanced)
            except Exception as ocr_err:
                # OCR failure is non-fatal; continue with empty result
                ocr_result = {
                    "all_texts": [],
                    "high_confidence_texts": [],
                    "expiry_date": None,
                    "product_code": None,
                    "quantity": None,
                    "processing_time_ms": 0,
                    "error": str(ocr_err),
                }

            # --- Parsing & validation stage ---
            parsed = self.extraction_processor.process(
                cv_result=cv_result,
                ocr_result=ocr_result,
                source_farm=source_farm,
                destination=destination,
            )

            total_ms = (time.time() - pipeline_start) * 1000

            return {
                "extraction_id": extraction_id,
                "status": "success",
                "extraction": parsed["extraction"],
                "is_valid": parsed["is_valid"],
                "errors": parsed["errors"],
                "cv_processing_time_ms": cv_result.get("processing_time_ms", 0),
                "ocr_processing_time_ms": ocr_result.get("processing_time_ms", 0),
                "processing_time_ms": total_ms,
            }

        except Exception as exc:
            total_ms = (time.time() - pipeline_start) * 1000
            anomaly = ErrorRecovery.log_anomaly(
                extraction_id=extraction_id,
                error_type="PIPELINE_ERROR",
                details={"error": str(exc)},
            )
            return {
                "extraction_id": extraction_id,
                "status": "error",
                "error": str(exc),
                "anomaly": anomaly,
                "processing_time_ms": total_ms,
            }

    def process_from_cv_only(self, image_source: Any) -> Dict[str, Any]:
        """
        Run pipeline using only the CV stage (no OCR).

        Useful when images contain no readable text labels.

        Args:
            image_source: Image to process

        Returns:
            Result dict with mode='cv_only'
        """
        extraction_id = str(uuid4())
        start = time.time()

        try:
            image = self.preprocessor.load_image(image_source)
            cv_result = self.cv_pipeline.process(image_source)

            # Parse with empty OCR result
            parsed = self.extraction_processor.process(
                cv_result=cv_result,
                ocr_result={},
            )

            return {
                "extraction_id": extraction_id,
                "mode": "cv_only",
                "status": "success",
                "extraction": parsed["extraction"],
                "is_valid": parsed["is_valid"],
                "errors": parsed["errors"],
                "processing_time_ms": (time.time() - start) * 1000,
            }

        except Exception as exc:
            return {
                "extraction_id": extraction_id,
                "mode": "cv_only",
                "status": "error",
                "error": str(exc),
                "processing_time_ms": (time.time() - start) * 1000,
            }


class BatchProcessor:
    """
    Process multiple images in batch.

    Wraps EndToEndPipeline for bulk operations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise batch processor.

        Args:
            config: Optional configuration passed to the pipeline
        """
        self.config = config or {}
        self.pipeline = EndToEndPipeline(self.config)

    def process_batch(
        self,
        image_sources: List[Any],
        source_farm: Optional[str] = None,
        destination: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a list of images.

        Args:
            image_sources: List of image paths / arrays
            source_farm: Origin farm identifier
            destination: Destination identifier

        Returns:
            Aggregated batch result
        """
        if not image_sources:
            return {
                "total_images": 0,
                "successful": 0,
                "failed": 0,
                "results": [],
                "aggregation": self._aggregate_results([]),
            }

        results = []
        successful = 0
        failed = 0

        for source in image_sources:
            result = self.pipeline.process(
                source,
                source_farm=source_farm,
                destination=destination,
            )
            results.append(result)
            if result.get("status") == "success":
                successful += 1
            else:
                failed += 1

        return {
            "total_images": len(image_sources),
            "successful": successful,
            "failed": failed,
            "results": results,
            "aggregation": self._aggregate_results(results),
        }

    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate statistics across batch results.

        Args:
            results: List of individual pipeline results

        Returns:
            Aggregation statistics dictionary
        """
        total_products = 0
        total_quantity = 0
        product_types: Dict[str, int] = {}
        earliest_expiry = None

        for result in results:
            extraction = result.get("extraction")

            # extraction can be an ExtractionResponse object or a plain dict
            if extraction is None:
                continue

            # Support both Pydantic model and raw dict
            if hasattr(extraction, "products"):
                products = extraction.products
            elif isinstance(extraction, dict):
                products = extraction.get("products", [])
            else:
                continue

            for product in products:
                total_products += 1

                # Quantity
                qty = getattr(product, "quantity", None) if hasattr(product, "quantity") else product.get("quantity", 0)
                total_quantity += qty or 0

                # Product type counts
                name = (
                    getattr(product, "product_name", None)
                    if hasattr(product, "product_name")
                    else product.get("product_name")
                )
                if name:
                    product_types[name] = product_types.get(name, 0) + 1

                # Earliest expiry
                expiry = (
                    getattr(product, "expiry_date", None)
                    if hasattr(product, "expiry_date")
                    else product.get("expiry_date")
                )
                if expiry:
                    if earliest_expiry is None or expiry < earliest_expiry:
                        earliest_expiry = expiry

        return {
            "total_products_detected": total_products,
            "total_quantity": total_quantity,
            "product_types": product_types,
            "earliest_expiry": earliest_expiry.isoformat() if isinstance(earliest_expiry, datetime) else earliest_expiry,
        }


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def process_image(
    image_source: Any,
    source_farm: Optional[str] = None,
    destination: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Quick single-image processing helper.

    Args:
        image_source: Image path, URL, PIL Image, or numpy array
        source_farm: Origin farm identifier
        destination: Destination identifier
        config: Optional pipeline configuration

    Returns:
        Pipeline result dictionary
    """
    pipeline = EndToEndPipeline(config)
    return pipeline.process(image_source, source_farm=source_farm, destination=destination)


def process_batch(
    image_sources: List[Any],
    source_farm: Optional[str] = None,
    destination: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Quick batch processing helper.

    Args:
        image_sources: List of image paths / arrays
        source_farm: Origin farm identifier
        destination: Destination identifier
        config: Optional pipeline configuration

    Returns:
        Aggregated batch result dictionary
    """
    processor = BatchProcessor(config)
    return processor.process_batch(image_sources, source_farm=source_farm, destination=destination)