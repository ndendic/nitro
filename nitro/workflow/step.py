"""nitro.workflow.step — WorkflowStep model definition."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """Defines a single step in a workflow.

    Attributes:
        name: Step identifier, must be unique within the workflow.
        handler: Optional callable executed when entering the step.
            Receives the entity and optional context dict.
        condition: Optional guard callable that must return True
            for a transition into this step to be allowed.
            Receives the entity and optional context dict.
        timeout_seconds: Maximum time (in seconds) allowed in this
            step before an automatic transition is triggered.
        on_timeout: Name of the step to transition to when the
            timeout_seconds threshold is exceeded.
        requires_approval: When True, advancing past this step
            requires an explicit ``approve()`` call.
        approved_by: Role or user identifier allowed to approve this
            step.  Purely informational unless enforced by the
            application layer.
        metadata: Arbitrary key/value data attached to the step.
    """

    name: str
    handler: Optional[Callable[..., Any]] = Field(default=None, exclude=True)
    condition: Optional[Callable[..., bool]] = Field(default=None, exclude=True)
    timeout_seconds: Optional[int] = None
    on_timeout: Optional[str] = None
    requires_approval: bool = False
    approved_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}
