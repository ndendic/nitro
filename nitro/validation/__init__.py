"""nitro.validation — Enhanced request validation for Entity classes.

Provides:
- ValidationResult    : Result object with .is_valid, .errors, .data
- validate_entity_data: Validate a dict against an Entity's Pydantic schema
- field_validator     : Decorator for adding custom field-level validation rules
- model_validator     : Decorator for cross-field (model-level) validation rules
- validate_request    : Extract + validate data from a framework-agnostic request

Quick start::

    from nitro.validation import validate_entity_data, field_validator, ValidationResult

    class Product(Entity, table=True):
        name: str
        price: float
        category: str = "general"

        @field_validator("price")
        def price_must_be_positive(cls, value, field_name):
            if value <= 0:
                raise ValueError("Price must be greater than zero")

        @field_validator("name")
        def name_not_empty(cls, value, field_name):
            if not value or not value.strip():
                raise ValueError("Name cannot be blank")

    result = validate_entity_data(Product, {"name": "Widget", "price": 9.99})
    if result.is_valid:
        product = Product(**result.data)
    else:
        print(result.errors)   # {"price": ["Price must be greater than zero"]}

Error formatting::

    result.to_json_errors()   # JSON-friendly dict for API responses
    result.to_form_errors()   # HTML-friendly dict for form field highlighting

Partial validation (for PATCH/update requests)::

    result = validate_entity_data(Product, {"price": -5}, partial=True)
    # Only validates provided fields; missing required fields are OK

Cross-field validation::

    class DateRange(Entity, table=True):
        start: str
        end: str

        @model_validator
        def end_after_start(cls, data):
            if data.get("end") <= data.get("start"):
                raise ValueError("end must be after start")
"""

from __future__ import annotations

from .core import (
    ValidationResult,
    validate_entity_data,
    validate_request,
)
from .decorators import field_validator, model_validator

__all__ = [
    "ValidationResult",
    "validate_entity_data",
    "validate_request",
    "field_validator",
    "model_validator",
]
