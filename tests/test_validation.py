"""Tests for nitro.validation — Enhanced request validation module.

Coverage:
- ValidationResult (is_valid, errors, data, formatting)
- validate_entity_data: basic, partial, type coercion, required fields
- @field_validator: single field, multiple fields, inheritance
- @model_validator: cross-field rules
- validate_request: dict, Sanic-style, Flask-style, raw body, empty
- Error formatting: to_json_errors, to_form_errors, first_error
- Edge cases: unknown fields, empty input, bad types
"""

from __future__ import annotations

import json
from typing import Optional

import pytest
from pydantic import BaseModel, Field

from nitro.validation import (
    ValidationResult,
    field_validator,
    model_validator,
    validate_entity_data,
    validate_request,
)
from nitro.validation.decorators import get_field_validators, get_model_validators


# ================================================================== #
# Test Models
# ================================================================== #


class SimpleModel(BaseModel):
    """Minimal model with a required and an optional field."""
    name: str
    age: int = 0


class ProductModel(BaseModel):
    """Richer model with custom validators."""
    name: str
    price: float
    category: str = "general"
    description: Optional[str] = None

    @field_validator("price")
    def price_positive(cls, value, field_name):
        if value <= 0:
            raise ValueError("Price must be greater than zero")

    @field_validator("name")
    def name_not_blank(cls, value, field_name):
        if not value or not str(value).strip():
            raise ValueError("Name cannot be blank")


class DateRangeModel(BaseModel):
    """Model with a cross-field model_validator."""
    start: str
    end: str

    @model_validator
    def end_after_start(cls, data):
        start = data.get("start", "")
        end = data.get("end", "")
        if start and end and end <= start:
            raise ValueError("end must be after start")


class MultiFieldValidatorModel(BaseModel):
    """Model where one validator handles multiple fields."""
    tag1: str = ""
    tag2: str = ""

    @field_validator("tag1", "tag2")
    def no_spaces_in_tags(cls, value, field_name):
        if " " in str(value):
            raise ValueError(f"{field_name} must not contain spaces")


class InheritedModel(ProductModel):
    """Subclass inheriting parent validators."""
    stock: int = 0


class MultiValidatorModel(BaseModel):
    """Field with two different validators applied in sequence."""
    username: str = ""

    @field_validator("username")
    def username_not_empty(cls, value, field_name):
        if not value:
            raise ValueError("username is required")

    @field_validator("username")
    def username_min_length(cls, value, field_name):
        if len(value) < 3:
            raise ValueError("username must be at least 3 characters")


# ================================================================== #
# ValidationResult
# ================================================================== #


class TestValidationResult:
    def test_valid_result(self):
        r = ValidationResult(errors={}, data={"name": "Alice", "age": 30})
        assert r.is_valid is True
        assert r.data == {"name": "Alice", "age": 30}
        assert r.errors == {}

    def test_invalid_result_clears_data(self):
        r = ValidationResult(errors={"name": ["too short"]}, data={"name": "x"})
        assert r.is_valid is False
        assert r.data is None

    def test_bool_truthy_when_valid(self):
        r = ValidationResult(errors={}, data={})
        assert bool(r) is True

    def test_bool_falsy_when_invalid(self):
        r = ValidationResult(errors={"age": ["must be positive"]}, data=None)
        assert bool(r) is False

    def test_to_json_errors_valid(self):
        r = ValidationResult(errors={}, data={"x": 1})
        payload = r.to_json_errors()
        assert payload["valid"] is True
        assert payload["errors"] == {}

    def test_to_json_errors_invalid(self):
        r = ValidationResult(errors={"price": ["Must be > 0"], "__all__": ["cross error"]}, data=None)
        payload = r.to_json_errors()
        assert payload["valid"] is False
        assert "price" in payload["errors"]
        assert "__all__" in payload["errors"]

    def test_to_form_errors_returns_first_message(self):
        r = ValidationResult(errors={"price": ["err1", "err2"]}, data=None)
        form = r.to_form_errors()
        assert form["price"] == "err1"

    def test_to_form_errors_flat_dict(self):
        r = ValidationResult(errors={"a": ["e1"], "b": ["e2"]}, data=None)
        form = r.to_form_errors()
        assert set(form.keys()) == {"a", "b"}

    def test_first_error_found(self):
        r = ValidationResult(errors={"name": ["too short", "invalid"]}, data=None)
        assert r.first_error("name") == "too short"

    def test_first_error_missing_field(self):
        r = ValidationResult(errors={}, data={})
        assert r.first_error("nonexistent") is None

    def test_to_json_errors_is_json_serialisable(self):
        r = ValidationResult(errors={"x": ["bad"]}, data=None)
        # Should not raise
        json.dumps(r.to_json_errors())


# ================================================================== #
# validate_entity_data — basic
# ================================================================== #


class TestValidateEntityDataBasic:
    def test_valid_data(self):
        r = validate_entity_data(SimpleModel, {"name": "Alice", "age": 25})
        assert r.is_valid
        assert r.data["name"] == "Alice"
        assert r.data["age"] == 25

    def test_missing_required_field(self):
        r = validate_entity_data(SimpleModel, {"age": 25})
        assert not r.is_valid
        assert "name" in r.errors

    def test_wrong_type_coercion(self):
        # Pydantic v2 coerces "30" to int
        r = validate_entity_data(SimpleModel, {"name": "Bob", "age": "30"})
        assert r.is_valid
        assert r.data["age"] == 30

    def test_wrong_type_fails(self):
        r = validate_entity_data(SimpleModel, {"name": "Bob", "age": "not-a-number"})
        assert not r.is_valid
        assert "age" in r.errors

    def test_default_field_not_required(self):
        r = validate_entity_data(SimpleModel, {"name": "Charlie"})
        assert r.is_valid
        assert r.data["age"] == 0

    def test_extra_fields_ignored(self):
        # Pydantic by default ignores extra fields
        r = validate_entity_data(SimpleModel, {"name": "Dave", "age": 1, "extra": "x"})
        assert r.is_valid

    def test_empty_dict_missing_required(self):
        r = validate_entity_data(SimpleModel, {})
        assert not r.is_valid
        assert "name" in r.errors

    def test_returns_all_errors_at_once(self):
        """Both name and age errors collected in one pass."""
        r = validate_entity_data(SimpleModel, {"age": "bad"})
        assert not r.is_valid
        assert "name" in r.errors
        assert "age" in r.errors


# ================================================================== #
# validate_entity_data — partial
# ================================================================== #


class TestValidateEntityDataPartial:
    def test_partial_valid_subset(self):
        r = validate_entity_data(SimpleModel, {"age": 10}, partial=True)
        assert r.is_valid
        assert r.data == {"age": 10}

    def test_partial_missing_required_is_ok(self):
        r = validate_entity_data(SimpleModel, {}, partial=True)
        assert r.is_valid
        assert r.data == {}

    def test_partial_wrong_type_fails(self):
        r = validate_entity_data(SimpleModel, {"age": "notanint"}, partial=True)
        assert not r.is_valid
        assert "age" in r.errors

    def test_partial_valid_with_multiple_fields(self):
        r = validate_entity_data(SimpleModel, {"name": "Eve", "age": 5}, partial=True)
        assert r.is_valid
        assert r.data["name"] == "Eve"

    def test_partial_ignores_unknown_fields(self):
        r = validate_entity_data(SimpleModel, {"nonexistent": "x"}, partial=True)
        assert r.is_valid
        assert r.data == {}


# ================================================================== #
# @field_validator
# ================================================================== #


class TestFieldValidator:
    def test_custom_validator_passes(self):
        r = validate_entity_data(ProductModel, {"name": "Widget", "price": 9.99})
        assert r.is_valid

    def test_custom_validator_fails_price(self):
        r = validate_entity_data(ProductModel, {"name": "Widget", "price": -1.0})
        assert not r.is_valid
        assert "price" in r.errors
        assert "greater than zero" in r.errors["price"][0]

    def test_custom_validator_fails_name_blank(self):
        r = validate_entity_data(ProductModel, {"name": "  ", "price": 5.0})
        assert not r.is_valid
        assert "name" in r.errors

    def test_multiple_custom_errors_collected(self):
        r = validate_entity_data(ProductModel, {"name": "", "price": 0.0})
        assert not r.is_valid
        # Both name and price should have errors
        assert "name" in r.errors
        assert "price" in r.errors

    def test_field_validator_on_multiple_fields(self):
        r = validate_entity_data(MultiFieldValidatorModel, {"tag1": "bad tag", "tag2": "ok"})
        assert not r.is_valid
        assert "tag1" in r.errors
        assert "tag2" not in r.errors

    def test_field_validator_both_fields_fail(self):
        r = validate_entity_data(MultiFieldValidatorModel, {"tag1": "bad one", "tag2": "bad two"})
        assert not r.is_valid
        assert "tag1" in r.errors
        assert "tag2" in r.errors

    def test_multiple_validators_on_same_field(self):
        """Two @field_validator decorators targeting the same field should both run."""
        r = validate_entity_data(MultiValidatorModel, {"username": "ab"})
        assert not r.is_valid
        assert "username" in r.errors
        # Should have the min-length error
        assert any("3 characters" in msg for msg in r.errors["username"])

    def test_multiple_validators_empty_fails_first(self):
        r = validate_entity_data(MultiValidatorModel, {"username": ""})
        assert not r.is_valid
        assert "username" in r.errors


# ================================================================== #
# Decorator introspection helpers
# ================================================================== #


class TestDecoratorIntrospection:
    def test_get_field_validators_finds_validators(self):
        validators = get_field_validators(ProductModel)
        assert "price" in validators
        assert "name" in validators
        assert len(validators["price"]) >= 1

    def test_get_model_validators_finds_validators(self):
        validators = get_model_validators(DateRangeModel)
        assert len(validators) >= 1

    def test_inherited_field_validators(self):
        """Subclass inherits field validators from parent."""
        validators = get_field_validators(InheritedModel)
        assert "price" in validators
        assert "name" in validators

    def test_no_validators_on_plain_model(self):
        validators = get_field_validators(SimpleModel)
        assert validators == {}

    def test_no_model_validators_on_plain_model(self):
        validators = get_model_validators(SimpleModel)
        assert validators == []


# ================================================================== #
# @model_validator (cross-field)
# ================================================================== #


class TestModelValidator:
    def test_valid_date_range(self):
        r = validate_entity_data(DateRangeModel, {"start": "2024-01-01", "end": "2024-12-31"})
        assert r.is_valid

    def test_invalid_date_range(self):
        r = validate_entity_data(DateRangeModel, {"start": "2024-12-31", "end": "2024-01-01"})
        assert not r.is_valid
        assert "__all__" in r.errors
        assert "after start" in r.errors["__all__"][0]

    def test_equal_dates_fail(self):
        r = validate_entity_data(DateRangeModel, {"start": "2024-06-01", "end": "2024-06-01"})
        assert not r.is_valid
        assert "__all__" in r.errors

    def test_model_validator_in_form_errors(self):
        r = validate_entity_data(DateRangeModel, {"start": "2024-12-31", "end": "2024-01-01"})
        form = r.to_form_errors()
        assert "__all__" in form


# ================================================================== #
# Inherited validators
# ================================================================== #


class TestInheritance:
    def test_inherited_price_validator(self):
        r = validate_entity_data(InheritedModel, {"name": "Widget", "price": -5.0})
        assert not r.is_valid
        assert "price" in r.errors

    def test_inherited_name_validator(self):
        r = validate_entity_data(InheritedModel, {"name": "", "price": 9.99})
        assert not r.is_valid
        assert "name" in r.errors

    def test_inherited_valid(self):
        r = validate_entity_data(InheritedModel, {"name": "Widget", "price": 9.99, "stock": 5})
        assert r.is_valid


# ================================================================== #
# validate_request — framework-agnostic extraction
# ================================================================== #


class _SanicRequest:
    """Minimal Sanic-style request stub."""
    def __init__(self, data: dict):
        self.json = data


class _FlaskRequest:
    """Minimal Flask-style request stub."""
    def __init__(self, data: dict):
        self._data = data

    def get_json(self):
        return self._data


class _RawBodyRequest:
    """Request with raw bytes body (like Starlette)."""
    def __init__(self, data: dict):
        self.body = json.dumps(data).encode("utf-8")


class _CallableJsonRequest:
    """Request where .json is a callable."""
    def __init__(self, data: dict):
        self._data = data

    def json(self):
        return self._data


class TestValidateRequest:
    def test_dict_directly(self):
        r = validate_request(SimpleModel, {"name": "Alice", "age": 5})
        assert r.is_valid

    def test_sanic_style_json_attr(self):
        req = _SanicRequest({"name": "Alice", "age": 5})
        r = validate_request(SimpleModel, req)
        assert r.is_valid

    def test_flask_style_get_json(self):
        req = _FlaskRequest({"name": "Bob", "age": 10})
        r = validate_request(SimpleModel, req)
        assert r.is_valid

    def test_raw_bytes_body(self):
        req = _RawBodyRequest({"name": "Carol", "age": 3})
        r = validate_request(SimpleModel, req)
        assert r.is_valid

    def test_empty_request_fails_required(self):
        class _EmptyRequest:
            json = None
        r = validate_request(SimpleModel, _EmptyRequest())
        assert not r.is_valid
        assert "name" in r.errors

    def test_partial_via_validate_request(self):
        req = _SanicRequest({"age": 7})
        r = validate_request(SimpleModel, req, partial=True)
        assert r.is_valid
        assert r.data == {"age": 7}

    def test_invalid_json_body_returns_empty(self):
        class _BadBody:
            body = b"not json at all"
        r = validate_request(SimpleModel, _BadBody())
        assert not r.is_valid

    def test_validation_errors_propagate_from_request(self):
        req = _SanicRequest({"name": "Widget", "price": -1.0})
        r = validate_request(ProductModel, req)
        assert not r.is_valid
        assert "price" in r.errors


# ================================================================== #
# Edge cases
# ================================================================== #


class TestEdgeCases:
    def test_none_value_for_optional_field(self):
        r = validate_entity_data(ProductModel, {"name": "X", "price": 1.0, "description": None})
        assert r.is_valid
        assert r.data["description"] is None

    def test_zero_price_triggers_custom_validator(self):
        r = validate_entity_data(ProductModel, {"name": "X", "price": 0.0})
        assert not r.is_valid
        assert "price" in r.errors

    def test_float_coercion_from_string(self):
        r = validate_entity_data(ProductModel, {"name": "X", "price": "9.99"})
        assert r.is_valid
        assert r.data["price"] == 9.99

    def test_boolean_coercion(self):
        class BoolModel(BaseModel):
            active: bool = True
        r = validate_entity_data(BoolModel, {"active": 1})
        assert r.is_valid
        assert r.data["active"] is True

    def test_optional_field_absent_is_ok(self):
        r = validate_entity_data(ProductModel, {"name": "Y", "price": 2.0})
        assert r.is_valid
        assert r.data["description"] is None

    def test_nested_loc_error(self):
        """Pydantic errors with nested loc tuples are handled gracefully."""
        # Force an error on a plain model; this exercises the _full_validate path
        r = validate_entity_data(SimpleModel, {"name": 123, "age": "bad"})
        # age fails — name might coerce from int (pydantic does that for str)
        # We just care no exception is raised and errors is a dict
        assert isinstance(r.errors, dict)

    def test_result_errors_are_lists(self):
        r = validate_entity_data(SimpleModel, {})
        for field, msgs in r.errors.items():
            assert isinstance(msgs, list)
            assert all(isinstance(m, str) for m in msgs)

    def test_validate_entity_data_with_entity_subclass(self):
        """Works with Entity subclasses (SQLModel based) as well as plain BaseModels."""
        from nitro.domain.entities.base_entity import Entity
        from sqlmodel import Field as SQField

        class TinyEntity(Entity, table=True):
            label: str = ""

        r = validate_entity_data(TinyEntity, {"label": "hello"})
        # Entity has auto id, label is optional with default ""
        assert r.is_valid
