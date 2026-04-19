"""
Combined CV + OCR Example Script

This script demonstrates how to combine object detection (YOLOv8) with OCR
for complete logistics data extraction from images.
"""

import cv2
import numpy as np
from ultralytics import YOLO
from models.ocr_pipeline import OCRPipeline, extract_text


class CombinedExtractionPipeline:
    """
    Pipeline that combines CV detection with OCR for complete extraction.
    """

    def __init__(self, cv_model_path: str = None, ocr_config: dict = None):
        """
        Initialize the combined pipeline.

        Args:
            cv_model_path: Path to YOLOv8 model weights
            ocr_config: Configuration for OCR pipeline
        """
        self.ocr_pipeline = OCRPipeline(ocr_config or {})

        if cv_model_path:
            self.cv_model = YOLO(cv_model_path)
        else:
            self.cv_model = None

    def extract_crate_regions(self, image: np.ndarray):
        """
        Use CV model to detect crate regions.

        Args:
            image: Input BGR image

        Returns:
            List of detected crate bounding boxes
        """
        if self.cv_model is None:
            # Return full image as single region if no CV model
            return [(0, 0, image.shape[1], image.shape[0])]

        results = self.cv_model(image)
        boxes = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                boxes.append((int(x1), int(y1), int(x2), int(y2)))

        return boxes

    def extract_from_crate_region(self, image: np.ndarray, bbox: tuple) -> dict:
        """
        Extract data from a specific crate region.

        Args:
            image: Source image
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            Extracted data dictionary
        """
        x1, y1, x2, y2 = bbox

        # Crop to ROI
        roi = image[y1:y2, x1:x2]

        # Run OCR on ROI
        ocr_result = extract_text(roi, self.ocr_pipeline.config)

        return {
            'bbox': bbox,
            'ocr_result': ocr_result,
        }

    def process(self, image_path: str) -> dict:
        """
        Process an image and extract complete logistics data.

        Args:
            image_path: Path to the image

        Returns:
            Complete extraction results
        """
        import time
        start_time = time.time()

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return {'error': f'Failed to load image: {image_path}'}

        # Detect crate regions
        crate_regions = self.extract_crate_regions(image)

        # Extract from each region
        extractions = []
        for bbox in crate_regions:
            extraction = self.extract_from_crate_region(image, bbox)
            extractions.append(extraction)

        processing_time = (time.time() - start_time) * 1000

        return {
            'image_path': image_path,
            'crate_regions_found': len(crate_regions),
            'extractions': extractions,
            'processing_time_ms': processing_time,
        }


def main():
    """
    Example usage of the combined pipeline.
    """
    # Initialize pipeline
    pipeline = CombinedExtractionPipeline(
        cv_model_path=None,  # Set to YOLO model path for CV detection
        ocr_config={
            'language': 'en',
            'confidence_threshold': 0.7,
        }
    )

    # Process an image
    image_path = 'data/raw/images/img_0000.jpg'
    result = pipeline.process(image_path)

    print("Extraction Results:")
    print(f"  Crates found: {result['crate_regions_found']}")
    print(f"  Processing time: {result['processing_time_ms']:.2f}ms")

    for i, extraction in enumerate(result.get('extractions', [])):
        print(f"\n  Crate {i+1}:")
        print(f"    Bounding box: {extraction['bbox']}")

        ocr = extraction['ocr_result']
        print(f"    Texts found: {len(ocr.get('all_texts', []))}")
        print(f"    Product code: {ocr.get('product_code')}")
        print(f"    Expiry date: {ocr.get('expiry_date')}")
        print(f"    Quantity: {ocr.get('quantity')}")


if __name__ == "__main__":
    main()
