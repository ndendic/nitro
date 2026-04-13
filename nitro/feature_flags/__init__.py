"""
nitro.feature_flags — Framework-agnostic feature flag management.

Provides:
- Flag             : Pydantic model representing a feature flag
- FlagRule         : Conditional activation rule (supports 9 operators)
- FlagStore        : Abstract storage backend interface
- MemoryFlagStore  : In-process dict-based store (default)
- FeatureFlags     : Main service class for flag management & evaluation
- FlagDisabledError: Raised by ``require()`` when a flag is inactive
- feature_flag     : Decorator for gating functions behind a flag

Quick start::

    from nitro.feature_flags import FeatureFlags, FlagRule

    flags = FeatureFlags()

    # Simple on/off flag
    flags.create("dark_mode", enabled=True)
    flags.is_enabled("dark_mode")           # True

    # Percentage rollout (deterministic by user_id)
    flags.create("new_ui", enabled=True, rollout_percentage=20)
    flags.is_enabled("new_ui", context={"user_id": "u42"})

    # Rule-based activation
    flags.create(
        "admin_panel",
        enabled=True,
        rules=[FlagRule(attribute="role", operator="eq", value="admin")],
    )
    flags.is_enabled("admin_panel", context={"role": "admin"})   # True
    flags.is_enabled("admin_panel", context={"role": "viewer"})  # False

    # Require (raises FlagDisabledError if inactive)
    flags.require("dark_mode")

    # Toggle
    flags.toggle("dark_mode")

Decorator usage::

    from nitro.feature_flags import FeatureFlags, feature_flag

    flags = FeatureFlags()
    flags.create("new_checkout", enabled=True)

    @feature_flag(flags, "new_checkout", fallback=old_checkout)
    async def new_checkout_handler(request):
        ...
"""

from .models import Flag, FlagRule
from .store import FlagStore, MemoryFlagStore
from .service import FeatureFlags, FlagDisabledError, feature_flag

__all__ = [
    "Flag",
    "FlagRule",
    "FlagStore",
    "MemoryFlagStore",
    "FeatureFlags",
    "FlagDisabledError",
    "feature_flag",
]
