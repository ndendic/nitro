"""
FastHTML adapter — DEPRECATED.

This adapter used the old REST-style routing system.
Use nitro.adapters.catch_all.dispatch_action() instead.
See docs/plans/2026-03-09-smart-routing-design.md for the new architecture.
"""
import warnings


def configure_nitro(*args, **kwargs):
    warnings.warn(
        "This adapter uses the old routing system. "
        "Use the catch-all adapter pattern instead. "
        "See docs/plans/2026-03-09-smart-routing-design.md",
        DeprecationWarning,
        stacklevel=2,
    )
