"""
OCR Testing Script for Task 1.5

This script tests the OCR pipeline on mock dataset images and generates:
- Extraction results
- Confidence analysis
- Error statistics
"""

import os
import json
import glob
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from models.ocr_pipeline import OCRPipeline, extract_text


def test_single_image(image_path: str, config: dict = None):
    """
    Test OCR on a single image.

    Args:
        image_path: Path to the image
        config: Optional OCR configuration

    Returns:
        Dictionary with extraction results
    """
    print(f"\nProcessing: {image_path}")

    try:
        # Load image to check if it exists
        image = cv2.imread(image_path)
        if image is None:
            return {
                'image_path': image_path,
                'status': 'error',
                'error': 'Failed to load image',
            }

        start_time = time.time()

        # Run OCR
        config = config or {}
        result = extract_text(image_path, config)

        processing_time = (time.time() - start_time) * 1000

        return {
            'image_path': image_path,
            'status': 'success',
            'processing_time_ms': processing_time,
            'texts_found': len(result.get('all_texts', [])),
            'high_confidence_texts': len(result.get('high_confidence_texts', [])),
            'extracted_expiry_date': result.get('expiry_date'),
            'extracted_product_code': result.get('product_code'),
            'extracted_quantity': result.get('quantity'),
        }

    except Exception as e:
        return {
            'image_path': image_path,
            'status': 'error',
            'error': str(e),
        }


def test_batch_images(image_paths: list, config: dict = None, verbose: bool = False):
    """
    Test OCR on a batch of images.

    Args:
        image_paths: List of image paths
        config: Optional OCR configuration
        verbose: Print detailed progress

    Returns:
        Dictionary with batch results and statistics
    """
    results = []
    successful = 0
    failed = 0
    total_time = 0

    for i, path in enumerate(image_paths):
        if verbose:
            print(f"[{i+1}/{len(image_paths)}] {path}")

        result = test_single_image(path, config)
        results.append(result)

        if result.get('status') == 'success':
            successful += 1
            total_time += result.get('processing_time_ms', 0)
        else:
            failed += 1

    # Calculate statistics
    stats = {
        'total_images': len(image_paths),
        'successful': successful,
        'failed': failed,
        'success_rate': successful / len(image_paths) if image_paths else 0,
        'avg_processing_time_ms': total_time / successful if successful > 0 else 0,
    }

    return {
        'results': results,
        'statistics': stats,
    }


def run_test_suite():
    """
    Run the complete OCR test suite.
    """
    print("=" * 60)
    print("OCR TEST SUITE - Task 1.5")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Find test images
    data_dir = Path("data/raw/images")
    if not data_dir.exists():
        print(f"\nData directory not found: {data_dir}")
        print("Creating mock test results...")

        # Create mock results for demonstration
        mock_results = {
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'language': 'en',
                'confidence_threshold': 0.7,
            },
            'test_images': [],
            'statistics': {
                'total_images': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0,
                'avg_processing_time_ms': 0,
            },
            'notes': [
                'Test suite requires PaddleOCR to be installed',
                'Run: pip install paddlepaddle paddleocr',
                'Test images found in: data/raw/images/',
            ],
        }

        return mock_results

    # Get image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(glob.glob(str(data_dir / ext)))

    image_paths = image_paths[:20]  # Limit to first 20 images

    print(f"\nFound {len(image_paths)} test images")
    print(f"Test directory: {data_dir}")

    # Test with different configurations
    test_configs = [
        {'language': 'en', 'confidence_threshold': 0.7},
        {'language': 'en', 'confidence_threshold': 0.85},
    ]

    all_results = {}

    for i, config in enumerate(test_configs):
        print(f"\n--- Test Configuration {i+1}: {config} ---")

        batch_result = test_batch_images(image_paths, config, verbose=True)
        all_results[f'config_{i+1}'] = {
            'configuration': config,
            'results': batch_result,
        }

    # Compile final report
    final_report = {
        'timestamp': datetime.now().isoformat(),
        'test_configs': all_results,
        'summary': {
            'total_images_tested': len(image_paths),
            'configurations_tested': len(test_configs),
        },
    }

    return final_report


def main():
    """
    Main entry point for OCR testing.
    """
    # Run test suite
    report = run_test_suite()

    # Save report
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"ocr_test_results_{timestamp}.json"

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print("TEST COMPLETE")
    print(f"{'=' * 60}")
    print(f"Report saved to: {report_path}")
    print(f"Summary: {json.dumps(report.get('summary', {}), indent=2)}")


if __name__ == "__main__":
    main()
