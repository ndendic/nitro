"""Query parameter parsing for filtering, sorting, and pagination."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import sqlalchemy as sa


@dataclass
class QueryParams:
    """Parsed REST query parameters."""

    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_desc: bool = False
    search: Optional[str] = None
    filters: dict[str, Any] = field(default_factory=dict)
    fields: Optional[list[str]] = None


def parse_query_params(args: dict, default_page_size: int = 20, max_page_size: int = 100) -> QueryParams:
    """Parse request query parameters into a QueryParams object.

    Supported parameters:
        page        — page number (1-based)
        page_size   — items per page
        sort        — field name, prefix with '-' for descending
        q           — text search query
        fields      — comma-separated list of fields to return
        <field>     — exact match filter (any other param)

    Reserved param names (not treated as filters):
        page, page_size, sort, q, fields
    """
    reserved = {"page", "page_size", "sort", "q", "fields"}

    page = max(1, _int_param(args, "page", 1))
    page_size = min(max_page_size, max(1, _int_param(args, "page_size", default_page_size)))

    sort_by = None
    sort_desc = False
    sort_val = _str_param(args, "sort")
    if sort_val:
        if sort_val.startswith("-"):
            sort_by = sort_val[1:]
            sort_desc = True
        else:
            sort_by = sort_val

    search = _str_param(args, "q")

    fields_str = _str_param(args, "fields")
    fields = [f.strip() for f in fields_str.split(",") if f.strip()] if fields_str else None

    filters = {}
    for key, value in args.items():
        if key not in reserved:
            # Normalize lists to single value
            if isinstance(value, list):
                value = value[0] if len(value) == 1 else value
            filters[key] = value

    return QueryParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc,
        search=search,
        filters=filters,
        fields=fields,
    )


def apply_filters(entity_class, params: QueryParams) -> list:
    """Apply filters, search, sort, and pagination to an entity query.

    Returns (items, total_count) tuple.
    """
    from nitro.html.components.model_views.fields import get_model_fields

    model_fields = get_model_fields(entity_class)
    expressions = []

    # Exact-match filters
    for field_name, value in params.filters.items():
        if field_name in model_fields or field_name == "id":
            col = getattr(entity_class, field_name, None)
            if col is not None:
                expressions.append(col == value)

    # Text search across string fields
    if params.search:
        search_cols = []
        for fname, finfo in model_fields.items():
            # get_model_fields returns dicts with a 'type' key
            field_type = finfo.get("type") if isinstance(finfo, dict) else getattr(finfo, "type", None)
            if field_type == "string":
                col = getattr(entity_class, fname, None)
                if col is not None:
                    search_cols.append(col)
        if search_cols:
            pattern = f"%{params.search}%"
            search_expr = sa.or_(*[col.ilike(pattern) for col in search_cols])
            expressions.append(search_expr)

    # Get total count
    if expressions:
        all_items = entity_class.where(*expressions)
    else:
        all_items = entity_class.all()

    total = len(all_items)

    # Sort
    if params.sort_by:
        reverse = params.sort_desc
        all_items.sort(
            key=lambda e: (getattr(e, params.sort_by, None) or ""),
            reverse=reverse,
        )

    # Paginate
    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    items = all_items[start:end]

    return items, total


def _int_param(args: dict, key: str, default: int) -> int:
    val = args.get(key)
    if val is None:
        return default
    if isinstance(val, list):
        val = val[0]
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _str_param(args: dict, key: str) -> Optional[str]:
    val = args.get(key)
    if val is None:
        return None
    if isinstance(val, list):
        val = val[0]
    return str(val) if val else None
