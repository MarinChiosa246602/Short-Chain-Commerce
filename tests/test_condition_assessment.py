"""
Tests for condition assessment module.
"""

import pytest
import numpy as np
import cv2

from models.condition_assessment import (
    ConditionAssessorAdvanced,
    MultiProductAssessor,
    DamageType,
    assess_condition,
)


class TestConditionAssessorAdvanced:
    """Test advanced condition assessor."""

    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {'product_type': 'tomato'}
        assessor = ConditionAssessorAdvanced(config)
        assert assessor.default_product_type == 'tomato'
        assert assessor.config == config

    def test_init_default_config(self):
        """Test initialization with default config."""
        assessor = ConditionAssessorAdvanced()
        assert assessor.default_product_type == 'generic'
        assert assessor.config == {}

    def test_assess_returns_required_fields(self):
        """Test that assessment returns all required fields."""
        assessor = ConditionAssessorAdvanced()
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = assessor.assess(image, 'tomato')

        assert 'condition' in result
        assert 'score' in result
        assert 'scores_breakdown' in result
        assert 'damage' in result
        assert 'freshness' in result
        assert 'texture' in result
        assert 'recommendations' in result

    def test_assess_score_range(self):
        """Test that score is in valid range."""
        assessor = ConditionAssessorAdvanced()

        # Test with various images
        for _ in range(5):
            image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            result = assessor.assess(image, 'green_vegetable')
            assert 0 <= result['score'] <= 100

    def test_score_to_condition_mapping(self):
        """Test score to condition category mapping."""
        assessor = ConditionAssessorAdvanced()

        # Test boundary conditions
        assert assessor._score_to_condition(95) == 'excellent'
        assert assessor._score_to_condition(90) == 'excellent'
        assert assessor._score_to_condition(89) == 'good'
        assert assessor._score_to_condition(75) == 'good'
        assert assessor._score_to_condition(74) == 'fair'
        assert assessor._score_to_condition(50) == 'fair'
        assert assessor._score_to_condition(49) == 'poor'
        assert assessor._score_to_condition(25) == 'poor'
        assert assessor._score_to_condition(24) == 'damaged'
        assert assessor._score_to_condition(0) == 'damaged'

    def test_analyze_damage_returns_structure(self):
        """Test damage analysis returns expected structure."""
        assessor = ConditionAssessorAdvanced()
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        result = assessor._analyze_damage(image, hsv)

        assert 'score' in result
        assert 'detected_damages' in result
        assert 'dark_region_ratio' in result
        assert isinstance(result['detected_damages'], list)

    def test_analyze_freshness_returns_structure(self):
        """Test freshness analysis returns expected structure."""
        assessor = ConditionAssessorAdvanced()
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        result = assessor._analyze_freshness(hsv, 'green_vegetable')

        assert 'score' in result
        assert 'color_ratio' in result
        assert 'avg_saturation' in result
        assert 'avg_value' in result
        assert 'product_category' in result

    def test_analyze_texture_returns_structure(self):
        """Test texture analysis returns expected structure."""
        assessor = ConditionAssessorAdvanced()
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = assessor._analyze_texture(image)

        assert 'score' in result
        assert 'texture_variance' in result
        assert 'smoothness' in result

    def test_analyze_color_distribution_returns_structure(self):
        """Test color distribution analysis returns expected structure."""
        assessor = ConditionAssessorAdvanced()
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        result = assessor._analyze_color_distribution(hsv)

        assert 'dominant_hues' in result
        assert 'color_uniformity' in result
        assert 'histogram' in result
        assert len(result['dominant_hues']) <= 5

    def test_generate_recommendations_empty_when_fine(self):
        """Test that good scores generate no recommendations."""
        assessor = ConditionAssessorAdvanced()

        scores = {
            'damage_score': 100,
            'freshness_score': 100,
            'texture_score': 100,
        }

        recommendations = assessor._generate_recommendations(scores, {'detected_damages': []})
        assert len(recommendations) == 0

    def test_generate_recommendations_for_damage(self):
        """Test recommendations are generated for damage."""
        assessor = ConditionAssessorAdvanced()

        scores = {
            'damage_score': 50,
            'freshness_score': 100,
            'texture_score': 100,
        }

        recommendations = assessor._generate_recommendations(
            scores,
            {'detected_damages': [{'type': DamageType.MOLD.value}]}
        )

        assert any('damage' in r.lower() for r in recommendations)
        assert any('HIGH PRIORITY' in r for r in recommendations)


class TestMultiProductAssessor:
    """Test multi-product assessor."""

    def test_init(self):
        """Test multi-product assessor initialization."""
        assessor = MultiProductAssessor({'test': 'config'})
        assert assessor.config == {'test': 'config'}

    def test_assess_products_empty_list(self):
        """Test assessing empty product list."""
        assessor = MultiProductAssessor()
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        results = assessor.assess_products(image, [])

        assert results == []

    def test_assess_products_single_product(self):
        """Test assessing single product."""
        assessor = MultiProductAssessor()
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        roi = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

        results = assessor.assess_products(image, [(roi, 'tomato')])

        assert len(results) == 1
        assert results[0]['product_index'] == 0
        assert results[0]['product_type'] == 'tomato'
        assert results[0]['score'] is not None

    def test_assess_products_with_invalid_roi(self):
        """Test assessing with invalid ROI."""
        assessor = MultiProductAssessor()
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        results = assessor.assess_products(image, [(None, 'tomato')])

        assert len(results) == 1
        assert results[0]['status'] == 'error'

    def test_aggregate_assessments_empty(self):
        """Test aggregating empty assessments."""
        assessor = MultiProductAssessor()

        result = assessor.aggregate_assessments([])

        assert result['total_products'] == 0
        assert result['status'] == 'no_products'

    def test_aggregate_assessments_multiple_products(self):
        """Test aggregating multiple product assessments."""
        assessor = MultiProductAssessor()

        assessments = [
            {'score': 90, 'condition': 'excellent', 'product_type': 'tomato'},
            {'score': 75, 'condition': 'good', 'product_type': 'tomato'},
            {'score': 50, 'condition': 'fair', 'product_type': 'lettuce'},
        ]

        result = assessor.aggregate_assessments(assessments)

        assert result['total_products'] == 3
        assert result['average_score'] == 71.67
        assert result['min_score'] == 50
        assert result['max_score'] == 90
        assert result['condition_distribution']['excellent'] == 1
        assert result['condition_distribution']['good'] == 1
        assert result['condition_distribution']['fair'] == 1

    def test_aggregate_assessments_with_errors(self):
        """Test aggregating assessments with some errors."""
        assessor = MultiProductAssessor()

        assessments = [
            {'score': 90, 'condition': 'excellent', 'product_type': 'tomato'},
            {'status': 'error', 'error': 'Invalid ROI'},
            {'score': 75, 'condition': 'good', 'product_type': 'tomato'},
        ]

        result = assessor.aggregate_assessments(assessments)

        assert result['total_products'] == 2  # Only valid ones


class TestAssessConditionFunction:
    """Test convenience function."""

    def test_assess_condition_quick_function(self):
        """Test the assess_condition convenience function."""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = assess_condition(image, 'tomato')

        assert 'condition' in result
        assert 'score' in result


class TestEdgeCases:
    """Test edge cases."""

    def test_assess_with_very_small_image(self):
        """Test assessment with very small image."""
        assessor = ConditionAssessorAdvanced()
        image = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)

        result = assessor.assess(image, 'tomato')

        assert result['score'] is not None
        assert 0 <= result['score'] <= 100

    def test_assess_with_very_large_image(self):
        """Test assessment with large image."""
        assessor = ConditionAssessorAdvanced()
        image = np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8)

        result = assessor.assess(image, 'tomato')

        assert result['score'] is not None
        assert 0 <= result['score'] <= 100

    def test_assess_with_uniform_color_image(self):
        """Test assessment with uniform color image."""
        assessor = ConditionAssessorAdvanced()
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = assessor.assess(image, 'tomato')

        assert result['score'] is not None

    def test_assess_with_black_image(self):
        """Test assessment with all black image."""
        assessor = ConditionAssessorAdvanced()
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        result = assessor.assess(image, 'tomato')

        # Black image should indicate mold/damage
        assert result['score'] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
