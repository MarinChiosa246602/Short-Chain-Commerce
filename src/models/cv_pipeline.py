"""
Computer Vision Pipeline for logistics data extraction.

This module handles:
- Object detection (YOLOv8) for product/crate detection
- Image preprocessing and enhancement
- Condition assessment
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image
import io

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


class ImagePreprocessor:
    """Preprocess images for optimal CV model inference."""

    @staticmethod
    def load_image(image_source: Any) -> np.ndarray:
        """
        Load image from various sources.

        Args:
            image_source: Can be a file path, PIL Image, or numpy array

        Returns:
            Image as numpy array (BGR format for OpenCV)
        """
        if isinstance(image_source, str):
            # Load from file path
            if image_source.startswith(('http://', 'https://')):
                # Download from URL
                import requests
                response = requests.get(image_source)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
            else:
                image = Image.open(image_source)
        elif isinstance(image_source, Image.Image):
            image = image_source
        elif isinstance(image_source, np.ndarray):
            return image_source
        else:
            raise ValueError(f"Unsupported image source type: {type(image_source)}")

        # Convert to BGR for OpenCV compatibility
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def preprocess_for_detection(image: np.ndarray, target_size: int = 640) -> np.ndarray:
        """
        Preprocess image for object detection.

        Args:
            image: Input image (BGR format)
            target_size: Target size for YOLO model (default 640)

        Returns:
            Preprocessed image ready for model inference
        """
        # Resize maintaining aspect ratio
        h, w = image.shape[:2]
        scale = target_size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Pad to target size
        pad_w = target_size - new_w
        pad_h = target_size - new_h
        pad_left = pad_w // 2
        pad_right = pad_w - pad_left
        pad_top = pad_h // 2
        pad_bottom = pad_h - pad_top

        padded = cv2.copyMakeBorder(
            resized, pad_top, pad_bottom, pad_left, pad_right,
            cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )

        # Normalize to [0, 1]
        normalized = padded.astype(np.float32) / 255.0

        # HWC to CHW format
        return np.transpose(normalized, (2, 0, 1))

    @staticmethod
    def enhance_image(image: np.ndarray) -> np.ndarray:
        """
        Enhance image quality for better OCR performance.

        Args:
            image: Input image

        Returns:
            Enhanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        # Split into L, A, B channels
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L channel (lightness)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced_l = clahe.apply(l)

        # Merge channels back
        enhanced_lab = cv2.merge((enhanced_l, a, b))

        # Convert back to BGR
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)


class ConditionAssessor:
    """Assess product condition from visual features."""

    # Color thresholds for freshness assessment
    FRESHNESS_COLORS = {
        'tomato': {'red_low': 0, 'red_high': 50, 'green_low': 0, 'green_high': 100},
        'lettuce': {'green_low': 100, 'green_high': 255},
    }

    def assess_condition(self, image: np.ndarray, product_type: str) -> Dict[str, Any]:
        """
        Assess the condition of a product.

        Args:
            image: Product ROI image
            product_type: Type of product

        Returns:
            Dictionary with condition score and assessment
        """
        score = 100  # Start with perfect score
        issues = []

        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Check for damage indicators
        damage_score = self._detect_damage(hsv)
        if damage_score < 0.7:
            score -= 30
            issues.append("visible_damage")

        # Check color freshness
        freshness_score = self._assess_color_freshness(hsv, product_type)
        if freshness_score < 0.7:
            score -= 20
            issues.append("color_fading")

        # Check for mold/wetness (dark spots)
        mold_score = self._detect_mold(image)
        if mold_score < 0.8:
            score -= 25
            issues.append("potential_mold")

        # Map score to condition enum
        if score >= 90:
            condition = "excellent"
        elif score >= 75:
            condition = "good"
        elif score >= 50:
            condition = "fair"
        elif score >= 25:
            condition = "poor"
        else:
            condition = "damaged"

        return {
            "condition": condition,
            "score": score,
            "issues": issues,
        }

    def _detect_damage(self, hsv: np.ndarray) -> float:
        """Detect visible damage in the product."""
        # Simple damage detection based on unusual color patterns
        # This would be enhanced with a trained model in production
        return 1.0  # Placeholder

    def _assess_color_freshness(self, hsv: np.ndarray, product_type: str) -> float:
        """Assess freshness based on color."""
        # Placeholder - would use trained color analysis
        return 1.0  # Placeholder

    def _detect_mold(self, image: np.ndarray) -> float:
        """Detect potential mold or wetness."""
        # Detect dark, saturated regions that might indicate mold
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        dark_regions = cv2.inRange(gray, 0, 50)
        dark_ratio = np.sum(dark_regions > 0) / dark_regions.size
        return 1.0 - min(dark_ratio, 1.0)


class ObjectDetector:
    """
    Object detection using YOLOv8.

    Detects crates, products, and other logistics items.
    """

    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        """
        Initialize the object detector.

        Args:
            model_path: Path to YOLOv8 model weights (default: pretrained model)
            confidence_threshold: Minimum confidence for detections
        """
        if not YOLO_AVAILABLE:
            raise ImportError(
                "ultralytics package is required. Install with: pip install ultralytics"
            )

        self.model = YOLO(model_path or 'yolov8m.pt')
        self.confidence_threshold = confidence_threshold
        self.preprocessor = ImagePreprocessor()
        self.condition_assessor = ConditionAssessor()

        # Default classes for logistics detection
        # In production, train on custom dataset
        self.class_names = [
            'crate', 'box', 'product', 'label', 'barcode'
        ]

    def detect(self, image_source: Any) -> List[Dict[str, Any]]:
        """
        Run object detection on an image.

        Args:
            image_source: Image file path, URL, or array

        Returns:
            List of detections with bounding boxes and metadata
        """
        # Load and preprocess image
        image = self.preprocessor.load_image(image_source)

        # Run inference
        results = self.model(image, conf=self.confidence_threshold)

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    box = boxes[i]
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    cls = int(box.cls[0].cpu().numpy())

                    detection = {
                        "class_id": cls,
                        "class_name": self.class_names[cls] if cls < len(self.class_names) else "unknown",
                        "confidence": conf,
                        "bbox": {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2),
                        },
                        "center": {
                            "x": int((x1 + x2) / 2),
                            "y": int((y1 + y2) / 2),
                        },
                    }

                    # Add condition assessment for products
                    if detection["class_name"] == "product":
                        roi = image[int(y1):int(y2), int(x1):int(x2)]
                        condition = self.condition_assessor.assess_condition(roi, "unknown")
                        detection["condition"] = condition

                    detections.append(detection)

        return detections

    def detect_multiple_products(self, image_source: Any) -> List[Dict[str, Any]]:
        """
        Detect multiple products in mixed crates.

        Args:
            image_source: Image source

        Returns:
            Grouped product detections
        """
        detections = self.detect(image_source)

        # Cluster detections by visual similarity
        # This is a placeholder - would use actual clustering in production
        return detections


class CVPipeline:
    """
    Main Computer Vision Pipeline.

    Chains together all CV components for end-to-end extraction.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CV pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or {}
        self.preprocessor = ImagePreprocessor()

        try:
            self.detector = ObjectDetector(
                confidence_threshold=self.config.get('detection_confidence', 0.5)
            )
        except ImportError as e:
            self.detector = None
            print(f"Warning: Object detection not available: {e}")

        self.condition_assessor = ConditionAssessor()

    def process(self, image_source: Any) -> Dict[str, Any]:
        """
        Run full CV pipeline on an image.

        Args:
            image_source: Image to process

        Returns:
            Dictionary with detection results and extracted features
        """
        start_time = __import__('time').time()

        # Load image
        image = self.preprocessor.load_image(image_source)

        # Preprocess for detection
        preprocessed = self.preprocessor.preprocess_for_detection(image)

        # Run object detection
        detections = []
        if self.detector:
            detections = self.detector.detect(image_source)

        # Enhance for OCR
        enhanced = self.preprocessor.enhance_image(image)

        processing_time = (__import__('time').time() - start_time) * 1000

        return {
            "detections": detections,
            "image_shape": image.shape,
            "enhanced_image": enhanced,
            "processing_time_ms": processing_time,
        }


# Convenience function for quick processing
def process_image(image_source: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Quick function to process an image with the CV pipeline.

    Args:
        image_source: Image to process
        config: Optional configuration

    Returns:
        Processing results
    """
    pipeline = CVPipeline(config)
    return pipeline.process(image_source)
