"""Model-based view generation for Nitro entities.

This module provides utilities and components for automatically generating UI
from Pydantic Entity classes. Supports forms, tables, cards, and CRUD dialogs.

Public API:
    - get_model_fields: Extract field metadata from Entity classes
    - get_input_type: Map field types to HTML input types
    - get_component_for_field: Map field types to component classes
    - ModelField: Render individual form fields from metadata
    - sort_fields: Sort fields by order attribute
    - ModelForm: Generate complete forms from Entity classes
    - ModelCard: Display entity data in card format
    - ModelTable: Generate data tables from Entity classes
    - Combobox: Searchable dropdown component for foreign keys
    - get_related_entity_class: Get Entity class from FK string
    - render_fk_field: Render FK field as Combobox
    - CRUDDialog: Create/Edit dialog with ModelForm
    - DeleteConfirmDialog: Confirmation modal for deletions
"""

from .fields import (
    get_model_fields,
    get_input_type,
    get_component_for_field,
)
from .model_field import ModelField, sort_fields
from .form import ModelForm
from .cards import ModelCard
from .tables import ModelTable
from .combobox import Combobox, get_related_entity_class, render_fk_field
from .dialogs import CRUDDialog, DeleteConfirmDialog

__all__ = [
    "get_model_fields",
    "get_input_type",
    "get_component_for_field",
    "ModelField",
    "sort_fields",
    "ModelForm",
    "ModelCard",
    "ModelTable",
    "Combobox",
    "get_related_entity_class",
    "render_fk_field",
    "CRUDDialog",
    "DeleteConfirmDialog",
]
