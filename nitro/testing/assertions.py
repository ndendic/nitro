"""
Assert helpers for entities, HTML, and SSE structures.

All helpers raise ``AssertionError`` with descriptive messages on failure so
they work naturally inside pytest test functions (no need to import pytest).
"""

import re
from typing import Any, Dict, Iterable, List, Optional


# ---------------------------------------------------------------------------
# Entity assertions
# ---------------------------------------------------------------------------

def assert_entity_saved(entity: Any) -> None:
    """
    Assert that *entity* exists in its repository.

    Calls ``entity.__class__.exists(entity.id)`` — requires the entity to be
    a ``nitro.domain.entities.base_entity.Entity`` subclass.

    Raises:
        AssertionError: if the entity is not found in the repository.
    """
    cls = type(entity)
    entity_id = getattr(entity, "id", None)
    assert entity_id is not None, (
        f"{cls.__name__} has no 'id' attribute; cannot check if it was saved."
    )
    assert cls.exists(entity_id), (
        f"Expected {cls.__name__}(id={entity_id!r}) to exist in the repository, "
        "but it was not found."
    )


def assert_entity_deleted(entity: Any) -> None:
    """
    Assert that *entity* no longer exists in its repository.

    Raises:
        AssertionError: if the entity is still found in the repository.
    """
    cls = type(entity)
    entity_id = getattr(entity, "id", None)
    assert entity_id is not None, (
        f"{cls.__name__} has no 'id' attribute; cannot check deletion."
    )
    assert not cls.exists(entity_id), (
        f"Expected {cls.__name__}(id={entity_id!r}) to be deleted from the repository, "
        "but it still exists."
    )


def assert_entity_equal(
    a: Any,
    b: Any,
    fields: Optional[List[str]] = None,
) -> None:
    """
    Assert that two entity instances have equal field values.

    Args:
        a: First entity.
        b: Second entity.
        fields: If provided, only compare these fields. Otherwise compare all
                fields from ``a.model_fields``.

    Raises:
        AssertionError: with a list of differing fields.
    """
    if fields is None:
        fields = list(getattr(type(a), "model_fields", {}).keys())

    diffs: List[str] = []
    for f in fields:
        val_a = getattr(a, f, None)
        val_b = getattr(b, f, None)
        if val_a != val_b:
            diffs.append(f"  {f}: {val_a!r} != {val_b!r}")

    assert not diffs, (
        f"Entities differ in {len(diffs)} field(s):\n" + "\n".join(diffs)
    )


def assert_entity_fields(entity: Any, **expected: Any) -> None:
    """
    Assert that *entity* has specific field values.

    Usage::

        assert_entity_fields(user, name="Alice", age=30)

    Raises:
        AssertionError: listing every field whose actual value differs from
                        the expected value.
    """
    diffs: List[str] = []
    for field_name, expected_value in expected.items():
        actual = getattr(entity, field_name, _MISSING)
        if actual is _MISSING:
            diffs.append(f"  {field_name}: attribute not found on entity")
        elif actual != expected_value:
            diffs.append(f"  {field_name}: expected {expected_value!r}, got {actual!r}")

    assert not diffs, (
        f"{type(entity).__name__} field assertion failed:\n" + "\n".join(diffs)
    )


# ---------------------------------------------------------------------------
# HTML assertions
# ---------------------------------------------------------------------------

def assert_html_contains(html: str, *texts: str) -> None:
    """
    Assert that *html* contains every string in *texts*.

    Case-sensitive substring check.

    Raises:
        AssertionError: listing every text that was not found.
    """
    missing = [t for t in texts if t not in html]
    assert not missing, (
        f"HTML is missing {len(missing)} expected string(s): "
        + ", ".join(repr(m) for m in missing)
    )


def assert_html_tag(html: str, tag: str, **attrs: Any) -> None:
    """
    Assert that *html* contains at least one ``<tag>`` element that has ALL of
    the specified attributes with the given values.

    Attribute matching is substring-based (e.g. ``class="foo"`` matches even if
    the element also has ``class="foo bar"``).  Pass ``_content`` as a special
    keyword to also check the element's inner content.

    Usage::

        assert_html_tag(html, "button", type="submit")
        assert_html_tag(html, "div", id="counter", _content="0")

    Raises:
        AssertionError: if no matching element is found.
    """
    content_check = attrs.pop("_content", None)

    # Quick check: does the tag appear at all?
    assert re.search(rf"<{re.escape(tag)}[\s>]", html), (
        f"No <{tag}> element found in HTML."
    )

    # Check every attribute substring
    missing_attrs: List[str] = []
    for attr_name, attr_value in attrs.items():
        attr_name_html = attr_name.replace("_", "-")
        pattern = rf'{re.escape(attr_name_html)}=["\']?[^"\']*{re.escape(str(attr_value))}'
        if not re.search(pattern, html):
            missing_attrs.append(f'{attr_name_html}="{attr_value}"')

    assert not missing_attrs, (
        f"<{tag}> found but missing attributes: "
        + ", ".join(missing_attrs)
    )

    if content_check is not None:
        assert content_check in html, (
            f"<{tag}> found but content {content_check!r} not present in HTML."
        )


# ---------------------------------------------------------------------------
# SSE assertions
# ---------------------------------------------------------------------------

def assert_sse_event(
    data: Any,
    event_type: Optional[str] = None,
    selector: Optional[str] = None,
) -> None:
    """
    Assert that *data* looks like a valid SSE (Server-Sent Events) payload.

    Performs structural checks:

    - If *data* is a ``str``: checks it starts with ``data:`` or contains
      standard SSE fields.
    - If *data* is a ``dict``: checks for common Datastar/SSE keys.

    Args:
        data:       The SSE payload to inspect.
        event_type: If provided, assert this event type is referenced in *data*.
        selector:   If provided, assert this CSS selector appears in *data*.

    Raises:
        AssertionError: if the structural checks fail.
    """
    if isinstance(data, str):
        assert data.strip(), "SSE data string is empty."
        lines = data.strip().splitlines()
        sse_prefixes = ("data:", "event:", "id:", "retry:")
        valid_lines = [ln for ln in lines if any(ln.startswith(p) for p in sse_prefixes)]
        assert valid_lines, (
            f"SSE string has no recognised fields (data:/event:/id:/retry:).\n"
            f"Got:\n{data}"
        )
        if event_type:
            assert event_type in data, (
                f"Expected event_type {event_type!r} not found in SSE data."
            )
        if selector:
            assert selector in data, (
                f"Expected selector {selector!r} not found in SSE data."
            )

    elif isinstance(data, dict):
        # Datastar-style dict payload
        known_keys = {"type", "event", "selector", "elements", "merge", "signals"}
        assert known_keys & set(data.keys()), (
            f"SSE dict has none of the expected keys {known_keys}. Got: {set(data.keys())}"
        )
        if event_type:
            assert data.get("type") == event_type or data.get("event") == event_type, (
                f"Expected event_type {event_type!r}, got {data.get('type') or data.get('event')!r}"
            )
        if selector:
            assert data.get("selector") == selector, (
                f"Expected selector {selector!r}, got {data.get('selector')!r}"
            )
    else:
        raise AssertionError(
            f"assert_sse_event: expected str or dict, got {type(data).__name__}"
        )


# ---------------------------------------------------------------------------
# Private sentinel
# ---------------------------------------------------------------------------

class _Missing:
    """Sentinel for missing attributes."""
    def __repr__(self):
        return "<MISSING>"


_MISSING = _Missing()
