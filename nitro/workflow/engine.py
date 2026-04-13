"""nitro.workflow.engine — WorkflowEngine orchestrates multiple workflow instances."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .definition import Workflow, WorkflowError
from .mixin import WorkflowMixin


class WorkflowEngine:
    """Manages multiple named workflow definitions and provides runtime helpers.

    Example::

        engine = WorkflowEngine()
        engine.register(order_workflow)

        status = engine.get_status(my_order)
        # {'step': 'draft', 'requires_approval': False, 'next_steps': ['submitted', 'cancelled']}

        engine.check_timeouts(my_order)
        # auto-transitions if the current step has timed out
    """

    def __init__(self) -> None:
        self._workflows: Dict[str, Workflow] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, workflow: Workflow) -> None:
        """Register a workflow definition.

        Args:
            workflow: The Workflow to register.

        Raises:
            WorkflowError: If a workflow with the same name is already registered.
        """
        if workflow.name in self._workflows:
            raise WorkflowError(
                f"Workflow '{workflow.name}' is already registered in this engine."
            )
        self._workflows[workflow.name] = workflow

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Retrieve a registered workflow by name.

        Args:
            name: Workflow name.

        Returns:
            The Workflow, or None if not registered.
        """
        return self._workflows.get(name)

    # ------------------------------------------------------------------
    # Runtime helpers
    # ------------------------------------------------------------------

    def check_timeouts(self, entity: WorkflowMixin) -> bool:
        """Check whether the entity's current step has timed out.

        If the current step defines ``timeout_seconds`` and the entity's
        most recent transition into that step happened long enough ago,
        the entity is automatically advanced to ``on_timeout``.

        The elapsed time is measured from the *timestamp* field of the most
        recent history entry whose ``to`` field matches the current state.
        If no such entry exists (i.e. the entity was created directly in this
        state), the check is skipped.

        Args:
            entity: A WorkflowMixin instance to inspect.

        Returns:
            True if a timeout transition was performed, False otherwise.
        """
        wf = entity.__class__.__workflow__
        step = wf.get_step(entity.state)
        if step is None or step.timeout_seconds is None or step.on_timeout is None:
            return False

        # Find the most recent entry to the current state.
        entry_time: Optional[datetime] = None
        for record in reversed(entity.workflow_history):
            if record.get("to") == entity.state:
                try:
                    entry_time = datetime.fromisoformat(record["timestamp"])
                except (KeyError, ValueError):
                    pass
                break

        if entry_time is None:
            return False

        now = datetime.now(timezone.utc)
        # Make entry_time timezone-aware if it isn't already.
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=timezone.utc)

        elapsed = (now - entry_time).total_seconds()
        if elapsed >= step.timeout_seconds:
            entity.advance(step.on_timeout, context={"reason": "timeout"})
            return True

        return False

    def get_status(self, entity: WorkflowMixin) -> Dict[str, Any]:
        """Return a status snapshot for the entity.

        Args:
            entity: A WorkflowMixin instance.

        Returns:
            A dict with keys:
            - ``step``: current step name (str)
            - ``requires_approval``: whether approval is needed (bool)
            - ``pending_approval``: whether approval is outstanding (bool)
            - ``next_steps``: list of reachable step names
            - ``history_count``: number of recorded transitions (int)
            - ``step_metadata``: metadata dict from the current step
        """
        wf = entity.__class__.__workflow__
        step = wf.get_step(entity.state)
        return {
            "step": entity.state,
            "requires_approval": step.requires_approval if step else False,
            "pending_approval": entity.pending_approval,
            "next_steps": entity.available_next_steps,
            "history_count": len(entity.workflow_history),
            "step_metadata": step.metadata if step else {},
        }

    def list_workflows(self) -> List[str]:
        """Return the names of all registered workflows."""
        return list(self._workflows.keys())
