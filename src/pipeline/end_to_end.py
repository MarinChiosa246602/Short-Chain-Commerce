"""
End-to-End Pipeline for logistics data extraction.

This module chains together all components:
- Image loading and preprocessing
- Object detection (CV)
- Text extraction (OCR)
- Data parsing and validation
- Error recovery and batch processing
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import cv2
import numpy as np

# Ensure sibling packages under src are importable when this file is run directly.
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from models.cv_pipeline import CVPipeline, ImagePreprocessor  # noqa: E402
from models.ocr_pipeline import OCRPipeline, extract_text  # noqa: E402
from utils.parser import ExtractionProcessor  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorRecovery:
    """Handle error recovery and retry strategies."""

    @staticmethod
    def retry_with_preprocessing(image: np.ndarray, max_retries: int = 3) -> List[np.ndarray]:
        """
        Retry failed OCR with different preprocessing.

        Args:
            image: Original image
            max_retries: Maximum retry attempts

        Returns:
            List of preprocessed image variants
        """
        variants = [image]

        # Generate preprocessing variants
        if len(variants) < max_retries:
            # High contrast
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(16, 16))
            enhanced = clahe.apply(l)
            enhanced_lab = cv2.merge((enhanced, a, b))
            variants.append(cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR))

        if len(variants) < max_retries:
            # Denoised
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 15, 15, 7, 21)
            variants.append(denoised)

        if len(variants) < max_retries:
            # Sharpened
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(image, -1, kernel)
            variants.append(sharpened)

        return variants

    @staticmethod
    def log_anomaly(extraction_id: str, error_type: str, details: Dict[str, Any]):
        """
        Log an anomaly for monitoring.

        Args:
            extraction_id: Unique extraction identifier
            error_type: Type of error
            details: Error details
        """
        anomaly = {
            "extraction_id": extraction_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "details": details,
        }
        logger.warning(f"ANOMALY [{error_type}]: {details}")
        return anomaly


class BatchProcessor:
    """
    Batch processing for multiple images.

    Handles:
    - Parallel processing
    - Aggregation of results
    - Progress tracking
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize batch processor.

        Args:
            config: Batch processing configuration
        """
        self.config = config or {}
        self.pipeline = EndToEndPipeline(config)

    def process_batch(
        self,
        image_paths: List[str],
        source_farm: str = None,
        destination: str = None,
        aggregate: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a batch of images.

        Args:
            image_paths: List of image file paths
            source_farm: Source farm identifier
            destination: Destination identifier
            aggregate: Whether to aggregate results

        Returns:
            Batch results with optional aggregation
        """
        start_time = time.time()

        results = []
        successful = 0
        failed = 0
        anomalies = []

        for i, path in enumerate(image_paths):
            try:
                result = self.pipeline.process(
                    image_source=path,
                    source_farm=source_farm,
                    destination=destination,
                )
                result["image_path"] = path
                result["batch_index"] = i

                if result.get("is_valid"):
                    successful += 1
                else:
                    # Partial success
                    if result.get("missing_fields"):
                        anomalies.append(
                            {
                                "image_path": path,
                                "type": "missing_fields",
                                "fields": result["missing_fields"],
                            }
                        )

                results.append(result)

            except Exception as e:
                failed += 1
                error_result = {
                    "image_path": path,
                    "batch_index": i,
                    "status": "error",
                    "error": str(e),
                }
                results.append(error_result)

                anomalies.append(
                    {
                        "image_path": path,
                        "type": "processing_error",
                        "error": str(e),
                    }
                )

        processing_time = (time.time() - start_time) * 1000

        batch_result = {
            "total_images": len(image_paths),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(image_paths) if image_paths else 0,
            "processing_time_ms": processing_time,
            "avg_time_per_image_ms": processing_time / len(image_paths) if image_paths else 0,
            "results": results,
        }

        if aggregate:
            batch_result["aggregation"] = self._aggregate_results(results)

        if anomalies:
            batch_result["anomalies"] = anomalies

        return batch_result

    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate batch results.

        Args:
            results: List of extraction results

        Returns:
            Aggregated statistics
        """
        total_products = 0
        total_quantity = 0
        product_types = {}
        expiry_dates = []

        for result in results:
            extraction = result.get("extraction")
            if extraction:
                for product in extraction.get("products", []):
                    total_products += 1
                    total_quantity += product.get("quantity", 1)

                    # Count product types
                    ptype = product.get("product_name", "Unknown")
                    product_types[ptype] = product_types.get(ptype, 0) + 1

                    # Collect expiry dates
                    if product.get("expiry_date"):
                        expiry_dates.append(product["expiry_date"])

        return {
            "total_products_detected": total_products,
            "total_quantity": total_quantity,
            "product_types": product_types,
            "earliest_expiry": min(expiry_dates).isoformat() if expiry_dates else None,
            "latest_expiry": max(expiry_dates).isoformat() if expiry_dates else None,
        }


class EndToEndPipeline:
    """
    Main end-to-end pipeline.

    Chains: Image -> Detection -> OCR -> Parsing -> Validation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the end-to-end pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or {}

        # Initialize components
        self.cv_pipeline = CVPipeline(config)
        self.ocr_pipeline = OCRPipeline(config)
        self.processor = ExtractionProcessor(config)
        self.error_recovery = ErrorRecovery()

        # Load image preprocessor
        self.preprocessor = ImagePreprocessor()

    def process(
        self,
        image_source: Any,
        source_farm: Optional[str] = None,
        destination: Optional[str] = None,
        retry_on_failure: bool = True,
    ) -> Dict[str, Any]:
        """
        Process an image end-to-end.

        Args:
            image_source: Image file path, URL, or array
            source_farm: Source farm identifier
            destination: Destination identifier
            retry_on_failure: Whether to retry on failure

        Returns:
            Complete extraction result
        """
        start_time = time.time()
        extraction_id = f"ext_{uuid4().hex[:12]}"

        try:
            # Load image
            image = self.preprocessor.load_image(image_source)

            # Step 1: CV Detection
            cv_result = self.cv_pipeline.process(image)

            # Step 2: OCR Extraction (from enhanced image)
            enhanced_image = cv_result.get("enhanced_image", image)
            try:
                ocr_result = self.ocr_pipeline.process(enhanced_image)
            except Exception as ocr_error:
                logger.warning(f"OCR failed, continuing with empty OCR fields: {ocr_error}")
                ocr_result = {
                    "all_texts": [],
                    "high_confidence_texts": [],
                    "expiry_date": None,
                    "product_code": None,
                    "quantity": None,
                    "processing_time_ms": 0,
                    "error": str(ocr_error),
                }

            # Step 3: Parsing and Validation
            parsing_result = self.processor.process(
                cv_result={"detections": cv_result.get("detections", [])},
                ocr_result=ocr_result,
                source_farm=source_farm,
                destination=destination,
            )

            processing_time = (time.time() - start_time) * 1000

            return {
                "extraction_id": extraction_id,
                "status": "success",
                "extraction": parsing_result["extraction"],
                "is_valid": parsing_result["is_valid"],
                "errors": parsing_result.get("errors", []),
                "cv_results": {
                    "detections": cv_result.get("detections", []),
                    "processing_time_ms": cv_result.get("processing_time_ms", 0),
                },
                "ocr_results": {
                    "texts_found": len(ocr_result.get("all_texts", [])),
                    "processing_time_ms": ocr_result.get("processing_time_ms", 0),
                },
                "processing_time_ms": processing_time,
            }

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            # Attempt recovery if enabled
            if retry_on_failure:
                logger.info(f"Retry attempt for extraction {extraction_id}")
                # Try with preprocessed variants
                try:
                    image = self.preprocessor.load_image(image_source)
                    variants = self.error_recovery.retry_with_preprocessing(image)

                    for variant in variants[1:]:  # Skip original, try variants
                        try:
                            ocr_result = extract_text(variant, self.config)
                            if ocr_result.get("all_texts"):
                                # Retry parsing with recovered OCR
                                parsing_result = self.processor.process(
                                    cv_result={"detections": []},
                                    ocr_result=ocr_result,
                                    source_farm=source_farm,
                                    destination=destination,
                                )
                                return {
                                    "extraction_id": extraction_id,
                                    "status": "recovered",
                                    "extraction": parsing_result["extraction"],
                                    "is_valid": parsing_result["is_valid"],
                                    "recovery_method": "image_preprocessing",
                                    "processing_time_ms": (time.time() - start_time) * 1000,
                                }
                        except Exception:
                            continue
                except Exception as recovery_error:
                    logger.error(f"Recovery failed: {recovery_error}")

            # Return error result
            return {
                "extraction_id": extraction_id,
                "status": "error",
                "error": str(e),
                "processing_time_ms": processing_time,
            }

    def process_from_cv_only(self, image_source: Any) -> Dict[str, Any]:
        """
        Process image using only CV detection (no OCR).

        Args:
            image_source: Image source

        Returns:
            CV-only extraction result
        """
        start_time = time.time()

        try:
            cv_result = self.cv_pipeline.process(image_source)

            # Create minimal OCR result
            ocr_result = {
                "product_code": None,
                "quantity": None,
                "expiry_date": None,
            }

            parsing_result = self.processor.process(
                cv_result={"detections": cv_result.get("detections", [])},
                ocr_result=ocr_result,
            )

            return {
                "status": "success",
                "extraction": parsing_result["extraction"],
                "is_valid": parsing_result["is_valid"],
                "mode": "cv_only",
                "processing_time_ms": (time.time() - start_time) * 1000,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "mode": "cv_only",
            }


def process_image(
    image_source: Any,
    source_farm: str = None,
    destination: str = None,
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Convenience function for single image processing.

    Args:
        image_source: Image file path, URL, or array
        source_farm: Source farm identifier
        destination: Destination identifier
        config: Optional configuration

    Returns:
        Extraction result
    """
    pipeline = EndToEndPipeline(config)
    return pipeline.process(image_source, source_farm, destination)


def process_batch(
    image_paths: List[str],
    source_farm: str = None,
    destination: str = None,
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Convenience function for batch processing.

    Args:
        image_paths: List of image file paths
        source_farm: Source farm identifier
        destination: Destination identifier
        config: Optional configuration

    Returns:
        Batch results with aggregation
    """
    processor = BatchProcessor(config)
    return processor.process_batch(image_paths, source_farm, destination)


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="End-to-End Logistics Data Extraction")
    parser.add_argument("--image", type=str, help="Single image path")
    parser.add_argument("--batch", type=str, help="Directory with batch of images")
    parser.add_argument("--source-farm", type=str, default="Unknown", help="Source farm ID")
    parser.add_argument("--destination", type=str, default="Unknown", help="Destination ID")

    args = parser.parse_args()

    if args.image:
        result = process_image(
            args.image,
            source_farm=args.source_farm,
            destination=args.destination,
        )
        print(f"Status: {result['status']}")
        print(f"Valid: {result.get('is_valid')}")

    elif args.batch:
        image_dir = Path(args.batch)
        image_paths = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
        image_paths = [str(p) for p in image_paths[:10]]  # Limit to 10

        result = process_batch(
            image_paths,
            source_farm=args.source_farm,
            destination=args.destination,
        )
        print(f"Batch complete: {result['successful']}/{result['total_images']} successful")

    else:
        print("No input provided. Use --image <path> for one image or --batch <dir> for batch mode.")
        parser.print_help()
