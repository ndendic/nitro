"""
Pydantic models for feature flags: Flag, FlagRule.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class FlagRule(BaseModel):
    """A single conditional rule for feature flag activation.

    Rules are evaluated against a context dict.  A rule passes when
    ``context[attribute]`` satisfies the ``operator`` comparison against
    ``value``.  If the attribute is absent from the context the rule fails.

    Supported operators:

    - ``eq`` / ``neq`` — equality / inequality
    - ``in`` / ``not_in`` — membership (value must be a list)
    - ``gt`` / ``lt`` / ``gte`` / ``lte`` — numeric comparisons
    - ``contains`` — substring / list membership check
    """

    attribute: str
    operator: Literal["eq", "neq", "in", "not_in", "gt", "lt", "gte", "lte", "contains"]
    value: Any

    model_config = {"frozen": False}

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate this rule against *context*.

        Returns ``True`` when the rule passes, ``False`` otherwise (including
        when the required attribute is missing from context).
        """
        if self.attribute not in context:
            return False

        ctx_val = context[self.attribute]
        op = self.operator

        try:
            if op == "eq":
                return ctx_val == self.value
            if op == "neq":
                return ctx_val != self.value
            if op == "in":
                return ctx_val in self.value
            if op == "not_in":
                return ctx_val not in self.value
            if op == "gt":
                return ctx_val > self.value
            if op == "lt":
                return ctx_val < self.value
            if op == "gte":
                return ctx_val >= self.value
            if op == "lte":
                return ctx_val <= self.value
            if op == "contains":
                return self.value in ctx_val
        except (TypeError, KeyError):
            return False

        return False  # unreachable but satisfies type-checker


class Flag(BaseModel):
    """Represents a single feature flag.

    Args:
        name: Unique identifier (e.g. ``"dark_mode"``).
        enabled: Master on/off switch.
        description: Human-readable description.
        rollout_percentage: Percentage of users who see the flag (0–100).
            Uses deterministic hashing of ``name + user_id`` so the same
            user always gets the same result.
        rules: List of :class:`FlagRule` instances.  All rules must match
            (AND logic).  Evaluated only when ``enabled`` is ``True``.
        metadata: Arbitrary extra data (e.g. owner, ticket).
        created_at: Auto-set on creation.
        updated_at: Auto-set on creation; updated by :class:`FeatureFlags`.
    """

    name: str
    enabled: bool = False
    description: str = ""
    rollout_percentage: int = Field(default=100, ge=0, le=100)
    rules: list[FlagRule] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"frozen": False}

    def _rollout_hash(self, user_id: str) -> int:
        """Return a deterministic 0-99 bucket for *user_id* and this flag."""
        raw = f"{self.name}:{user_id}".encode()
        digest = hashlib.md5(raw).hexdigest()  # noqa: S324 — not security-sensitive
        return int(digest[:8], 16) % 100

    def is_active_for(self, context: dict[str, Any] | None) -> bool:
        """Return whether this flag is active for the given *context*.

        Checks in order:

        1. ``enabled`` is ``True``
        2. Rollout percentage allows this user
        3. All rules pass (if any are defined)
        """
        if not self.enabled:
            return False

        ctx = context or {}

        # Rollout check
        if self.rollout_percentage == 0:
            return False
        if self.rollout_percentage < 100:
            user_id = str(ctx.get("user_id", ""))
            bucket = self._rollout_hash(user_id)
            if bucket >= self.rollout_percentage:
                return False

        # Rule check (AND logic)
        for rule in self.rules:
            if not rule.evaluate(ctx):
                return False

        return True
