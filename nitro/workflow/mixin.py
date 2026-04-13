"""nitro.workflow.mixin — WorkflowMixin adds high-level workflow behavior to entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional

from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

from nitro.domain.mixins import StateMachineMixin

from .definition import Workflow, WorkflowError


class ApprovalRequired(WorkflowError):
    """Raised when a step requires approval before advancing."""

    def __init__(self, step_name: str) -> None:
        self.step_name = step_name
        super().__init__(f"Step '{step_name}' requires approval before advancing.")


class ConditionFailed(WorkflowError):
    """Raised when a guard condition prevents entering a step."""

    def __init__(self, step_name: str) -> None:
        self.step_name = step_name
        super().__init__(f"Guard condition failed for step '{step_name}'.")


class InvalidWorkflowTransition(WorkflowError):
    """Raised when the requested transition is not allowed by the workflow."""

    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Transition from '{current}' to '{target}' is not allowed by the workflow."
        )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowMixin(StateMachineMixin):
    """Adds high-level workflow-aware behavior on top of StateMachineMixin.

    Subclasses must declare a ``__workflow__`` class variable pointing to a
    :class:`~nitro.workflow.definition.Workflow` instance.  ``__states__``
    and ``__initial_state__`` are derived automatically from the workflow so
    that the underlying StateMachineMixin manages the ``state`` field.

    Persisted fields added to the entity table:

    * ``workflow_history`` — JSON list of transition records.

    In-memory (non-persisted) state:

    * ``_approval_granted`` — internal flag; True when the current step's
      approval requirement has been satisfied.

    Example::

        from nitro.workflow import Workflow, WorkflowStep, WorkflowMixin
        from nitro.domain.entities.base_entity import Entity

        wf = Workflow(name="order", initial_step="draft")
        wf.add_step(WorkflowStep(name="draft"))
        wf.add_step(WorkflowStep(name="submitted", requires_approval=True))
        wf.add_step(WorkflowStep(name="approved"))
        wf.add_transition("draft", "submitted")
        wf.add_transition("submitted", "approved")

        class Order(Entity, WorkflowMixin, table=True):
            __workflow__ = wf
    """

    __workflow__: ClassVar[Workflow]

    # sa_type=JSON tells SQLModel to create a JSON-typed Column per concrete
    # subclass, avoiding the "Column already assigned" error that occurs when
    # a single Column instance (via sa_column=) is shared across subclasses.
    workflow_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_type=JSON,
        sa_column_kwargs={"nullable": False},
    )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "__workflow__") and isinstance(cls.__workflow__, Workflow):
            wf = cls.__workflow__
            cls.__states__ = wf.to_states_dict()  # type: ignore[assignment]
            cls.__initial_state__ = wf.initial_step  # type: ignore[assignment]

    def __init__(self, **data: Any) -> None:
        if "workflow_history" not in data:
            data["workflow_history"] = []
        super().__init__(**data)
        # Reset approval flag on instantiation.
        object.__setattr__(self, "_approval_granted", False)

    # ------------------------------------------------------------------
    # Approval
    # ------------------------------------------------------------------

    @property
    def pending_approval(self) -> bool:
        """True if the current step requires approval and it has not been granted."""
        step = self._current_step
        if step is None:
            return False
        return step.requires_approval and not self._approval_granted

    def approve(self, approved_by: str = "") -> None:
        """Grant approval for the current step.

        Args:
            approved_by: Identifier of the approver (role or username).
                         Stored in workflow history; not validated here.

        Raises:
            WorkflowError: If the current step does not require approval.
        """
        step = self._current_step
        if step is None or not step.requires_approval:
            raise WorkflowError(
                f"Current step '{self.state}' does not require approval."
            )
        object.__setattr__(self, "_approval_granted", True)

    # ------------------------------------------------------------------
    # Advancing
    # ------------------------------------------------------------------

    def advance(
        self,
        target: str,
        context: Optional[Dict[str, Any]] = None,
        approved_by: str = "",
    ) -> None:
        """Attempt to transition the entity to *target* step.

        The following checks are performed in order:

        1. The transition is allowed by the workflow definition.
        2. If the *current* step requires approval, it must have been
           granted via :meth:`approve` (or ``approved_by`` is provided
           as a convenience shorthand to approve-and-advance in one call).
        3. The guard condition on the *target* step (if any) must return
           True.
        4. The target step's handler (if any) is invoked.
        5. The transition is recorded in :attr:`workflow_history`.
        6. The approval flag is reset for the new step.
        7. Lifecycle hooks ``on_exit_<old>`` / ``on_enter_<new>`` are called.

        Args:
            target: Name of the step to advance to.
            context: Arbitrary data passed to the condition and handler.
            approved_by: If non-empty, grants approval for the current step
                         before advancing (convenience shorthand).

        Raises:
            InvalidWorkflowTransition: If the transition is not allowed.
            ApprovalRequired: If approval is needed and not granted.
            ConditionFailed: If the target step's guard condition returns False.
        """
        context = context or {}

        # 1. Check allowed transition.
        wf = self.__class__.__workflow__
        allowed = wf.transitions.get(self.state, [])
        if target not in allowed:
            raise InvalidWorkflowTransition(self.state, target)

        # 2. Check approval for current step.
        if approved_by:
            self.approve(approved_by=approved_by)

        current_step = self._current_step
        if current_step is not None and current_step.requires_approval:
            if not self._approval_granted:
                raise ApprovalRequired(self.state)

        # 3. Check guard condition on the target step.
        target_step = wf.get_step(target)
        if target_step is not None and target_step.condition is not None:
            if not target_step.condition(self, context):
                raise ConditionFailed(target)

        # 4. Run handler on target step.
        if target_step is not None and target_step.handler is not None:
            target_step.handler(self, context)

        # 5. Record history before state change.
        record: Dict[str, Any] = {
            "from": self.state,
            "to": target,
            "timestamp": _utc_now_iso(),
            "context": context,
        }
        if approved_by:
            record["approved_by"] = approved_by

        old_state = self.state

        # Update state directly (bypass StateMachineMixin.transition_to so we
        # avoid double-firing lifecycle hooks).
        self.state = target

        # Persist history — reassign so SQLModel detects the mutation.
        current_history = self.workflow_history if self.workflow_history is not None else []
        self.workflow_history = list(current_history) + [record]

        # 6. Reset approval flag for the new step.
        object.__setattr__(self, "_approval_granted", False)

        # 7. Lifecycle hooks (mirrors StateMachineMixin behaviour).
        exit_hook = getattr(self, f"on_exit_{old_state}", None)
        if callable(exit_hook):
            exit_hook()

        enter_hook = getattr(self, f"on_enter_{target}", None)
        if callable(enter_hook):
            enter_hook()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _current_step(self):
        """Return the WorkflowStep for the current state, or None."""
        if not hasattr(self.__class__, "__workflow__"):
            return None
        return self.__class__.__workflow__.get_step(self.state)

    @property
    def available_next_steps(self) -> List[str]:
        """Return the list of step names reachable from the current state."""
        wf = self.__class__.__workflow__
        return list(wf.transitions.get(self.state, []))
