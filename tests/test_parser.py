"""
Tests for data parser and validator.
"""

import pytest
from datetime import datetime, timedelta

from utils.parser import (
    FieldValidator,
    DataParser,
    DataValidator,
    ExtractionProcessor,
)
from models.schemas import (
    Product,
    Metadata,
    UnitType,
    ConditionType,
    ExtractionResponse,
)


class TestFieldValidator:
    """Test field validation functions."""

    def test_validate_date_valid(self):
        """Test validating a valid future date."""
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        result = FieldValidator.validate_date(future_date)
        assert result is not None
        assert isinstance(result, datetime)

    def test_validate_date_invalid_past(self):
        """Test validating a past date (should return None)."""
        past_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        result = FieldValidator.validate_date(past_date)
        assert result is None

    def test_validate_date_invalid_format(self):
        """Test validating an invalid date format."""
        result = FieldValidator.validate_date("not-a-date")
        assert result is None

    def test_validate_quantity_valid(self):
        """Test validating valid quantities."""
        assert FieldValidator.validate_quantity(24) == 24
        assert FieldValidator.validate_quantity(1) == 1
        assert FieldValidator.validate_quantity(99999) == 99999

    def test_validate_quantity_invalid(self):
        """Test validating invalid quantities."""
        assert FieldValidator.validate_quantity(0) is None
        assert FieldValidator.validate_quantity(-5) is None
        assert FieldValidator.validate_quantity(100000) is None
        assert FieldValidator.validate_quantity("invalid") is None

    def test_validate_unit(self):
        """Test unit validation and mapping."""
        assert FieldValidator.validate_unit("crate") == UnitType.CRATE
        assert FieldValidator.validate_unit("kg") == UnitType.KG
        assert FieldValidator.validate_unit("Kilograms") == UnitType.KG
        assert FieldValidator.validate_unit("invalid") is None

    def test_validate_condition(self):
        """Test condition validation and mapping."""
        assert FieldValidator.validate_condition("excellent") == ConditionType.EXCELLENT
        assert FieldValidator.validate_condition("good") == ConditionType.GOOD
        assert FieldValidator.validate_condition("FAIR") == ConditionType.FAIR
        assert FieldValidator.validate_condition("invalid") is None


class TestDataParser:
    """Test data parsing functions."""

    def test_parse_product_basic(self):
        """Test parsing a basic product."""
        parser = DataParser()
        cv_detection = {"class_name": "tomato", "condition": {"condition": "excellent", "score": 95}}
        ocr_result = {"product_code": "TOM-001", "quantity": 24}

        product, missing = parser.parse_product(cv_detection, ocr_result)

        assert product.product_id == "TOM-001"
        assert product.product_name == "Tomato"
        assert product.quantity == 24
        assert product.unit == UnitType.PIECE
        assert len(missing) == 0

    def test_parse_product_missing_fields(self):
        """Test parsing product with missing fields."""
        parser = DataParser()
        product, missing = parser.parse_product(None, None)

        assert product.product_name == "Unknown Product"
        assert product.quantity == 1
        assert "product_id" in missing

    def test_parse_metadata(self):
        """Test parsing metadata."""
        parser = DataParser()
        metadata = parser.parse_metadata(
            source_farm="Farm-001",
            destination="Market-X",
            temperature=5.0,
            humidity=85.0,
        )

        assert metadata.source_farm == "Farm-001"
        assert metadata.destination == "Market-X"
        assert metadata.temperature == 5.0
        assert metadata.humidity == 85.0


class TestDataValidator:
    """Test data validation functions."""

    def test_validate_valid_extraction(self):
        """Test validating a valid extraction."""
        validator = DataValidator()
        response = ExtractionResponse(
            products=[
                Product(
                    product_id="SKU-123",
                    product_name="Tomato",
                    quantity=24,
                    unit=UnitType.CRATE,
                )
            ],
            metadata=Metadata(
                source_farm="Farm-001",
                destination="Market-X",
            ),
        )

        is_valid, errors = validator.validate(response)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_missing_product_id(self):
        """Test validation with missing product ID."""
        validator = DataValidator()
        response = ExtractionResponse(
            products=[
                Product(
                    product_id="",
                    product_name="Tomato",
                    quantity=24,
                    unit=UnitType.CRATE,
                )
            ],
            metadata=Metadata(
                source_farm="Farm-001",
                destination="Market-X",
            ),
        )

        is_valid, errors = validator.validate(response)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_missing_metadata(self):
        """Test validation with missing metadata."""
        validator = DataValidator()
        response = ExtractionResponse(
            products=[
                Product(
                    product_id="SKU-123",
                    product_name="Tomato",
                    quantity=24,
                    unit=UnitType.CRATE,
                )
            ],
            metadata=Metadata(
                source_farm="",
                destination="",
            ),
        )

        is_valid, errors = validator.validate(response)
        assert is_valid is False
        assert len(errors) == 2


class TestExtractionProcessor:
    """Test extraction processor."""

    def test_process_full_extraction(self):
        """Test processing a full extraction."""
        processor = ExtractionProcessor()

        cv_result = {
            "detections": [
                {
                    "class_name": "product",
                    "condition": {"condition": "excellent", "score": 95},
                }
            ]
        }

        ocr_result = {
            "product_code": "TOM-001",
            "quantity": 24,
        }

        result = processor.process(cv_result, ocr_result, source_farm="Farm-001", destination="Market-X")

        assert "extraction" in result
        assert "is_valid" in result
        assert "processing_time_ms" in result
        assert result["extraction"].metadata.source_farm == "Farm-001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
