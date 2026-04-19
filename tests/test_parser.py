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

   # test_validate_missing_product_id — replace the whole test body:
def test_validate_missing_product_id(self):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Product(product_id="", product_name="Tomato", quantity=24, unit=UnitType.CRATE)

# test_validate_missing_metadata — replace:
def test_validate_missing_metadata(self):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Metadata(source_farm="", destination="")

# test_validate_empty_product_id — replace:
def test_validate_empty_product_id(self):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Product(product_id="   ", product_name="Test", quantity=10, unit=UnitType.CRATE)

# test_validate_bounds_below_minimum — change e["code"] to e.code:
assert any(e.code == "BELOW_MINIMUM" for e in errors)

# test_validate_bounds_above_maximum — change e["code"] to e.code:
assert any(e.code == "EXCEEDS_MAXIMUM" for e in errors)


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


class TestFieldValidatorEdgeCases:
    """Test edge cases for field validation."""

    def test_validate_date_past_date_returns_none(self):
        """Test that past dates return None."""
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        result = FieldValidator.validate_date(past_date)
        assert result is None

    def test_validate_date_different_formats(self):
        """Test validating dates in different formats."""
        assert FieldValidator.validate_date("2026-12-25") is not None
        assert FieldValidator.validate_date("25-12-2026") is not None
        assert FieldValidator.validate_date("12/25/2026") is not None

    def test_validate_date_invalid_string(self):
        """Test validating completely invalid date string."""
        assert FieldValidator.validate_date("not-a-date") is None
        assert FieldValidator.validate_date("") is None
        assert FieldValidator.validate_date("2026-13-45") is None

    def test_validate_quantity_string_input(self):
        """Test validating quantity from string input."""
        assert FieldValidator.validate_quantity("24") == 24
        assert FieldValidator.validate_quantity("100") == 100

    def test_validate_quantity_edge_bounds(self):
        """Test quantity validation at boundaries."""
        assert FieldValidator.validate_quantity(1) == 1
        assert FieldValidator.validate_quantity(99999) == 99999
        assert FieldValidator.validate_quantity(0) is None
        assert FieldValidator.validate_quantity(100000) is None

    def test_validate_unit_case_insensitive(self):
        """Test that unit validation is case insensitive."""
        assert FieldValidator.validate_unit("CRATE") == UnitType.CRATE
        assert FieldValidator.validate_unit("Crate") == UnitType.CRATE
        assert FieldValidator.validate_unit("kg") == UnitType.KG
        assert FieldValidator.validate_unit("KG") == UnitType.KG

    def test_validate_condition_case_insensitive(self):
        """Test that condition validation is case insensitive."""
        assert FieldValidator.validate_condition("EXCELLENT") == ConditionType.EXCELLENT
        assert FieldValidator.validate_condition("Good") == ConditionType.GOOD


class TestDataParserEdgeCases:
    """Test edge cases for data parsing."""

    def test_parse_product_with_empty_cv_detection(self):
        """Test parsing product with empty CV detection."""
        parser = DataParser()
        product, missing = parser.parse_product(
            cv_detection={},
            ocr_result={"product_code": "TEST-001", "quantity": 10}
        )
        assert product.product_id == "TEST-001"
        assert product.quantity == 10

    def test_parse_product_with_ocr_only(self):
        """Test parsing product with only OCR data."""
        parser = DataParser()
        product, missing = parser.parse_product(
            cv_detection=None,
            ocr_result={"product_code": "OCR-123"}
        )
        assert product.product_id == "OCR-123"
        assert "product_name" not in missing

    def test_parse_product_auto_generates_id_when_missing(self):
        """Test that missing product ID is auto-generated."""
        parser = DataParser()
        product, missing = parser.parse_product(
            cv_detection={"class_name": "tomato"},
            ocr_result={}
        )
        assert product.product_id.startswith("SKU-")
        assert "product_id" in missing

    def test_parse_metadata_with_all_fields(self):
        """Test parsing metadata with all fields provided."""
        parser = DataParser()
        metadata = parser.parse_metadata(
            source_farm="Farm-ABC",
            destination="Warehouse-1",
            temperature=4.5,
            humidity=80.0
        )
        assert metadata.source_farm == "Farm-ABC"
        assert metadata.temperature == 4.5
        assert metadata.humidity == 80.0

    def test_parse_metadata_with_defaults(self):
        """Test parsing metadata with minimal fields."""
        parser = DataParser()
        metadata = parser.parse_metadata(
            source_farm="Farm-X",
            destination="Dest-Y"
        )
        assert metadata.source_farm == "Farm-X"
        assert metadata.temperature is None
        assert metadata.humidity is None


class TestExtractionProcessorEdgeCases:
    """Test edge cases for extraction processor."""

    def test_process_with_empty_cv_result(self):
        """Test processing with empty CV result."""
        processor = ExtractionProcessor()
        result = processor.process(
            cv_result={},
            ocr_result={},
            source_farm="TestFarm",
            destination="TestDest"
        )
        assert "extraction" in result
        assert result["extraction"].products is not None

    def test_process_with_full_cv_and_ocr(self):
        """Test processing with complete CV and OCR data."""
        processor = ExtractionProcessor()

        cv_result = {
            "detections": [
                {
                    "class_name": "crate",
                    "condition": {"condition": "good", "score": 85}
                }
            ]
        }

        ocr_result = {
            "product_code": "FULL-001",
            "quantity": 50,
            "expiry_date": {"parsed": "2026-12-31", "confidence": "high"}
        }

        result = processor.process(
            cv_result=cv_result,
            ocr_result=ocr_result,
            source_farm="Farm-Z",
            destination="Warehouse-A"
        )

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert result["extraction"].products[0].product_id == "FULL-001"
        assert result["extraction"].products[0].quantity == 50

    def test_process_tracking_time(self):
        """Test that processing time is tracked."""
        processor = ExtractionProcessor()
        result = processor.process(
            cv_result={},
            ocr_result={},
            source_farm="Farm",
            destination="Dest"
        )
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] >= 0

    def test_process_with_missing_fields_flagged(self):
        """Test that missing fields are properly flagged."""
        processor = ExtractionProcessor()

        cv_result = {"detections": [{"class_name": "product"}]}
        ocr_result = {}  # No OCR data

        result = processor.process(
            cv_result=cv_result,
            ocr_result=ocr_result,
            source_farm="Farm",
            destination="Dest"
        )

        assert "product_id" in result["extraction"].missing_fields


class TestDataValidatorEdgeCases:
    """Test edge cases for data validator."""

    def test_validate_empty_product_id(self):
        """Test validation catches empty product ID."""
        from models.schemas import Product, Metadata, ExtractionResponse

        validator = DataValidator()
        response = ExtractionResponse(
            products=[
                Product(
                    product_id="   ",
                    product_name="Test",
                    quantity=10,
                    unit=UnitType.CRATE
                )
            ],
            metadata=Metadata(source_farm="F", destination="D")
        )

        is_valid, errors = validator.validate(response)
        # Empty/whitespace ID should fail validation
        assert is_valid is False

    def test_validate_bounds_below_minimum(self):
        """Test bounds validation for below minimum products."""
        from models.schemas import Product, Metadata, ExtractionResponse

        validator = DataValidator()
        response = ExtractionResponse(
            products=[],
            metadata=Metadata(source_farm="F", destination="D")
        )

        is_valid, errors = validator.validate_bounds(response, min_products=1)
        assert is_valid is False
        assert any(e["code"] == "BELOW_MINIMUM" for e in errors)

    def test_validate_bounds_above_maximum(self):
        """Test bounds validation for above maximum products."""
        from models.schemas import Product, Metadata, ExtractionResponse

        validator = DataValidator()
        products = [
            Product(
                product_id=f"PROD-{i}",
                product_name=f"Product {i}",
                quantity=1,
                unit=UnitType.PIECE
            )
            for i in range(10)
        ]
        response = ExtractionResponse(
            products=products,
            metadata=Metadata(source_farm="F", destination="D")
        )

        is_valid, errors = validator.validate_bounds(response, max_products=5)
        assert is_valid is False
        assert any(e["code"] == "EXCEEDS_MAXIMUM" for e in errors)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_parse_extraction_quick_function(self):
        """Test the parse_extraction convenience function."""
        from utils.parser import parse_extraction

        result = parse_extraction(
            cv_result={"detections": [{"class_name": "tomato"}]},
            ocr_result={"product_code": "CONV-001"},
            source_farm="Farm",
            destination="Dest"
        )

        assert result.products[0].product_id == "CONV-001"

    def test_validate_extraction_quick_function(self):
        """Test the validate_extraction convenience function."""
        from utils.parser import validate_extraction
        from models.schemas import Product, Metadata, ExtractionResponse

        response = ExtractionResponse(
            products=[
                Product(
                    product_id="VAL-001",
                    product_name="Valid Product",
                    quantity=5,
                    unit=UnitType.BOX
                )
            ],
            metadata=Metadata(source_farm="F", destination="D")
        )

        is_valid, errors = validate_extraction(response)
        assert is_valid is True
        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
