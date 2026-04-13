"""
Tests for nitro.api — standardized API response formatting module.

Covers: ApiResponse (success/error/paginated/serialisation),
        PaginationMeta (computed fields), ErrorDetail,
        all ApiError subclasses, error_handler, from_pydantic_error,
        content negotiation (wants_json, negotiate, NegotiatedResponse).
"""

from __future__ import annotations

import json

import pytest
import pydantic

from nitro.api import (
    ApiResponse,
    PaginationMeta,
    ErrorDetail,
    ApiError,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    ForbiddenError,
    ConflictError,
    RateLimitError,
    error_handler,
    from_pydantic_error,
    negotiate,
    wants_json,
    json_response,
    NegotiatedResponse,
)


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


class FakeRequest:
    def __init__(self, accept: str = "application/json"):
        self.headers = {"accept": accept}


# ------------------------------------------------------------------ #
# ErrorDetail
# ------------------------------------------------------------------ #


class TestErrorDetail:
    def test_message_only(self):
        ed = ErrorDetail(message="something went wrong")
        assert ed.message == "something went wrong"
        assert ed.code is None
        assert ed.field is None

    def test_with_code_and_field(self):
        ed = ErrorDetail(message="required", code="required_field", field="email")
        assert ed.code == "required_field"
        assert ed.field == "email"


# ------------------------------------------------------------------ #
# PaginationMeta
# ------------------------------------------------------------------ #


class TestPaginationMeta:
    def test_total_pages_computed(self):
        meta = PaginationMeta(total=100, page=1, page_size=20)
        assert meta.total_pages == 5

    def test_total_pages_rounds_up(self):
        meta = PaginationMeta(total=101, page=1, page_size=20)
        assert meta.total_pages == 6

    def test_total_pages_exact_division(self):
        meta = PaginationMeta(total=40, page=2, page_size=10)
        assert meta.total_pages == 4

    def test_total_pages_zero_items(self):
        meta = PaginationMeta(total=0, page=1, page_size=10)
        assert meta.total_pages == 0

    def test_zero_page_size_gives_zero_pages(self):
        meta = PaginationMeta(total=50, page=1, page_size=0)
        assert meta.total_pages == 0

    def test_fields_preserved(self):
        meta = PaginationMeta(total=30, page=3, page_size=10)
        assert meta.total == 30
        assert meta.page == 3
        assert meta.page_size == 10


# ------------------------------------------------------------------ #
# ApiResponse — success constructor
# ------------------------------------------------------------------ #


class TestApiResponseSuccess:
    def test_success_sets_data(self):
        resp = ApiResponse.success({"id": 1})
        assert resp.data == {"id": 1}
        assert resp.success is True
        assert resp.errors is None
        assert resp.meta is None

    def test_success_with_meta(self):
        resp = ApiResponse.success([1, 2, 3], meta={"count": 3})
        assert resp.meta == {"count": 3}

    def test_success_with_none_data(self):
        resp = ApiResponse.success(None)
        assert resp.success is True
        assert resp.data is None


# ------------------------------------------------------------------ #
# ApiResponse — error constructor
# ------------------------------------------------------------------ #


class TestApiResponseError:
    def test_error_sets_success_false(self):
        resp = ApiResponse.error("Something broke")
        assert resp.success is False
        assert resp.data is None

    def test_error_creates_error_detail(self):
        resp = ApiResponse.error("Not found", code="not_found")
        assert len(resp.errors) == 1
        assert resp.errors[0].message == "Not found"
        assert resp.errors[0].code == "not_found"

    def test_error_with_details(self):
        details = [ErrorDetail(message="email invalid", field="email")]
        resp = ApiResponse.error("Validation failed", details=details)
        assert resp.errors[0].field == "email"

    def test_error_without_code(self):
        resp = ApiResponse.error("oops")
        assert resp.errors[0].code is None


# ------------------------------------------------------------------ #
# ApiResponse — paginated constructor
# ------------------------------------------------------------------ #


class TestApiResponsePaginated:
    def test_paginated_sets_items(self):
        resp = ApiResponse.paginated(items=["a", "b"], total=2, page=1, page_size=10)
        assert resp.data == ["a", "b"]
        assert resp.success is True

    def test_paginated_meta_keys(self):
        resp = ApiResponse.paginated(items=[], total=50, page=2, page_size=10)
        assert resp.meta["total"] == 50
        assert resp.meta["page"] == 2
        assert resp.meta["page_size"] == 10
        assert resp.meta["total_pages"] == 5

    def test_paginated_empty_items(self):
        resp = ApiResponse.paginated(items=[], total=0, page=1, page_size=20)
        assert resp.data == []
        assert resp.meta["total_pages"] == 0


# ------------------------------------------------------------------ #
# ApiResponse — serialisation
# ------------------------------------------------------------------ #


class TestApiResponseSerialisation:
    def test_to_dict_returns_dict(self):
        resp = ApiResponse.success("hello")
        d = resp.to_dict()
        assert isinstance(d, dict)
        assert d["data"] == "hello"
        assert d["success"] is True

    def test_to_json_returns_string(self):
        resp = ApiResponse.success({"x": 1})
        j = resp.to_json()
        assert isinstance(j, str)
        parsed = json.loads(j)
        assert parsed["data"] == {"x": 1}

    def test_to_json_error_response(self):
        resp = ApiResponse.error("bad input")
        j = resp.to_json()
        parsed = json.loads(j)
        assert parsed["success"] is False
        assert parsed["errors"][0]["message"] == "bad input"

    def test_to_dict_paginated(self):
        resp = ApiResponse.paginated(["x"], total=1, page=1, page_size=10)
        d = resp.to_dict()
        assert d["meta"]["total_pages"] == 1


# ------------------------------------------------------------------ #
# Error classes
# ------------------------------------------------------------------ #


class TestApiErrorHierarchy:
    def test_base_api_error(self):
        exc = ApiError("oops")
        assert exc.status_code == 500
        assert exc.message == "oops"
        assert exc.code == "internal_error"

    def test_not_found_error(self):
        exc = NotFoundError("Item missing")
        assert exc.status_code == 404
        assert exc.code == "not_found"

    def test_validation_error(self):
        exc = ValidationError("Bad data")
        assert exc.status_code == 422
        assert exc.code == "validation_error"

    def test_authentication_error(self):
        exc = AuthenticationError("Login required")
        assert exc.status_code == 401

    def test_forbidden_error(self):
        exc = ForbiddenError("No access")
        assert exc.status_code == 403

    def test_conflict_error(self):
        exc = ConflictError("Already exists")
        assert exc.status_code == 409

    def test_rate_limit_error(self):
        exc = RateLimitError("Too many requests")
        assert exc.status_code == 429

    def test_custom_status_code(self):
        exc = ApiError("custom", status_code=418)
        assert exc.status_code == 418

    def test_is_exception(self):
        with pytest.raises(NotFoundError):
            raise NotFoundError("gone")


# ------------------------------------------------------------------ #
# error_handler
# ------------------------------------------------------------------ #


class TestErrorHandler:
    def test_converts_not_found(self):
        exc = NotFoundError("Item 42 not found")
        resp = error_handler(exc)
        assert isinstance(resp, ApiResponse)
        assert resp.success is False
        assert resp.errors[0].message == "Item 42 not found"

    def test_converts_validation_error(self):
        details = [ErrorDetail(message="required", field="name")]
        exc = ValidationError("Validation failed", field_errors=details)
        resp = error_handler(exc)
        assert resp.errors[0].field == "name"

    def test_preserves_code(self):
        exc = ConflictError("Duplicate email")
        resp = error_handler(exc)
        assert resp.errors[0].code == "conflict"

    def test_data_is_none(self):
        resp = error_handler(ApiError("err"))
        assert resp.data is None


# ------------------------------------------------------------------ #
# from_pydantic_error
# ------------------------------------------------------------------ #


class TestFromPydanticError:
    def _make_pydantic_error(self):
        class StrictModel(pydantic.BaseModel):
            name: str
            age: int

        try:
            StrictModel(name=123, age="not-a-number")  # type: ignore
        except pydantic.ValidationError as exc:
            return exc
        return None

    def test_returns_api_response(self):
        exc = self._make_pydantic_error()
        resp = from_pydantic_error(exc)
        assert isinstance(resp, ApiResponse)
        assert resp.success is False

    def test_error_details_populated(self):
        exc = self._make_pydantic_error()
        resp = from_pydantic_error(exc)
        assert resp.errors is not None
        assert len(resp.errors) >= 1

    def test_field_paths_present(self):
        exc = self._make_pydantic_error()
        resp = from_pydantic_error(exc)
        fields = [e.field for e in resp.errors if e.field]
        assert len(fields) >= 1

    def test_code_matches_pydantic_type(self):
        exc = self._make_pydantic_error()
        resp = from_pydantic_error(exc)
        # Each error should carry a type string from pydantic
        assert all(e.code is not None for e in resp.errors)


# ------------------------------------------------------------------ #
# wants_json
# ------------------------------------------------------------------ #


class TestWantsJson:
    def test_json_accept_header(self):
        req = FakeRequest("application/json")
        assert wants_json(req) is True

    def test_html_accept_header(self):
        req = FakeRequest("text/html")
        assert wants_json(req) is False

    def test_wildcard_accept_header(self):
        req = FakeRequest("*/*")
        assert wants_json(req) is False

    def test_no_accept_header(self):
        req = FakeRequest("")
        assert wants_json(req) is False

    def test_mixed_accept_prefers_json(self):
        req = FakeRequest("text/html, application/json")
        assert wants_json(req) is True


# ------------------------------------------------------------------ #
# json_response
# ------------------------------------------------------------------ #


class TestJsonResponse:
    def test_returns_dict(self):
        result = json_response({"key": "value"})
        assert isinstance(result, dict)

    def test_status_key(self):
        result = json_response({}, status=201)
        assert result["status"] == 201

    def test_default_status_200(self):
        result = json_response({})
        assert result["status"] == 200

    def test_content_type(self):
        result = json_response({})
        assert result["content_type"] == "application/json"

    def test_body_is_json_string(self):
        result = json_response({"x": 1})
        parsed = json.loads(result["body"])
        assert parsed["x"] == 1

    def test_accepts_api_response(self):
        resp = ApiResponse.success("ok")
        result = json_response(resp)
        parsed = json.loads(result["body"])
        assert parsed["success"] is True


# ------------------------------------------------------------------ #
# negotiate
# ------------------------------------------------------------------ #


class TestNegotiate:
    def test_json_request_returns_json_descriptor(self):
        req = FakeRequest("application/json")
        result = negotiate(req, {"hello": "world"})
        assert result["status"] == 200
        parsed = json.loads(result["body"])
        assert parsed["data"] == {"hello": "world"}

    def test_html_request_calls_renderer(self):
        req = FakeRequest("text/html")
        rendered = negotiate(req, {"key": "val"}, html_renderer=lambda d: f"<p>{d}</p>")
        assert rendered == "<p>{'key': 'val'}</p>"

    def test_html_request_no_renderer_falls_back_to_json(self):
        req = FakeRequest("text/html")
        result = negotiate(req, {"x": 1})
        parsed = json.loads(result["body"])
        assert parsed["success"] is True

    def test_already_api_response_passthrough(self):
        req = FakeRequest("application/json")
        data = ApiResponse.success("done")
        result = negotiate(req, data)
        parsed = json.loads(result["body"])
        assert parsed["data"] == "done"


# ------------------------------------------------------------------ #
# NegotiatedResponse
# ------------------------------------------------------------------ #


class TestNegotiatedResponse:
    def test_resolve_json(self):
        req = FakeRequest("application/json")
        nr = NegotiatedResponse({"id": 1})
        result = nr.resolve(req)
        assert result["status"] == 200

    def test_resolve_html_with_renderer(self):
        req = FakeRequest("text/html")
        nr = NegotiatedResponse({"id": 1}, html_renderer=lambda d: "<div>ok</div>")
        result = nr.resolve(req)
        assert result == "<div>ok</div>"

    def test_resolve_html_without_renderer_fallback(self):
        req = FakeRequest("text/html")
        nr = NegotiatedResponse({"x": 2})
        result = nr.resolve(req)
        parsed = json.loads(result["body"])
        assert parsed["success"] is True
