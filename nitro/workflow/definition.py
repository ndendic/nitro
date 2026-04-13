"""nitro.workflow.definition — Workflow class for defining workflow graphs."""

from __future__ import annotations

from typing import Dict, List, Optional

from .step import WorkflowStep


class WorkflowError(Exception):
    """Raised when a workflow definition is invalid."""


class Workflow:
    """Defines a complete workflow as a directed graph of named steps.

    Example::

        wf = Workflow(name="order", initial_step="draft")
        wf.add_step(WorkflowStep(name="draft"))
        wf.add_step(WorkflowStep(name="submitted", requires_approval=True))
        wf.add_step(WorkflowStep(name="approved"))
        wf.add_transition("draft", "submitted")
        wf.add_transition("submitted", "approved")
        wf.validate()

    Attributes:
        name: Workflow identifier.
        steps: Mapping from step name to WorkflowStep instance.
        initial_step: The step an entity starts in.
        transitions: Mapping from step name to list of reachable step names.
    """

    def __init__(self, name: str, initial_step: str = "") -> None:
        self.name: str = name
        self.initial_step: str = initial_step
        self.steps: Dict[str, WorkflowStep] = {}
        self.transitions: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_step(self, step: WorkflowStep) -> None:
        """Register *step* in the workflow.

        Args:
            step: The WorkflowStep to add.

        Raises:
            WorkflowError: If a step with the same name is already registered.
        """
        if step.name in self.steps:
            raise WorkflowError(f"Step '{step.name}' is already registered in workflow '{self.name}'.")
        self.steps[step.name] = step
        if step.name not in self.transitions:
            self.transitions[step.name] = []

    def add_transition(self, from_step: str, to_step: str) -> None:
        """Allow a transition from *from_step* to *to_step*.

        Both steps must be registered before calling this method.

        Args:
            from_step: Name of the originating step.
            to_step: Name of the destination step.

        Raises:
            WorkflowError: If either step name is unknown.
        """
        if from_step not in self.steps:
            raise WorkflowError(f"Unknown step '{from_step}' in workflow '{self.name}'.")
        if to_step not in self.steps:
            raise WorkflowError(f"Unknown step '{to_step}' in workflow '{self.name}'.")
        if to_step not in self.transitions[from_step]:
            self.transitions[from_step].append(to_step)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_step(self, name: str) -> Optional[WorkflowStep]:
        """Return the step registered under *name*, or None.

        Args:
            name: Step name to look up.

        Returns:
            The WorkflowStep, or None if not found.
        """
        return self.steps.get(name)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Assert the workflow is well-formed.

        Checks performed:
        - ``initial_step`` is non-empty and exists.
        - All steps referenced in transitions are registered.
        - Every registered step is reachable from ``initial_step``
          (no orphan steps that can never be entered).

        Raises:
            WorkflowError: Describing the first problem found.
        """
        if not self.initial_step:
            raise WorkflowError(f"Workflow '{self.name}' has no initial_step defined.")
        if self.initial_step not in self.steps:
            raise WorkflowError(
                f"Workflow '{self.name}': initial_step '{self.initial_step}' is not a registered step."
            )

        # All transition targets must be known steps.
        for from_step, targets in self.transitions.items():
            if from_step not in self.steps:
                raise WorkflowError(
                    f"Workflow '{self.name}': transition source '{from_step}' is not a registered step."
                )
            for to_step in targets:
                if to_step not in self.steps:
                    raise WorkflowError(
                        f"Workflow '{self.name}': transition target '{to_step}' "
                        f"from '{from_step}' is not a registered step."
                    )

        # Reachability: BFS from initial_step.
        reachable = {self.initial_step}
        queue = [self.initial_step]
        while queue:
            current = queue.pop(0)
            for target in self.transitions.get(current, []):
                if target not in reachable:
                    reachable.add(target)
                    queue.append(target)

        orphans = set(self.steps.keys()) - reachable
        if orphans:
            raise WorkflowError(
                f"Workflow '{self.name}': unreachable (orphan) steps: {sorted(orphans)}. "
                f"Every step must be reachable from '{self.initial_step}'."
            )

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_states_dict(self) -> Dict[str, List[str]]:
        """Convert this workflow to a ``__states__`` dict compatible with
        :class:`~nitro.domain.mixins.StateMachineMixin`.

        Returns:
            A dict mapping each step name to its list of reachable step names.
        """
        return {step: list(targets) for step, targets in self.transitions.items()}

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"Workflow(name={self.name!r}, steps={list(self.steps)}, initial_step={self.initial_step!r})"
