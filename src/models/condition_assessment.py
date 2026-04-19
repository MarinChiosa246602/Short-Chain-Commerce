"""
Advanced Condition Assessment Module.

This module provides detailed condition assessment for logistics products:
- Damage detection (bruises, cuts, mold)
- Freshness estimation (color analysis)
- Condition scoring (0-100)
- Multi-product handling
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class DamageType(Enum):
    """Types of detectable damage."""

    BRUISED = "bruised"
    CUT = "cut"
    MOLD = "mold"
    WET = "wet"
    WITHERED = "withered"
    DISCOLORED = "discolored"


class ConditionAssessorAdvanced:
    """
    Advanced condition assessment using computer vision.

    Provides detailed analysis including:
    - Damage type detection
    - Freshness scoring
    - Color-based quality assessment
    """

    # Color ranges for freshness assessment (HSV)
    FRESHNESS_RANGES = {
        # Green vegetables (lettuce, cabbage, etc.)
        "green_vegetable": {
            "hue_low": 35,
            "hue_high": 85,
            "saturation_low": 50,
            "saturation_high": 255,
            "value_low": 50,
            "value_high": 255,
        },
        # Red produce (tomatoes, peppers)
        "red_produce": {
            "hue_low": 0,
            "hue_high": 15,
            "saturation_low": 100,
            "saturation_high": 255,
            "value_low": 50,
            "value_high": 255,
        },
        # Yellow/orange produce (citrus, corn)
        "yellow_produce": {
            "hue_low": 20,
            "hue_high": 35,
            "saturation_low": 100,
            "saturation_high": 255,
            "value_low": 100,
            "value_high": 255,
        },
    }

    # Damage detection thresholds
    DAMAGE_THRESHOLDS = {
        "dark_spot_value": 60,  # Values below this are considered dark spots
        "dark_spot_area_ratio": 0.05,  # Minimum area ratio for damage
        "color_deviation": 30,  # Hue deviation from expected
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the condition assessor.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.default_product_type = self.config.get("product_type", "generic")

    def assess(self, image: np.ndarray, product_type: str = None) -> Dict[str, Any]:
        """
        Perform full condition assessment.

        Args:
            image: Product ROI image (BGR)
            product_type: Type of product for specific analysis

        Returns:
            Comprehensive assessment result
        """
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Run all assessments
        damage_analysis = self._analyze_damage(image, hsv)
        freshness_analysis = self._analyze_freshness(hsv, product_type or self.default_product_type)
        texture_analysis = self._analyze_texture(image)
        color_distribution = self._analyze_color_distribution(hsv)

        # Calculate overall score
        scores = {
            "damage_score": damage_analysis["score"],
            "freshness_score": freshness_analysis["score"],
            "texture_score": texture_analysis["score"],
        }

        # Weighted average (damage is most important)
        overall_score = int(scores["damage_score"] * 0.4 + scores["freshness_score"] * 0.35 + scores["texture_score"] * 0.25)

        # Map to condition category
        condition = self._score_to_condition(overall_score)

        return {
            "condition": condition,
            "score": overall_score,
            "scores_breakdown": scores,
            "damage": damage_analysis,
            "freshness": freshness_analysis,
            "texture": texture_analysis,
            "color_distribution": color_distribution,
            "recommendations": self._generate_recommendations(scores, damage_analysis),
        }

    def _analyze_damage(self, image: np.ndarray, hsv: np.ndarray) -> Dict[str, Any]:
        """Analyze image for damage indicators."""
        damage_details = []
        damage_score = 100

        # 1. Detect dark spots (mold, rot)
        dark_mask = cv2.inRange(hsv, (0, 0, 0), (180, 255, self.DAMAGE_THRESHOLDS["dark_spot_value"]))
        dark_ratio = np.sum(dark_mask > 0) / dark_mask.size

        if dark_ratio > self.DAMAGE_THRESHOLDS["dark_spot_area_ratio"]:
            damage_score -= int(dark_ratio * 50)
            damage_details.append(
                {
                    "type": DamageType.MOLD.value,
                    "severity": "high" if dark_ratio > 0.1 else "medium",
                    "area_ratio": float(dark_ratio),
                }
            )

        # 2. Detect unusual color regions (bruises)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Find regions with unusual brightness
        _, light_mask = cv2.threshold(blur, 240, 255, cv2.THRESH_BINARY)
        _, dark_mask2 = cv2.threshold(blur, 40, 255, cv2.THRESH_BINARY)

        light_ratio = np.sum(light_mask > 0) / light_mask.size
        dark_ratio2 = np.sum(dark_mask2 > 0) / dark_mask2.size

        if light_ratio > 0.15:
            damage_score -= 15
            damage_details.append(
                {
                    "type": DamageType.BRUISED.value,
                    "severity": "medium",
                    "indicator": "unusual_light_regions",
                }
            )

        if dark_ratio2 > 0.15:
            damage_score -= 15
            damage_details.append(
                {
                    "type": DamageType.DISCOLORED.value,
                    "severity": "medium",
                    "indicator": "unusual_dark_regions",
                }
            )

        # 3. Edge-based cut detection
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size

        # High edge density inside product may indicate cuts
        if edge_density > 0.3:
            damage_score -= 10
            damage_details.append(
                {
                    "type": DamageType.CUT.value,
                    "severity": "low",
                    "indicator": "high_edge_density",
                }
            )

        return {
            "score": max(damage_score, 0),
            "detected_damages": damage_details,
            "dark_region_ratio": float(dark_ratio),
        }

    def _analyze_freshness(self, hsv: np.ndarray, product_type: str) -> Dict[str, Any]:
        """Analyze freshness based on color properties."""
        # Get expected color range for product type
        range_key = (
            "green_vegetable"
            if "green" in product_type.lower()
            else (
                "red_produce"
                if "red" in product_type.lower()
                else "yellow_produce" if "yellow" in product_type.lower() else "green_vegetable"
            )
        )  # Default

        expected = self.FRESHNESS_RANGES.get(range_key, self.FRESHNESS_RANGES["green_vegetable"])

        # Create mask for expected color range
        lower = np.array([expected["hue_low"], expected["saturation_low"], expected["value_low"]], dtype=np.uint8)
        upper = np.array([expected["hue_high"], expected["saturation_high"], expected["value_high"]], dtype=np.uint8)

        mask = cv2.inRange(hsv, lower, upper)
        color_ratio = np.sum(mask > 0) / mask.size

        # Calculate saturation and value averages for colored regions
        colored_pixels = hsv[mask > 0]
        if len(colored_pixels) > 0:
            avg_saturation = np.mean(colored_pixels[:, 1])
            avg_value = np.mean(colored_pixels[:, 2])
        else:
            avg_saturation = 0
            avg_value = 0

        # Calculate freshness score
        freshness_score = 100

        # Color ratio indicates freshness (more vibrant = fresher)
        freshness_score -= int((1 - color_ratio) * 30)

        # Saturation affects freshness (too low = faded)
        if avg_saturation < 100:
            freshness_score -= int((100 - avg_saturation) / 100 * 20)

        # Value affects freshness (too dark = wilting, too light = overripe)
        if avg_value < 80:
            freshness_score -= 15
        elif avg_value > 220:
            freshness_score -= 10

        return {
            "score": max(freshness_score, 0),
            "color_ratio": float(color_ratio),
            "avg_saturation": float(avg_saturation),
            "avg_value": float(avg_value),
            "product_category": range_key,
        }

    def _analyze_texture(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze texture for wilting/withered detection."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Laplacian variance for texture analysis
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_variance = np.var(laplacian)

        # Normalize variance (higher = more texture = fresher for most produce)
        # This is heuristic and would be refined with training data
        texture_score = min(texture_variance / 100, 100)

        # Detect smoothness (wilting = smoother surface)
        blur = cv2.GaussianBlur(gray, (15, 15), 0)
        diff = cv2.absdiff(gray, blur)
        smoothness = np.mean(diff)

        # High smoothness may indicate wilting
        if smoothness < 20:
            texture_score = min(texture_score, 60)

        return {
            "score": int(texture_score),
            "texture_variance": float(texture_variance),
            "smoothness": float(smoothness),
        }

    def _analyze_color_distribution(self, hsv: np.ndarray) -> Dict[str, Any]:
        """Analyze color distribution for quality assessment."""
        # Calculate hue histogram
        hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hist_norm = cv2.normalize(hist, hist).flatten()

        # Find dominant hue regions
        peaks = []
        for i in range(0, 180, 10):
            if hist_norm[i] > 0.1:
                peaks.append({"hue_range": f"{i}-{i+10}", "relative_intensity": float(hist_norm[i])})

        # Calculate color uniformity
        color_uniformity = 1 - np.std(hist_norm)

        return {
            "dominant_hues": peaks[:5],  # Top 5 peaks
            "color_uniformity": float(color_uniformity),
            "histogram": hist_norm.tolist(),
        }

    def _score_to_condition(self, score: int) -> str:
        """Map numeric score to condition category."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 50:
            return "fair"
        elif score >= 25:
            return "poor"
        else:
            return "damaged"

    def _generate_recommendations(self, scores: Dict[str, float], damage_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on assessment."""
        recommendations = []

        if scores["damage_score"] < 70:
            recommendations.append("Inspect for visible damage before shipping")

        if scores["freshness_score"] < 70:
            recommendations.append("Consider expedited shipping due to freshness concerns")

        if scores["texture_score"] < 60:
            recommendations.append("Check for wilting; may need humidity adjustment")

        damage_types = [d["type"] for d in damage_analysis.get("detected_damages", [])]
        if DamageType.MOLD.value in damage_types:
            recommendations.append("HIGH PRIORITY: Potential mold detected - isolate affected items")

        return recommendations


class MultiProductAssessor:
    """
    Assess conditions for multiple products in a single image.

    Handles mixed crates with different product types.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize multi-product assessor.

        Args:
            config: Configuration including product-specific settings
        """
        self.config = config or {}
        self.assessor = ConditionAssessorAdvanced(config)

    def assess_products(
        self,
        image: np.ndarray,
        product_rois: List[Tuple[np.ndarray, str]],
    ) -> List[Dict[str, Any]]:
        """
        Assess multiple product regions.

        Args:
            image: Full image (for context)
            product_rois: List of (roi_image, product_type) tuples

        Returns:
            List of assessments for each product
        """
        results = []

        for i, (roi, product_type) in enumerate(product_rois):
            if roi is None or roi.size == 0:
                results.append(
                    {
                        "product_index": i,
                        "product_type": product_type,
                        "status": "error",
                        "error": "Invalid ROI",
                    }
                )
                continue

            assessment = self.assessor.assess(roi, product_type)
            assessment["product_index"] = i
            assessment["product_type"] = product_type
            results.append(assessment)

        return results

    def aggregate_assessments(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate multiple product assessments.

        Args:
            assessments: List of individual assessments

        Returns:
            Aggregated summary
        """
        if not assessments:
            return {
                "total_products": 0,
                "status": "no_products",
            }

        # Filter out errors
        valid = [a for a in assessments if a.get("score") is not None]

        if not valid:
            return {
                "total_products": len(assessments),
                "valid_assessments": 0,
                "status": "all_errors",
            }

        scores = [a["score"] for a in valid]
        conditions = [a["condition"] for a in valid]

        # Count conditions
        condition_counts = {}
        for c in conditions:
            condition_counts[c] = condition_counts.get(c, 0) + 1

        # Product type distribution
        type_scores = {}
        for a in valid:
            ptype = a.get("product_type", "unknown")
            if ptype not in type_scores:
                type_scores[ptype] = []
            type_scores[ptype].append(a["score"])

        avg_by_type = {k: sum(v) / len(v) for k, v in type_scores.items()}

        return {
            "total_products": len(valid),
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "condition_distribution": condition_counts,
            "average_score_by_type": avg_by_type,
            "all_assessments": valid,
        }


# Convenience functions
def assess_condition(
    image: np.ndarray,
    product_type: str = None,
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Quick function to assess product condition.

    Args:
        image: Product ROI image
        product_type: Type of product
        config: Optional configuration

    Returns:
        Condition assessment result
    """
    assessor = ConditionAssessorAdvanced(config)
    return assessor.assess(image, product_type)


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python condition_assessment.py <image_path> [product_type]")
        sys.exit(1)

    image_path = sys.argv[1]
    product_type = sys.argv[2] if len(sys.argv) > 2 else None

    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        sys.exit(1)

    result = assess_condition(image, product_type)

    print(f"Condition: {result['condition']}")
    print(f"Score: {result['score']}/100")
    print("Breakdown:")
    print(f"  Damage: {result['scores_breakdown']['damage_score']}")
    print(f"  Freshness: {result['scores_breakdown']['freshness_score']}")
    print(f"  Texture: {result['scores_breakdown']['texture_score']}")

    if result["recommendations"]:
        print("Recommendations:")
        for rec in result["recommendations"]:
            print(f"  - {rec}")
