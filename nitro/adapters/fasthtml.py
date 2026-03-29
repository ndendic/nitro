"""
FastHTML adapter — DEPRECATED.

FastHTML is built on Starlette. Use the Starlette adapter instead:
    from nitro.adapters.starlette import configure_nitro
"""
import warnings


def configure_nitro(*args, **kwargs):
    warnings.warn(
        "FastHTML is built on Starlette. "
        "Use nitro.adapters.starlette.configure_nitro instead.",
        DeprecationWarning,
        stacklevel=2,
    )
