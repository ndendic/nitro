"""CRUD view generator functions.

Each function returns an HtmlString fragment ready to be embedded in a page.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Type, Optional

from rusty_tags import Div, H1, H2, Span, A, HtmlString, Fragment
from nitro.html.components import (
    Card, CardHeader, CardTitle, CardContent,
    Button, Badge, LucideIcon,
)
from nitro.html.components.model_views import (
    ModelTable, ModelForm, ModelCard,
    CRUDDialog, DeleteConfirmDialog, get_model_fields,
)

from .config import CRUDConfig

if TYPE_CHECKING:
    pass


def _resolve(entity_class, config: Optional[CRUDConfig]) -> CRUDConfig:
    cfg = config or CRUDConfig()
    return cfg.resolve(entity_class)


# ---------------------------------------------------------------------------
# List view
# ---------------------------------------------------------------------------

def crud_list_view(
    entity_class,
    request=None,
    config: Optional[CRUDConfig] = None,
) -> HtmlString:
    """Return an HTML fragment with the list view for *entity_class*.

    Includes:
    - Page header with title and optional "Create" button
    - Optional search input (if config.searchable)
    - ModelTable with edit/delete action expressions
    - DeleteConfirmDialog (hidden until triggered via Datastar)

    Args:
        entity_class: Entity subclass to list.
        request: Optional Sanic/framework request (unused, reserved).
        config: Optional CRUDConfig; defaults are auto-derived.

    Returns:
        HtmlString fragment.
    """
    cfg = _resolve(entity_class, config)
    prefix = cfg.url_prefix

    # Determine which fields to show
    exclude = list(cfg.exclude_fields)
    if cfg.list_fields:
        # Exclude all fields NOT in list_fields (beyond the base excludes)
        all_fields = list(get_model_fields(entity_class).keys())
        extra_exclude = [f for f in all_fields if f not in cfg.list_fields and f not in exclude]
        exclude = exclude + extra_exclude

    # Build on_edit / on_delete expressions for the table rows
    on_edit = f"@get('{prefix}/{{id}}/edit')"
    on_delete = (
        f"$_delete_id='{{id}}'; document.getElementById('crud-delete-dialog').showModal()"
    )

    # Table actions flag
    show_actions = bool({"edit", "delete"} & set(cfg.actions))

    table = ModelTable(
        entity_class,
        exclude_fields=exclude,
        sortable=cfg.sortable,
        actions=show_actions,
        on_edit=on_edit if "edit" in cfg.actions else None,
        on_delete=on_delete if "delete" in cfg.actions else None,
        id=f"{entity_class.__name__.lower()}-table",
    )

    # Header
    header_children = [
        Div(
            H1(cfg.title, cls="text-2xl font-bold"),
            cls="flex-1",
        ),
    ]
    if "create" in cfg.actions:
        header_children.append(
            Button(
                LucideIcon("plus"),
                " New ",
                cfg.title_singular,
                variant="primary",
                cls="create-btn",
                **{"data-on:click": f"@get('{prefix}/create')"},
            )
        )

    header = Div(*header_children, cls="flex items-center justify-between mb-6")

    # Optional search bar
    search_bar = None
    if cfg.searchable:
        search_bar = Div(
            Div(
                LucideIcon("search", cls="text-muted-foreground"),
                cls="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2",
            ),
            **{
                "data-signals:_search": "''",
                "class": "relative mb-4",
            },
        )

    # DeleteConfirmDialog (hidden, triggered by table rows)
    delete_dialog = DeleteConfirmDialog(
        entity_name=cfg.title_singular,
        entity_id="",  # will be filled by Datastar signal $_delete_id
        dialog_id="crud-delete-dialog",
        on_confirm=f"@delete('{prefix}/${{$_delete_id}}/delete')",
    )

    parts = [header]
    if search_bar:
        parts.append(search_bar)
    parts.append(table)
    parts.append(delete_dialog)

    return Div(*parts, cls="crud-list-view", **{"data-signals:_delete_id": "''"})


# ---------------------------------------------------------------------------
# Detail view
# ---------------------------------------------------------------------------

def crud_detail_view(
    entity_class,
    entity_id: str,
    config: Optional[CRUDConfig] = None,
) -> HtmlString:
    """Return an HTML fragment with the detail (card) view for one entity.

    Args:
        entity_class: Entity subclass.
        entity_id: Primary key of the instance to display.
        config: Optional CRUDConfig.

    Returns:
        HtmlString fragment.

    Raises:
        ValueError: If the entity is not found.
    """
    cfg = _resolve(entity_class, config)
    prefix = cfg.url_prefix

    instance = entity_class.get(entity_id)
    if instance is None:
        raise ValueError(f"{cfg.title_singular} with id '{entity_id}' not found.")

    exclude = list(cfg.exclude_fields)
    if cfg.detail_fields:
        all_fields = list(get_model_fields(entity_class).keys())
        extra_exclude = [f for f in all_fields if f not in cfg.detail_fields and f not in exclude]
        exclude = exclude + extra_exclude

    # Breadcrumb
    entity_label = str(getattr(instance, cfg.title_field, entity_id)) if cfg.title_field else entity_id
    breadcrumb = Div(
        A(cfg.title, href=prefix, cls="text-muted-foreground hover:underline"),
        Span(" / ", cls="text-muted-foreground mx-1"),
        Span(entity_label, cls="font-medium"),
        cls="flex items-center text-sm mb-4",
    )

    card = ModelCard(
        entity_class,
        instance=instance,
        exclude_fields=exclude,
        title_field=cfg.title_field,
        description_field=cfg.description_field,
    )

    # Action buttons
    action_btns = [
        A(
            Button("Back to list", variant="outline"),
            href=prefix,
        ),
    ]
    if "edit" in cfg.actions:
        action_btns.append(
            A(
                Button("Edit", variant="primary"),
                href=f"{prefix}/{entity_id}/edit",
            )
        )
    if "delete" in cfg.actions:
        action_btns.append(
            Button(
                "Delete",
                variant="destructive",
                **{"data-on:click": f"@delete('{prefix}/{entity_id}/delete')"},
            )
        )

    actions_row = Div(*action_btns, cls="flex gap-2 mt-4")

    return Div(breadcrumb, card, actions_row, cls="crud-detail-view")


# ---------------------------------------------------------------------------
# Create view
# ---------------------------------------------------------------------------

def crud_create_view(
    entity_class,
    config: Optional[CRUDConfig] = None,
) -> HtmlString:
    """Return an HTML fragment with a blank create form.

    Args:
        entity_class: Entity subclass.
        config: Optional CRUDConfig.

    Returns:
        HtmlString fragment.
    """
    cfg = _resolve(entity_class, config)
    prefix = cfg.url_prefix

    exclude = list(cfg.exclude_fields)
    if cfg.form_fields:
        all_fields = list(get_model_fields(entity_class).keys())
        extra_exclude = [f for f in all_fields if f not in cfg.form_fields and f not in exclude]
        exclude = exclude + extra_exclude

    header = Div(
        H2(f"Create {cfg.title_singular}", cls="text-xl font-bold"),
        cls="mb-4",
    )

    form = ModelForm(entity_class, exclude_fields=exclude)

    save_action = f"@post('{prefix}/create')"
    cancel_href = prefix

    buttons = Div(
        A(Button("Cancel", variant="outline"), href=cancel_href),
        Button(
            "Save",
            variant="primary",
            cls="save-btn",
            **{"data-on:click": save_action},
        ),
        cls="flex gap-2 mt-4",
    )

    return Div(header, form, buttons, cls="crud-create-view")


# ---------------------------------------------------------------------------
# Edit view
# ---------------------------------------------------------------------------

def crud_edit_view(
    entity_class,
    entity_id: str,
    config: Optional[CRUDConfig] = None,
) -> HtmlString:
    """Return an HTML fragment with an edit form pre-filled with entity data.

    Args:
        entity_class: Entity subclass.
        entity_id: Primary key of the instance to edit.
        config: Optional CRUDConfig.

    Returns:
        HtmlString fragment.

    Raises:
        ValueError: If the entity is not found.
    """
    cfg = _resolve(entity_class, config)
    prefix = cfg.url_prefix

    instance = entity_class.get(entity_id)
    if instance is None:
        raise ValueError(f"{cfg.title_singular} with id '{entity_id}' not found.")

    exclude = list(cfg.exclude_fields)
    if cfg.form_fields:
        all_fields = list(get_model_fields(entity_class).keys())
        extra_exclude = [f for f in all_fields if f not in cfg.form_fields and f not in exclude]
        exclude = exclude + extra_exclude

    header = Div(
        H2(f"Edit {cfg.title_singular}", cls="text-xl font-bold"),
        cls="mb-4",
    )

    form = ModelForm(entity_class, instance=instance, exclude_fields=exclude)

    save_action = f"@post('{prefix}/{entity_id}/edit')"
    cancel_href = f"{prefix}/{entity_id}"

    buttons = Div(
        A(Button("Cancel", variant="outline"), href=cancel_href),
        Button(
            "Save",
            variant="primary",
            cls="save-btn",
            **{"data-on:click": save_action},
        ),
        cls="flex gap-2 mt-4",
    )

    return Div(header, form, buttons, cls="crud-edit-view")
