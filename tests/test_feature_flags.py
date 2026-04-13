"""
Tests for nitro.feature_flags

Covers:
- Flag CRUD (create, read, update, delete, list)
- is_enabled with no context, with context, with rules
- Rollout percentage (0%, 50%, 100%, deterministic hashing)
- All 9 rule operators
- Rule combinations (AND logic)
- Missing context attributes
- require() raises FlagDisabledError
- toggle()
- feature_flag decorator (enabled, disabled, fallback, async)
- MemoryFlagStore operations
- Edge cases (nonexistent flags, empty store, duplicate creates)
- Flag metadata
- Timestamps (created_at, updated_at)
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from datetime import datetime, timezone

import pytest

from nitro.feature_flags import (
    FeatureFlags,
    Flag,
    FlagDisabledError,
    FlagRule,
    FlagStore,
    MemoryFlagStore,
    feature_flag,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_flags() -> FeatureFlags:
    """Return a fresh FeatureFlags with a clean in-memory store."""
    return FeatureFlags()


def run(coro):
    """Run a coroutine synchronously."""
    return asyncio.run(coro)


# ===========================================================================
# MemoryFlagStore
# ===========================================================================

class TestMemoryFlagStore:
    def test_get_missing(self):
        store = MemoryFlagStore()
        assert store.get("nonexistent") is None

    def test_set_and_get(self):
        store = MemoryFlagStore()
        flag = Flag(name="f1")
        store.set(flag)
        assert store.get("f1") is flag

    def test_delete_existing(self):
        store = MemoryFlagStore()
        store.set(Flag(name="f1"))
        assert store.delete("f1") is True
        assert store.get("f1") is None

    def test_delete_nonexistent(self):
        store = MemoryFlagStore()
        assert store.delete("ghost") is False

    def test_list_all_empty(self):
        store = MemoryFlagStore()
        assert store.list_all() == []

    def test_list_all(self):
        store = MemoryFlagStore()
        store.set(Flag(name="a"))
        store.set(Flag(name="b"))
        names = {f.name for f in store.list_all()}
        assert names == {"a", "b"}

    def test_overwrite_with_set(self):
        store = MemoryFlagStore()
        store.set(Flag(name="f1", enabled=False))
        store.set(Flag(name="f1", enabled=True))
        assert store.get("f1").enabled is True

    def test_store_is_flagstore_subclass(self):
        assert isinstance(MemoryFlagStore(), FlagStore)


# ===========================================================================
# Flag model
# ===========================================================================

class TestFlagModel:
    def test_defaults(self):
        flag = Flag(name="x")
        assert flag.enabled is False
        assert flag.description == ""
        assert flag.rollout_percentage == 100
        assert flag.rules == []
        assert flag.metadata == {}

    def test_created_at_auto(self):
        before = datetime.now(timezone.utc)
        flag = Flag(name="ts")
        after = datetime.now(timezone.utc)
        assert before <= flag.created_at <= after

    def test_updated_at_auto(self):
        flag = Flag(name="ts")
        assert flag.updated_at is not None

    def test_rollout_percentage_validation(self):
        # valid boundaries
        Flag(name="x", rollout_percentage=0)
        Flag(name="x", rollout_percentage=100)

    def test_rollout_percentage_invalid_above(self):
        with pytest.raises(Exception):
            Flag(name="x", rollout_percentage=101)

    def test_rollout_percentage_invalid_below(self):
        with pytest.raises(Exception):
            Flag(name="x", rollout_percentage=-1)

    def test_metadata_stored(self):
        flag = Flag(name="x", metadata={"owner": "alice", "ticket": "T-42"})
        assert flag.metadata["owner"] == "alice"
        assert flag.metadata["ticket"] == "T-42"


# ===========================================================================
# FlagRule model
# ===========================================================================

class TestFlagRuleModel:
    def test_eq_pass(self):
        rule = FlagRule(attribute="role", operator="eq", value="admin")
        assert rule.evaluate({"role": "admin"}) is True

    def test_eq_fail(self):
        rule = FlagRule(attribute="role", operator="eq", value="admin")
        assert rule.evaluate({"role": "user"}) is False

    def test_neq_pass(self):
        rule = FlagRule(attribute="role", operator="neq", value="admin")
        assert rule.evaluate({"role": "user"}) is True

    def test_neq_fail(self):
        rule = FlagRule(attribute="role", operator="neq", value="admin")
        assert rule.evaluate({"role": "admin"}) is False

    def test_in_pass(self):
        rule = FlagRule(attribute="plan", operator="in", value=["pro", "enterprise"])
        assert rule.evaluate({"plan": "pro"}) is True

    def test_in_fail(self):
        rule = FlagRule(attribute="plan", operator="in", value=["pro", "enterprise"])
        assert rule.evaluate({"plan": "free"}) is False

    def test_not_in_pass(self):
        rule = FlagRule(attribute="plan", operator="not_in", value=["pro", "enterprise"])
        assert rule.evaluate({"plan": "free"}) is True

    def test_not_in_fail(self):
        rule = FlagRule(attribute="plan", operator="not_in", value=["pro", "enterprise"])
        assert rule.evaluate({"plan": "pro"}) is False

    def test_gt_pass(self):
        rule = FlagRule(attribute="age", operator="gt", value=18)
        assert rule.evaluate({"age": 19}) is True

    def test_gt_fail(self):
        rule = FlagRule(attribute="age", operator="gt", value=18)
        assert rule.evaluate({"age": 18}) is False

    def test_lt_pass(self):
        rule = FlagRule(attribute="age", operator="lt", value=18)
        assert rule.evaluate({"age": 17}) is True

    def test_lt_fail(self):
        rule = FlagRule(attribute="age", operator="lt", value=18)
        assert rule.evaluate({"age": 18}) is False

    def test_gte_pass_equal(self):
        rule = FlagRule(attribute="score", operator="gte", value=50)
        assert rule.evaluate({"score": 50}) is True

    def test_gte_pass_greater(self):
        rule = FlagRule(attribute="score", operator="gte", value=50)
        assert rule.evaluate({"score": 99}) is True

    def test_gte_fail(self):
        rule = FlagRule(attribute="score", operator="gte", value=50)
        assert rule.evaluate({"score": 49}) is False

    def test_lte_pass_equal(self):
        rule = FlagRule(attribute="score", operator="lte", value=50)
        assert rule.evaluate({"score": 50}) is True

    def test_lte_pass_less(self):
        rule = FlagRule(attribute="score", operator="lte", value=50)
        assert rule.evaluate({"score": 10}) is True

    def test_lte_fail(self):
        rule = FlagRule(attribute="score", operator="lte", value=50)
        assert rule.evaluate({"score": 51}) is False

    def test_contains_substring_pass(self):
        rule = FlagRule(attribute="email", operator="contains", value="@corp.com")
        assert rule.evaluate({"email": "alice@corp.com"}) is True

    def test_contains_substring_fail(self):
        rule = FlagRule(attribute="email", operator="contains", value="@corp.com")
        assert rule.evaluate({"email": "alice@gmail.com"}) is False

    def test_contains_list_pass(self):
        rule = FlagRule(attribute="tags", operator="contains", value="beta")
        assert rule.evaluate({"tags": ["alpha", "beta", "gamma"]}) is True

    def test_contains_list_fail(self):
        rule = FlagRule(attribute="tags", operator="contains", value="delta")
        assert rule.evaluate({"tags": ["alpha", "beta"]}) is False

    def test_missing_attribute_returns_false(self):
        rule = FlagRule(attribute="country", operator="eq", value="US")
        assert rule.evaluate({"role": "admin"}) is False

    def test_missing_attribute_in_empty_context(self):
        rule = FlagRule(attribute="plan", operator="eq", value="pro")
        assert rule.evaluate({}) is False


# ===========================================================================
# FeatureFlags — CRUD
# ===========================================================================

class TestFeatureFlagsCRUD:
    def test_create_returns_flag(self):
        ff = make_flags()
        flag = ff.create("my_flag")
        assert isinstance(flag, Flag)
        assert flag.name == "my_flag"

    def test_create_defaults(self):
        ff = make_flags()
        flag = ff.create("x")
        assert flag.enabled is False
        assert flag.rollout_percentage == 100

    def test_create_custom(self):
        ff = make_flags()
        flag = ff.create("x", enabled=True, description="test", rollout_percentage=50)
        assert flag.enabled is True
        assert flag.description == "test"
        assert flag.rollout_percentage == 50

    def test_create_duplicate_raises(self):
        ff = make_flags()
        ff.create("x")
        with pytest.raises(ValueError, match="already exists"):
            ff.create("x")

    def test_get_existing(self):
        ff = make_flags()
        ff.create("x")
        flag = ff.get("x")
        assert flag is not None
        assert flag.name == "x"

    def test_get_nonexistent(self):
        ff = make_flags()
        assert ff.get("ghost") is None

    def test_update_field(self):
        ff = make_flags()
        ff.create("x", enabled=False)
        updated = ff.update("x", enabled=True)
        assert updated.enabled is True

    def test_update_updates_updated_at(self):
        ff = make_flags()
        ff.create("x")
        flag = ff.get("x")
        original_ts = flag.updated_at
        time.sleep(0.01)
        ff.update("x", description="changed")
        refreshed = ff.get("x")
        assert refreshed.updated_at > original_ts

    def test_update_nonexistent_raises(self):
        ff = make_flags()
        with pytest.raises(KeyError):
            ff.update("ghost", enabled=True)

    def test_delete_existing(self):
        ff = make_flags()
        ff.create("x")
        assert ff.delete("x") is True
        assert ff.get("x") is None

    def test_delete_nonexistent(self):
        ff = make_flags()
        assert ff.delete("ghost") is False

    def test_list_flags_empty(self):
        ff = make_flags()
        assert ff.list_flags() == []

    def test_list_flags(self):
        ff = make_flags()
        ff.create("a")
        ff.create("b")
        ff.create("c")
        names = {f.name for f in ff.list_flags()}
        assert names == {"a", "b", "c"}

    def test_create_with_metadata(self):
        ff = make_flags()
        flag = ff.create("x", metadata={"owner": "team-a"})
        assert flag.metadata["owner"] == "team-a"

    def test_create_with_rules(self):
        ff = make_flags()
        rules = [FlagRule(attribute="role", operator="eq", value="admin")]
        flag = ff.create("x", rules=rules)
        assert len(flag.rules) == 1


# ===========================================================================
# FeatureFlags — is_enabled
# ===========================================================================

class TestIsEnabled:
    def test_disabled_flag(self):
        ff = make_flags()
        ff.create("x", enabled=False)
        assert ff.is_enabled("x") is False

    def test_enabled_flag_no_context(self):
        ff = make_flags()
        ff.create("x", enabled=True)
        assert ff.is_enabled("x") is True

    def test_nonexistent_flag_returns_false(self):
        ff = make_flags()
        assert ff.is_enabled("ghost") is False

    def test_rollout_100_enabled(self):
        ff = make_flags()
        ff.create("x", enabled=True, rollout_percentage=100)
        assert ff.is_enabled("x", context={"user_id": "any"}) is True

    def test_rollout_0_disabled(self):
        ff = make_flags()
        ff.create("x", enabled=True, rollout_percentage=0)
        assert ff.is_enabled("x", context={"user_id": "any"}) is False

    def test_rollout_deterministic_same_user(self):
        """Same user always gets same result."""
        ff = make_flags()
        ff.create("rollout_flag", enabled=True, rollout_percentage=50)
        result_a = ff.is_enabled("rollout_flag", context={"user_id": "user_abc"})
        result_b = ff.is_enabled("rollout_flag", context={"user_id": "user_abc"})
        assert result_a == result_b

    def test_rollout_deterministic_different_users_varied(self):
        """With a 50% rollout, different users should have different outcomes."""
        ff = make_flags()
        ff.create("half", enabled=True, rollout_percentage=50)
        results = set()
        for i in range(100):
            r = ff.is_enabled("half", context={"user_id": f"user_{i:04d}"})
            results.add(r)
            if len(results) == 2:
                break
        # We should see both True and False across 100 users at 50% rollout
        assert True in results and False in results

    def test_rollout_hash_matches_expected(self):
        """Verify the rollout hashing algorithm directly."""
        flag_name = "my_flag"
        user_id = "test_user"
        raw = f"{flag_name}:{user_id}".encode()
        digest = hashlib.md5(raw).hexdigest()
        expected_bucket = int(digest[:8], 16) % 100

        ff = make_flags()
        ff.create(flag_name, enabled=True, rollout_percentage=expected_bucket + 1)
        assert ff.is_enabled(flag_name, context={"user_id": user_id}) is True

        ff2 = make_flags()
        ff2.create(flag_name, enabled=True, rollout_percentage=expected_bucket)
        assert ff2.is_enabled(flag_name, context={"user_id": user_id}) is False

    def test_rollout_no_user_id_uses_empty_string(self):
        """Missing user_id uses empty string — result is deterministic."""
        ff = make_flags()
        ff.create("x", enabled=True, rollout_percentage=50)
        r1 = ff.is_enabled("x", context={})
        r2 = ff.is_enabled("x", context={})
        assert r1 == r2

    def test_rule_passes_enables_flag(self):
        ff = make_flags()
        ff.create(
            "admin_only",
            enabled=True,
            rules=[FlagRule(attribute="role", operator="eq", value="admin")],
        )
        assert ff.is_enabled("admin_only", context={"role": "admin"}) is True

    def test_rule_fails_disables_flag(self):
        ff = make_flags()
        ff.create(
            "admin_only",
            enabled=True,
            rules=[FlagRule(attribute="role", operator="eq", value="admin")],
        )
        assert ff.is_enabled("admin_only", context={"role": "user"}) is False

    def test_multiple_rules_all_must_pass(self):
        """AND logic: all rules must pass."""
        ff = make_flags()
        ff.create(
            "strict",
            enabled=True,
            rules=[
                FlagRule(attribute="role", operator="eq", value="admin"),
                FlagRule(attribute="plan", operator="eq", value="enterprise"),
            ],
        )
        assert ff.is_enabled("strict", context={"role": "admin", "plan": "enterprise"}) is True
        assert ff.is_enabled("strict", context={"role": "admin", "plan": "pro"}) is False
        assert ff.is_enabled("strict", context={"role": "user", "plan": "enterprise"}) is False

    def test_rule_with_missing_attribute_fails(self):
        ff = make_flags()
        ff.create(
            "x",
            enabled=True,
            rules=[FlagRule(attribute="country", operator="eq", value="US")],
        )
        assert ff.is_enabled("x", context={"role": "admin"}) is False

    def test_rules_not_evaluated_when_disabled(self):
        """Rules are irrelevant if enabled=False."""
        ff = make_flags()
        ff.create(
            "x",
            enabled=False,
            rules=[FlagRule(attribute="role", operator="eq", value="admin")],
        )
        assert ff.is_enabled("x", context={"role": "admin"}) is False

    def test_enabled_with_none_context(self):
        ff = make_flags()
        ff.create("x", enabled=True)
        assert ff.is_enabled("x", context=None) is True


# ===========================================================================
# toggle()
# ===========================================================================

class TestToggle:
    def test_toggle_disabled_to_enabled(self):
        ff = make_flags()
        ff.create("x", enabled=False)
        flag = ff.toggle("x")
        assert flag.enabled is True

    def test_toggle_enabled_to_disabled(self):
        ff = make_flags()
        ff.create("x", enabled=True)
        flag = ff.toggle("x")
        assert flag.enabled is False

    def test_toggle_twice_returns_original(self):
        ff = make_flags()
        ff.create("x", enabled=True)
        ff.toggle("x")
        flag = ff.toggle("x")
        assert flag.enabled is True

    def test_toggle_nonexistent_raises(self):
        ff = make_flags()
        with pytest.raises(KeyError):
            ff.toggle("ghost")

    def test_toggle_updates_updated_at(self):
        ff = make_flags()
        ff.create("x", enabled=False)
        original_ts = ff.get("x").updated_at
        time.sleep(0.01)
        ff.toggle("x")
        assert ff.get("x").updated_at > original_ts


# ===========================================================================
# require()
# ===========================================================================

class TestRequire:
    def test_require_enabled_returns_true(self):
        ff = make_flags()
        ff.create("x", enabled=True)
        assert ff.require("x") is True

    def test_require_disabled_raises(self):
        ff = make_flags()
        ff.create("x", enabled=False)
        with pytest.raises(FlagDisabledError) as exc_info:
            ff.require("x")
        assert exc_info.value.flag_name == "x"

    def test_require_nonexistent_raises(self):
        ff = make_flags()
        with pytest.raises(FlagDisabledError) as exc_info:
            ff.require("ghost")
        assert exc_info.value.flag_name == "ghost"

    def test_require_includes_context_in_error(self):
        ff = make_flags()
        ff.create("x", enabled=False)
        ctx = {"user_id": "u1"}
        with pytest.raises(FlagDisabledError) as exc_info:
            ff.require("x", context=ctx)
        assert exc_info.value.context == ctx

    def test_require_with_failing_rule_raises(self):
        ff = make_flags()
        ff.create(
            "x",
            enabled=True,
            rules=[FlagRule(attribute="role", operator="eq", value="admin")],
        )
        with pytest.raises(FlagDisabledError):
            ff.require("x", context={"role": "user"})

    def test_flag_disabled_error_message(self):
        ff = make_flags()
        ff.create("dark_mode", enabled=False)
        with pytest.raises(FlagDisabledError) as exc_info:
            ff.require("dark_mode")
        assert "dark_mode" in str(exc_info.value)


# ===========================================================================
# feature_flag decorator
# ===========================================================================

class TestFeatureFlagDecorator:
    def test_decorator_enabled_sync(self):
        ff = make_flags()
        ff.create("x", enabled=True)

        @feature_flag(ff, "x")
        def handler():
            return "new"

        assert handler() == "new"

    def test_decorator_disabled_sync_raises(self):
        ff = make_flags()
        ff.create("x", enabled=False)

        @feature_flag(ff, "x")
        def handler():
            return "new"

        with pytest.raises(FlagDisabledError):
            handler()

    def test_decorator_disabled_sync_fallback(self):
        ff = make_flags()
        ff.create("x", enabled=False)

        def old_handler():
            return "old"

        @feature_flag(ff, "x", fallback=old_handler)
        def new_handler():
            return "new"

        assert new_handler() == "old"

    def test_decorator_enabled_async(self):
        ff = make_flags()
        ff.create("x", enabled=True)

        @feature_flag(ff, "x")
        async def handler():
            return "new_async"

        result = run(handler())
        assert result == "new_async"

    def test_decorator_disabled_async_raises(self):
        ff = make_flags()
        ff.create("x", enabled=False)

        @feature_flag(ff, "x")
        async def handler():
            return "new_async"

        with pytest.raises(FlagDisabledError):
            run(handler())

    def test_decorator_disabled_async_fallback(self):
        ff = make_flags()
        ff.create("x", enabled=False)

        async def old_handler():
            return "old_async"

        @feature_flag(ff, "x", fallback=old_handler)
        async def new_handler():
            return "new_async"

        assert run(new_handler()) == "old_async"

    def test_decorator_sync_fallback_from_async_decorated(self):
        """Async func with sync fallback."""
        ff = make_flags()
        ff.create("x", enabled=False)

        def old_sync():
            return "old_sync"

        @feature_flag(ff, "x", fallback=old_sync)
        async def new_handler():
            return "new_async"

        assert run(new_handler()) == "old_sync"

    def test_decorator_with_context_extractor(self):
        ff = make_flags()
        ff.create(
            "admin",
            enabled=True,
            rules=[FlagRule(attribute="role", operator="eq", value="admin")],
        )

        def extract(req):
            return {"role": req.get("role")}

        @feature_flag(ff, "admin", context_extractor=extract)
        def handler(req):
            return "admin_view"

        assert handler({"role": "admin"}) == "admin_view"

        with pytest.raises(FlagDisabledError):
            handler({"role": "user"})

    def test_decorator_preserves_func_name(self):
        ff = make_flags()
        ff.create("x", enabled=True)

        @feature_flag(ff, "x")
        def my_special_handler():
            pass

        assert my_special_handler.__name__ == "my_special_handler"

    def test_decorator_passes_args(self):
        ff = make_flags()
        ff.create("x", enabled=True)

        @feature_flag(ff, "x")
        def add(a, b):
            return a + b

        assert add(2, 3) == 5


# ===========================================================================
# Edge cases
# ===========================================================================

class TestEdgeCases:
    def test_empty_store_list(self):
        ff = make_flags()
        assert ff.list_flags() == []

    def test_create_flag_with_all_options(self):
        ff = make_flags()
        rules = [
            FlagRule(attribute="plan", operator="in", value=["pro", "enterprise"]),
            FlagRule(attribute="country", operator="neq", value="CN"),
        ]
        flag = ff.create(
            "full_flag",
            enabled=True,
            description="Full featured flag",
            rollout_percentage=75,
            rules=rules,
            metadata={"owner": "platform", "jira": "PLAT-123"},
        )
        assert flag.rollout_percentage == 75
        assert len(flag.rules) == 2
        assert flag.metadata["jira"] == "PLAT-123"

    def test_is_enabled_after_delete(self):
        ff = make_flags()
        ff.create("x", enabled=True)
        ff.delete("x")
        assert ff.is_enabled("x") is False

    def test_update_rollout_percentage(self):
        ff = make_flags()
        ff.create("x", enabled=True, rollout_percentage=100)
        ff.update("x", rollout_percentage=0)
        assert ff.is_enabled("x", context={"user_id": "anyone"}) is False

    def test_update_metadata(self):
        ff = make_flags()
        ff.create("x", metadata={"v": 1})
        ff.update("x", metadata={"v": 2, "new": True})
        flag = ff.get("x")
        assert flag.metadata["v"] == 2
        assert flag.metadata["new"] is True

    def test_update_rules(self):
        ff = make_flags()
        ff.create("x", enabled=True)
        ff.update("x", rules=[FlagRule(attribute="role", operator="eq", value="admin")])
        assert ff.is_enabled("x", context={"role": "user"}) is False
        assert ff.is_enabled("x", context={"role": "admin"}) is True

    def test_created_at_unchanged_after_update(self):
        ff = make_flags()
        flag = ff.create("x")
        original_created = flag.created_at
        time.sleep(0.01)
        ff.update("x", description="changed")
        assert ff.get("x").created_at == original_created

    def test_flag_disabled_error_is_exception(self):
        err = FlagDisabledError("test_flag")
        assert isinstance(err, Exception)
        assert err.flag_name == "test_flag"
        assert err.context is None

    def test_rollout_50_distributes_roughly_evenly(self):
        """At 50% rollout, roughly half of a large user set should be enabled."""
        ff = make_flags()
        ff.create("half", enabled=True, rollout_percentage=50)
        enabled_count = sum(
            1 for i in range(1000)
            if ff.is_enabled("half", context={"user_id": f"u{i}"})
        )
        # Allow wide margin: expect between 35% and 65% enabled
        assert 350 <= enabled_count <= 650, f"Expected ~500, got {enabled_count}"

    def test_flag_with_zero_rules_and_enabled(self):
        ff = make_flags()
        ff.create("simple", enabled=True)
        assert ff.is_enabled("simple") is True

    def test_custom_store_injected(self):
        custom_store = MemoryFlagStore()
        custom_store.set(Flag(name="injected", enabled=True))
        ff = FeatureFlags(store=custom_store)
        assert ff.is_enabled("injected") is True

    def test_is_enabled_with_empty_context_dict(self):
        ff = make_flags()
        ff.create("x", enabled=True)
        assert ff.is_enabled("x", context={}) is True

    def test_rule_numeric_boundary(self):
        ff = make_flags()
        ff.create(
            "age_gate",
            enabled=True,
            rules=[FlagRule(attribute="age", operator="gte", value=18)],
        )
        assert ff.is_enabled("age_gate", context={"age": 18}) is True
        assert ff.is_enabled("age_gate", context={"age": 17}) is False
