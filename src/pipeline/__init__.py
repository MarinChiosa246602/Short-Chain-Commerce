"""
Pipeline module for end-to-end logistics data extraction.

This module provides:
- EndToEndPipeline: Main pipeline chaining CV + OCR + Validation
- BatchProcessor: Batch processing for multiple images
- ErrorRecovery: Error handling and retry mechanisms
"""

from pipeline.end_to_end import BatchProcessor, EndToEndPipeline, ErrorRecovery, process_batch, process_image

__all__ = [
    "EndToEndPipeline",
    "BatchProcessor",
    "ErrorRecovery",
    "process_image",
    "process_batch",
]
