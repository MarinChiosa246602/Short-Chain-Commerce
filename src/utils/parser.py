"""
Data Parser and Validator for logistics data extraction.

This module handles:
- Converting CV + OCR outputs to structured JSON
- Validation of extracted fields
- Error handling and missing field detection
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from models.schemas import (
    ExtractionResponse,
    Product,
    Metadata,
    UnitType,
    ConditionType,
    ValidationErrorDetail,
)


class FieldValidator:
    """Validate individual fields."""

    @staticmethod
    def validate_date(date_str: str) -> Optional[datetime]:
        """
        Validate and parse a date string.

        Args:
            date_str: Date string to validate

        Returns:
            Parsed datetime or None if invalid
        """
        date_formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                if parsed > datetime.now():
                    return parsed
            except ValueError:
                continue

        return None

    @staticmethod
    def validate_quantity(value: Any) -> Optional[int]:
        """
        Validate quantity value.

        Args:
            value: Value to validate

        Returns:
            Validated quantity or None
        """
        try:
            qty = int(value)
            if 1 <= qty <= 99999:
                return qty
        except (ValueError, TypeError):
            pass
        return None

    @staticmethod
    def validate_unit(value: str) -> Optional[UnitType]:
        """
        Validate and map unit string to enum.

        Args:
            value: Unit string

        Returns:
            UnitType enum or None
        """
        unit_mapping = {
            "crate": UnitType.CRATE,
            "box": UnitType.BOX,
            "kg": UnitType.KG,
            "kilogram": UnitType.KG,
            "kilograms": UnitType.KG,
            "lb": UnitType.LB,
            "lbs": UnitType.LB,
            "pound": UnitType.LB,
            "pounds": UnitType.LB,
            "piece": UnitType.PIECE,
            "pieces": UnitType.PIECE,
            "carton": UnitType.CARTON,
            "pallet": UnitType.PALLET,
        }
        return unit_mapping.get(value.lower().strip())

    @staticmethod
    def validate_condition(value: str) -> Optional[ConditionType]:
        """
        Validate and map condition string to enum.

        Args:
            value: Condition string

        Returns:
            ConditionType enum or None
        """
        condition_mapping = {
            "excellent": ConditionType.EXCELLENT,
            "good": ConditionType.GOOD,
            "fair": ConditionType.FAIR,
            "poor": ConditionType.POOR,
            "damaged": ConditionType.DAMAGED,
        }
        return condition_mapping.get(value.lower().strip())


class DataParser:
    """Parse CV and OCR outputs into structured data."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the parser.

        Args:
            config: Parser configuration
        """
        self.config = config or {}
        self.validator = FieldValidator()

    def parse_product(
        self,
        cv_detection: Optional[Dict[str, Any]] = None,
        ocr_result: Optional[Dict[str, Any]] = None,
        default_unit: str = "piece",
    ) -> tuple[Optional[Product], List[str]]:
        """
        Parse a product from CV and OCR results.

        Args:
            cv_detection: Object detection result
            ocr_result: OCR extraction result
            default_unit: Default unit if not detected

        Returns:
            Tuple of (Product, missing_fields)
        """
        missing_fields = []

        # Extract product ID
        product_id = None
        if ocr_result and ocr_result.get("product_code"):
            product_id = ocr_result["product_code"]

        if not product_id:
            missing_fields.append("product_id")
            product_id = f"SKU-{uuid4().hex[:8].upper()}"  # Generate temp ID

        # Extract product name
        product_name = "Unknown Product"
        if cv_detection and cv_detection.get("class_name") != "unknown":
            product_name = cv_detection["class_name"].replace("_", " ").title()

        # Extract quantity
        quantity = 1
        if ocr_result and ocr_result.get("quantity"):
            quantity = ocr_result["quantity"]

        # Extract unit
        unit = self.validator.validate_unit(default_unit)

        # Extract expiry date
        expiry_date = None
        if ocr_result and ocr_result.get("expiry_date"):
            expiry_date_str = ocr_result["expiry_date"].get("parsed")
            if expiry_date_str:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")

        # Extract condition
        condition = None
        if cv_detection and cv_detection.get("condition"):
            cond_data = cv_detection["condition"]
            if isinstance(cond_data, dict):
                condition_str = cond_data.get("condition", "")
                condition = self.validator.validate_condition(condition_str)

        product = Product(
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit=unit or UnitType.PIECE,
            expiry_date=expiry_date,
            storage_location=None,
            condition=condition,
        )

        return product, missing_fields

    def parse_metadata(
        self,
        source_farm: Optional[str] = None,
        destination: Optional[str] = None,
        cv_result: Optional[Dict[str, Any]] = None,
        ocr_result: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
    ) -> Metadata:
        """
        Parse metadata from various sources.

        Args:
            source_farm: Source farm identifier
            destination: Destination identifier
            cv_result: CV pipeline result
            ocr_result: OCR result
            temperature: Temperature reading
            humidity: Humidity reading

        Returns:
            Metadata object
        """
        # Use provided values or defaults
        metadata = Metadata(
            source_farm=source_farm or "Unknown",
            destination=destination or "Unknown",
            temperature=temperature,
            humidity=humidity,
        )

        return metadata

    def parse_full_extraction(
        self,
        cv_result: Dict[str, Any],
        ocr_result: Dict[str, Any],
        source_farm: Optional[str] = None,
        destination: Optional[str] = None,
    ) -> ExtractionResponse:
        """
        Parse complete extraction result from CV and OCR.

        Args:
            cv_result: CV pipeline output
            ocr_result: OCR pipeline output
            source_farm: Source farm identifier
            destination: Destination identifier

        Returns:
            Structured ExtractionResponse
        """
        products = []
        all_missing_fields = []

        # Parse each detected product
        for detection in cv_result.get("detections", []):
            if detection.get("class_name") == "product" or detection.get("class_name") in ["crate", "box"]:
                product, missing = self.parse_product(
                    cv_detection=detection,
                    ocr_result=ocr_result,
                )
                products.append(product)
                all_missing_fields.extend(missing)

        # If no products detected, create a default entry
        if not products:
             default_product, missing = self.parse_product(
                cv_detection=None,
                ocr_result=ocr_result,
             )
             products.append(default_product)
             all_missing_fields.extend(missing)
             all_missing_fields.append("product_name")
             all_missing_fields.append("quantity")

        # Parse metadata
        metadata = self.parse_metadata(
            source_farm=source_farm,
            destination=destination,
            cv_result=cv_result,
            ocr_result=ocr_result,
        )

        # Get low confidence fields
        low_confidence_fields = []
        if ocr_result.get("expiry_date") and ocr_result["expiry_date"].get("confidence") == "low":
            low_confidence_fields.append("expiry_date")

        return ExtractionResponse(
            products=products,
            metadata=metadata,
            missing_fields=list(set(all_missing_fields)),
            low_confidence_fields=low_confidence_fields,
        )


class DataValidator:
    """Validate complete extraction responses."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the validator.

        Args:
            config: Validation configuration
        """
        self.config = config or {}

    def validate(self, response: ExtractionResponse) -> tuple[bool, List[ValidationErrorDetail]]:
        """
        Validate an extraction response.

        Args:
            response: ExtractionResponse to validate

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        # Validate each product
        for i, product in enumerate(response.products):
            # Check required fields
            if not product.product_id:
                errors.append(
                    ValidationErrorDetail(
                        field=f"products[{i}].product_id",
                        code="MISSING_REQUIRED",
                        message="Product ID is required",
                    )
                )

            if not product.product_name:
                errors.append(
                    ValidationErrorDetail(
                        field=f"products[{i}].product_name",
                        code="MISSING_REQUIRED",
                        message="Product name is required",
                    )
                )

            if product.quantity < 1:
                errors.append(
                    ValidationErrorDetail(
                        field=f"products[{i}].quantity",
                        code="OUT_OF_BOUNDS",
                        message="Quantity must be at least 1",
                    )
                )

        # Validate metadata
        if not response.metadata.source_farm:
            errors.append(
                ValidationErrorDetail(
                    field="metadata.source_farm",
                    code="MISSING_REQUIRED",
                    message="Source farm is required",
                )
            )

        if not response.metadata.destination:
            errors.append(
                ValidationErrorDetail(
                    field="metadata.destination",
                    code="MISSING_REQUIRED",
                    message="Destination is required",
                )
            )

        return len(errors) == 0, errors

    def validate_bounds(
        self,
        response: ExtractionResponse,
        min_products: int = 1,
        max_products: int = 100,
    ) -> tuple[bool, List[ValidationErrorDetail]]:
        """
        Validate extraction bounds.

        Args:
            response: ExtractionResponse to validate
            min_products: Minimum expected products
            max_products: Maximum expected products

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        if len(response.products) < min_products:
            errors.append(
                ValidationErrorDetail(
                    field="products",
                    code="BELOW_MINIMUM",
                    message=f"Expected at least {min_products} products, got {len(response.products)}",
                )
            )

        if len(response.products) > max_products:
            errors.append(
                ValidationErrorDetail(
                    field="products",
                    code="EXCEEDS_MAXIMUM",
                    message=f"Expected at most {max_products} products, got {len(response.products)}",
                )
            )

        return len(errors) == 0, errors


class ExtractionProcessor:
    """
    Main extraction processor.

    Combines parsing and validation for end-to-end processing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the extraction processor.

        Args:
            config: Processing configuration
        """
        self.config = config or {}
        self.parser = DataParser(config)
        self.validator = DataValidator(config)

    def process(
        self,
        cv_result: Dict[str, Any],
        ocr_result: Dict[str, Any],
        source_farm: Optional[str] = None,
        destination: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process CV and OCR results into validated extraction.

        Args:
            cv_result: CV pipeline output
            ocr_result: OCR pipeline output
            source_farm: Source farm identifier
            destination: Destination identifier

        Returns:
            Dictionary with extraction results and validation status
        """
        import time

        start_time = time.time()

        # Parse extraction
        extraction = self.parser.parse_full_extraction(
            cv_result=cv_result,
            ocr_result=ocr_result,
            source_farm=source_farm,
            destination=destination,
        )

        # Validate extraction
        is_valid, errors = self.validator.validate(extraction)

        processing_time = (time.time() - start_time) * 1000

        return {
            "extraction": extraction,
            "is_valid": is_valid,
            "errors": errors,
            "processing_time_ms": processing_time,
        }

    def parse_product_from_text(self, text: str) -> Optional[Product]:
        """
        Parse a product directly from OCR text.

        Args:
            text: Raw OCR text

        Returns:
            Parsed Product or None
        """
        # Try to extract product info from text
        lines = text.strip().split("\n")

        product_id = None
        product_name = None
        quantity = None

        for line in lines:
            line = line.strip()

            # Try to find product code
            if not product_id:
                match = re.search(r"\b([A-Z]{2,5}-?\d{3,6})\b", line, re.IGNORECASE)
                if match:
                    product_id = match.group(1)

            # Try to find quantity
            if quantity is None:
                match = re.search(r"(\d+)\s*(?:pcs?|kg|lbs?|box|crate)", line, re.IGNORECASE)
                if match:
                    quantity = int(match.group(1))

            # Product name is usually first meaningful text
            if not product_name and len(line) > 3 and len(line) < 100:
                if not any(kw in line.lower() for kw in ["exp", "best", "qty", "sku", "prod"]):
                    product_name = line

        if product_id or product_name:
            return Product(
                product_id=product_id or f"SKU-{uuid4().hex[:8].upper()}",
                product_name=product_name or "Extracted Product",
                quantity=quantity or 1,
                unit=UnitType.PIECE,
            )

        return None


# Convenience functions
def parse_extraction(
    cv_result: Dict[str, Any],
    ocr_result: Dict[str, Any],
    **kwargs,
) -> ExtractionResponse:
    """
    Quick function to parse CV and OCR results.

    Args:
        cv_result: CV pipeline output
        ocr_result: OCR pipeline output
        **kwargs: Additional arguments for source_farm, destination

    Returns:
        Parsed ExtractionResponse
    """
    processor = ExtractionProcessor()
    result = processor.process(cv_result, ocr_result, **kwargs)
    return result["extraction"]


def validate_extraction(response: ExtractionResponse) -> tuple[bool, List[ValidationErrorDetail]]:
    """
    Quick function to validate an extraction response.

    Args:
        response: ExtractionResponse to validate

    Returns:
        Tuple of (is_valid, errors)
    """
    validator = DataValidator()
    return validator.validate(response)
