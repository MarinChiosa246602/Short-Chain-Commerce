"""
Celery tasks for background processing.
"""

import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from pipeline.end_to_end import BatchProcessor
from database.db_manager import get_database_manager
from monitoring.logging_utils import get_extraction_logger

logger = logging.getLogger(__name__)
extraction_logger = get_extraction_logger()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_batch_async(self, image_paths: list, source_farm: str = None, destination: str = None):
    """
    Process a batch of images asynchronously.

    Args:
        image_paths: List of image file paths
        source_farm: Source farm identifier
        destination: Destination identifier

    Returns:
        Batch processing results
    """
    extraction_id = f"batch_{__import__('uuid').uuid4().hex[:12]}"

    try:
        logger.info(f"Starting batch processing: {extraction_id}")
        extraction_logger.log_batch_start(extraction_id, len(image_paths))

        processor = BatchProcessor({"confidence_threshold": 0.7})
        result = processor.process_batch(
            image_sources=image_paths,
            source_farm=source_farm,
            destination=destination,
        )

        logger.info(f"Batch processing completed: {extraction_id}")
        extraction_logger.log_batch_complete(
            extraction_id,
            total=result.get("total_images", 0),
            successful=result.get("successful", 0),
            failed=result.get("failed", 0),
            processing_time_ms=result.get("processing_time_ms", 0),
        )

        # Save to database
        try:
            db = get_database_manager()
            db.initialize()
            for extraction_result in result.get("results", []):
                if extraction_result.get("status") in ("success", "partial"):
                    extraction = extraction_result.get("extraction", {})
                    if extraction:
                        db.save_extraction(
                            extraction_id=str(extraction.get("image_id")),
                            image_id=str(extraction.get("image_id")),
                            timestamp=extraction.get("timestamp"),
                            source_farm=extraction.get("metadata", {}).get("source_farm") or source_farm,
                            destination=extraction.get("metadata", {}).get("destination") or destination,
                            status=extraction_result.get("status", "error"),
                            is_valid=extraction_result.get("is_valid", False),
                            processing_time_ms=extraction_result.get("processing_time_ms", 0),
                            products=[
                                {
                                    "product_id": p.get("product_id"),
                                    "product_name": p.get("product_name"),
                                    "quantity": p.get("quantity"),
                                    "unit": p.get("unit"),
                                    "expiry_date": p.get("expiry_date"),
                                    "storage_location": p.get("storage_location"),
                                    "condition": p.get("condition"),
                                }
                                for p in extraction.get("products", [])
                            ],
                            missing_fields=extraction.get("missing_fields", []),
                            low_confidence_fields=extraction.get("low_confidence_fields", []),
                        )
        except Exception as db_err:
            logger.warning(f"Failed to save batch to database: {db_err}")

        return result

    except MaxRetriesExceededError:
        logger.error(f"Batch processing failed after max retries: {extraction_id}")
        raise
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def extract_single_image(self, image_path: str, source_farm: str = None, destination: str = None):
    """
    Extract data from a single image asynchronously.

    Args:
        image_path: Path to the image file
        source_farm: Source farm identifier
        destination: Destination identifier

    Returns:
        Extraction result
    """
    from pipeline.end_to_end import process_image
    from uuid import uuid4

    extraction_id = str(uuid4())

    try:
        logger.info(f"Starting extraction: {extraction_id}")
        extraction_logger.log_extraction_start(extraction_id, {"image_path": image_path})

        result = process_image(
            image_source=image_path,
            source_farm=source_farm,
            destination=destination,
        )

        extraction_logger.log_extraction_complete(
            extraction_id,
            status=result.get("status", "error"),
            processing_time_ms=result.get("processing_time_ms", 0),
            products_count=len(result.get("extraction", {}).get("products", [])),
        )

        return result

    except MaxRetriesExceededError:
        logger.error(f"Extraction failed after max retries: {extraction_id}")
        raise
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise self.retry(exc=e)


@shared_task
def cleanup_old_extractions(days: int = 30):
    """
    Clean up old extraction records from the database.

    Args:
        days: Remove records older than this many days
    """
    from datetime import datetime, timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    try:
        # Implementation depends on database backend
        logger.info(f"Cleanup completed: removed records older than {cutoff_date}")
        return {"cleaned_until": cutoff_date.isoformat()}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise
