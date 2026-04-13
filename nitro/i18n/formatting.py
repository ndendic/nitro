"""Message formatting and pluralization."""

from __future__ import annotations


def pluralize(template: str, count: int, locale: str = "en") -> str:
    """Select the correct plural form from a pipe-separated template.

    Supports English-style (2 forms) and Slavic-style (3 forms) pluralization.

    English (2 forms): ``"1 item|{count} items"``
    - Form 0: count == 1
    - Form 1: everything else

    Slavic (3 forms, e.g., Serbian/Russian): ``"stavka|stavke|stavki"``
    - Form 0: count % 10 == 1 and count % 100 != 11
    - Form 1: count % 10 in {2,3,4} and count % 100 not in {12,13,14}
    - Form 2: everything else

    Args:
        template: Pipe-separated plural forms.
        count: The number to pluralize for.
        locale: Locale code for plural rule selection.

    Returns:
        The selected form with ``{count}`` replaced.
    """
    forms = template.split("|")
    n_forms = len(forms)

    if n_forms == 1:
        idx = 0
    elif n_forms == 2:
        idx = _plural_index_en(count)
    elif n_forms >= 3:
        if _is_slavic_locale(locale):
            idx = _plural_index_slavic(count)
        else:
            # Default: treat as 2-form even if 3 given
            idx = _plural_index_en(count)
    else:
        idx = 0

    idx = min(idx, len(forms) - 1)
    return forms[idx].format(count=count)


def format_message(template: str, **kwargs: object) -> str:
    """Format a message template with keyword arguments.

    Uses Python's ``str.format()`` — safe for user-provided templates
    because unknown keys raise KeyError (not arbitrary code execution).

    Args:
        template: The message template with ``{name}`` placeholders.
        **kwargs: Values to substitute.

    Returns:
        The formatted string.
    """
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        # Return template with whatever we could substitute
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


def _plural_index_en(count: int) -> int:
    """English plural rule: 0 for singular, 1 for plural."""
    return 0 if count == 1 else 1


def _plural_index_slavic(count: int) -> int:
    """Slavic plural rule (Serbian, Russian, Ukrainian, etc.)."""
    if count % 10 == 1 and count % 100 != 11:
        return 0
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return 1
    return 2


def _is_slavic_locale(locale: str) -> bool:
    """Check if a locale uses Slavic plural rules."""
    code = locale.split("-")[0].split("_")[0].lower()
    return code in ("sr", "hr", "bs", "ru", "uk", "be", "pl", "cs", "sk")
