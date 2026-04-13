"""nitro.workflow — Higher-level workflow engine built on StateMachineMixin.

Public API
----------
WorkflowStep
    Pydantic model defining a single step in a workflow (handler, condition,
    timeout, approval requirements, metadata).

Workflow
    Defines a complete workflow as a directed graph of named steps with
    allowed transitions, validation, and conversion to StateMachineMixin format.

WorkflowMixin
    SQLModel mixin for entities that adds workflow-aware ``advance()``,
    ``approve()``, ``pending_approval``, and ``workflow_history`` fields.

WorkflowEngine
    Orchestrator that manages multiple workflow definitions and provides
    timeout checking and status inspection for workflow instances.

WorkflowError
    Base exception for workflow-related errors.

ApprovalRequired
    Raised when advancing past a step that has not been approved.

ConditionFailed
    Raised when a guard condition prevents entering a step.

InvalidWorkflowTransition
    Raised when a requested transition is not allowed by the workflow.

Quick start::

    from nitro.workflow import Workflow, WorkflowStep, WorkflowMixin, WorkflowEngine
    from nitro.domain.entities.base_entity import Entity

    wf = Workflow(name="order", initial_step="draft")
    wf.add_step(WorkflowStep(name="draft"))
    wf.add_step(WorkflowStep(name="submitted", requires_approval=True))
    wf.add_step(WorkflowStep(name="approved"))
    wf.add_transition("draft", "submitted")
    wf.add_transition("submitted", "approved")

    class Order(Entity, WorkflowMixin, table=True):
        __workflow__ = wf

    order = Order(id="o1")
    order.advance("submitted")
    order.approve(approved_by="manager")
    order.advance("approved")
"""

from .definition import Workflow, WorkflowError
from .engine import WorkflowEngine
from .mixin import (
    ApprovalRequired,
    ConditionFailed,
    InvalidWorkflowTransition,
    WorkflowMixin,
)
from .step import WorkflowStep

__all__ = [
    "Workflow",
    "WorkflowStep",
    "WorkflowMixin",
    "WorkflowEngine",
    "WorkflowError",
    "ApprovalRequired",
    "ConditionFailed",
    "InvalidWorkflowTransition",
]
