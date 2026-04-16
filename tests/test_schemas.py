"""
Tests for data schemas and validation.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from models.schemas import (
    UnitType,
    ConditionType,
    Product,
    Metadata,
    ExtractionResponse,
)


class TestUnitType:
    """Test UnitType enum."""

    def test_valid_units(self):
        """Test all valid unit values."""
        assert UnitType.CRATE.value == "crate"
        assert UnitType.BOX.value == "box"
        assert UnitType.KG.value == "kg"
        assert UnitType.LB.value == "lb"
        assert UnitType.PIECE.value == "piece"
        assert UnitType.CARTON.value == "carton"
        assert UnitType.PALLET.value == "pallet"


class TestConditionType:
    """Test ConditionType enum."""

    def test_valid_conditions(self):
        """Test all valid condition values."""
        assert ConditionType.EXCELLENT.value == "excellent"
        assert ConditionType.GOOD.value == "good"
        assert ConditionType.FAIR.value == "fair"
        assert ConditionType.POOR.value == "poor"
        assert ConditionType.DAMAGED.value == "damaged"


class TestProduct:
    """Test Product model."""

    def test_valid_product(self):
        """Test creating a valid product."""
        product = Product(
            product_id="SKU-123",
            product_name="Tomato",
            quantity=24,
            unit=UnitType.CRATE,
        )
        assert product.product_id == "SKU-123"
        assert product.product_name == "Tomato"
        assert product.quantity == 24
        assert product.unit == UnitType.CRATE

    def test_product_with_optional_fields(self):
        """Test product with optional fields."""
        product = Product(
            product_id="SKU-123",
            product_name="Tomato",
            quantity=24,
            unit=UnitType.CRATE,
            expiry_date=datetime.now() + timedelta(days=7),
            storage_location="Fridge A",
            condition=ConditionType.EXCELLENT,
        )
        assert product.expiry_date is not None
        assert product.storage_location == "Fridge A"
        assert product.condition == ConditionType.EXCELLENT

    def test_product_empty_id(self):
        """Test product validation with empty ID."""
        with pytest.raises(ValidationError):
            Product(
                product_id="",
                product_name="Tomato",
                quantity=24,
                unit=UnitType.CRATE,
            )

    def test_product_zero_quantity(self):
        """Test product validation with zero quantity."""
        with pytest.raises(ValidationError):
            Product(
                product_id="SKU-123",
                product_name="Tomato",
                quantity=0,
                unit=UnitType.CRATE,
            )

    def test_product_negative_quantity(self):
        """Test product validation with negative quantity."""
        with pytest.raises(ValidationError):
            Product(
                product_id="SKU-123",
                product_name="Tomato",
                quantity=-5,
                unit=UnitType.CRATE,
            )

    def test_product_too_large_quantity(self):
        """Test product validation with excessive quantity."""
        with pytest.raises(ValidationError):
            Product(
                product_id="SKU-123",
                product_name="Tomato",
                quantity=100000,
                unit=UnitType.CRATE,
            )


class TestMetadata:
    """Test Metadata model."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = Metadata(
            source_farm="Farm-001",
            destination="Market-X",
            temperature=5.0,
            humidity=85.0,
        )
        assert metadata.source_farm == "Farm-001"
        assert metadata.destination == "Market-X"
        assert metadata.temperature == 5.0
        assert metadata.humidity == 85.0

    def test_metadata_required_fields_only(self):
        """Test metadata with only required fields."""
        metadata = Metadata(
            source_farm="Farm-001",
            destination="Market-X",
        )
        assert metadata.source_farm == "Farm-001"
        assert metadata.destination == "Market-X"
        assert metadata.temperature is None
        assert metadata.humidity is None

    def test_metadata_invalid_temperature(self):
        """Test metadata validation with invalid temperature."""
        with pytest.raises(ValidationError):
            Metadata(
                source_farm="Farm-001",
                destination="Market-X",
                temperature=-50.0,  # Below -40
            )

    def test_metadata_invalid_humidity(self):
        """Test metadata validation with invalid humidity."""
        with pytest.raises(ValidationError):
            Metadata(
                source_farm="Farm-001",
                destination="Market-X",
                humidity=150.0,  # Above 100
            )


class TestExtractionResponse:
    """Test ExtractionResponse model."""

    def test_valid_extraction(self):
        """Test creating a valid extraction response."""
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
        assert len(response.products) == 1
        assert response.missing_fields == []
        assert response.low_confidence_fields == []

    def test_extraction_with_missing_fields(self):
        """Test extraction response with missing fields."""
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
            missing_fields=["expiry_date", "condition"],
        )
        assert "expiry_date" in response.missing_fields
        assert "condition" in response.missing_fields

    def test_extraction_multiple_products(self):
        """Test extraction response with multiple products."""
        response = ExtractionResponse(
            products=[
                Product(
                    product_id="SKU-001",
                    product_name="Tomato",
                    quantity=24,
                    unit=UnitType.CRATE,
                ),
                Product(
                    product_id="SKU-002",
                    product_name="Lettuce",
                    quantity=12,
                    unit=UnitType.BOX,
                ),
            ],
            metadata=Metadata(
                source_farm="Farm-001",
                destination="Market-X",
            ),
        )
        assert len(response.products) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
