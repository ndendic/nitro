"""
Tests for nitro.html.forms — Pydantic validation → inline HTML error helpers.

Covers: extract_errors, error_message, form_errors_fragment, @validated decorator.
"""

import pytest
from pydantic import BaseModel, ValidationError, field_validator

from nitro.html.forms import (
    error_message,
    extract_errors,
    form_errors_fragment,
    validated,
)


# ---------------------------------------------------------------------------
# Test Pydantic models
# ---------------------------------------------------------------------------


class PostForm(BaseModel):
    title: str
    content: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("content")
    @classmethod
    def content_min_length(cls, v):
        if len(v) < 10:
            raise ValueError("Content must be at least 10 characters")
        return v


class SimpleForm(BaseModel):
    name: str
    age: int


# ---------------------------------------------------------------------------
# extract_errors
# ---------------------------------------------------------------------------


class TestExtractErrors:
    def test_single_field_error(self):
        try:
            PostForm(title="", content="Long enough content here")
        except ValidationError as e:
            errors = extract_errors(e)
            assert "title" in errors
            assert "content" not in errors

    def test_multiple_field_errors(self):
        try:
            PostForm(title="", content="short")
        except ValidationError as e:
            errors = extract_errors(e)
            assert "title" in errors
            assert "content" in errors

    def test_type_error_extraction(self):
        try:
            SimpleForm(name="Alice", age="not-a-number")
        except ValidationError as e:
            errors = extract_errors(e)
            assert "age" in errors

    def test_keeps_first_error_per_field(self):
        """If a field has multiple errors, only the first is kept."""
        try:
            PostForm(title="", content="short")
        except ValidationError as e:
            errors = extract_errors(e)
            # Each field should have exactly one error message
            assert isinstance(errors["title"], str)
            assert isinstance(errors["content"], str)

    def test_missing_field_error(self):
        try:
            PostForm()  # type: ignore
        except ValidationError as e:
            errors = extract_errors(e)
            assert "title" in errors
            assert "content" in errors


# ---------------------------------------------------------------------------
# error_message
# ---------------------------------------------------------------------------


class TestErrorMessage:
    def test_returns_html_when_error_present(self):
        errors = {"title": "Title cannot be empty"}
        result = error_message("title", errors)
        assert "Title cannot be empty" in result
        assert "<p" in result
        assert "error-title" in result

    def test_returns_empty_when_no_error(self):
        errors = {"title": "Some error"}
        result = error_message("content", errors)
        assert result == ""

    def test_returns_empty_for_empty_errors(self):
        result = error_message("anything", {})
        assert result == ""

    def test_custom_css_class(self):
        errors = {"name": "Required"}
        result = error_message("name", errors, cls="text-red-500")
        assert "text-red-500" in result


# ---------------------------------------------------------------------------
# form_errors_fragment
# ---------------------------------------------------------------------------


class TestFormErrorsFragment:
    def test_calls_render_form_with_errors(self):
        calls = []

        def render_form(data, errors):
            calls.append((data, errors))
            return f"<form>{errors}</form>"

        try:
            PostForm(title="", content="short")
        except ValidationError as e:
            result = form_errors_fragment(e, {"title": "", "content": "short"}, render_form)
            assert len(calls) == 1
            data, errors = calls[0]
            assert data == {"title": "", "content": "short"}
            assert "title" in errors
            assert "content" in errors

    def test_passes_through_render_form_return(self):
        def render_form(data, errors):
            return "<div>rendered</div>"

        try:
            PostForm(title="", content="x")
        except ValidationError as e:
            result = form_errors_fragment(e, {}, render_form)
            assert result == "<div>rendered</div>"


# ---------------------------------------------------------------------------
# @validated decorator
# ---------------------------------------------------------------------------


class TestValidatedDecorator:
    @pytest.mark.asyncio
    async def test_valid_data_passes_form(self):
        @validated(PostForm)
        async def create(request, form=None, form_errors=None, **kwargs):
            return {"form": form, "errors": form_errors}

        req = object()
        result = await create(req, title="Hello World", content="This is long enough content")
        assert result["form"] is not None
        assert isinstance(result["form"], PostForm)
        assert result["form"].title == "Hello World"
        assert result["errors"] is None

    @pytest.mark.asyncio
    async def test_invalid_data_provides_errors(self):
        @validated(PostForm)
        async def create(request, form=None, form_errors=None, **kwargs):
            return {"form": form, "errors": form_errors}

        req = object()
        result = await create(req, title="", content="short")
        assert result["form"] is None
        assert result["errors"] is not None
        assert "title" in result["errors"]
        assert "content" in result["errors"]

    @pytest.mark.asyncio
    async def test_validated_strips_special_kwargs(self):
        """Signals dict should not include 'request' in form validation."""

        @validated(SimpleForm)
        async def handler(request, form=None, form_errors=None, **kwargs):
            return {"form": form, "errors": form_errors}

        req = object()
        result = await handler(req, name="Alice", age=30)
        assert result["form"] is not None
        assert result["form"].name == "Alice"
        assert result["form"].age == 30
