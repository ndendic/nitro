"""
Simple email template engine.

Provides lightweight template rendering for emails without requiring
Jinja2 or other heavy template engines. Uses Python's ``string.Template``
for variable substitution and a clean HTML wrapper for styled emails.

Example::

    from nitro.email import EmailTemplate, EmailMessage

    welcome = EmailTemplate(
        subject="Welcome, $name!",
        body="Hello $name, your account is ready.",
        html_body=\"\"\"
        <h1>Welcome, $name!</h1>
        <p>Your account is ready. Click <a href="$link">here</a> to get started.</p>
        \"\"\",
    )

    msg = welcome.render(name="Alice", link="https://example.com/start")
    # → EmailMessage with subject, body, and styled HTML

Template registry::

    from nitro.email import TemplateRegistry

    registry = TemplateRegistry()
    registry.register("welcome", welcome)
    registry.register("reset", reset_template)

    msg = registry.render("welcome", to=["alice@example.com"], name="Alice", link="...")
"""

from __future__ import annotations

from string import Template
from typing import Any, Dict, List, Optional

from .base import Attachment, EmailMessage, EmailPriority


class EmailTemplate:
    """A reusable email template with variable substitution.

    Uses ``$variable`` syntax (Python's ``string.Template``).

    Args:
        subject: Subject template string.
        body: Plain-text body template.
        html_body: HTML body template (optional — if omitted, body is used).
        default_from: Sender address for rendered messages.
        default_tags: Tags applied to all rendered messages.
    """

    def __init__(
        self,
        *,
        subject: str,
        body: str = "",
        html_body: str = "",
        default_from: str = "",
        default_tags: List[str] | None = None,
    ):
        self.subject_tpl = Template(subject)
        self.body_tpl = Template(body) if body else None
        self.html_body_tpl = Template(html_body) if html_body else None
        self.default_from = default_from
        self.default_tags = default_tags or []

    def render(
        self,
        *,
        to: List[str] | str | None = None,
        from_addr: str = "",
        cc: List[str] | None = None,
        bcc: List[str] | None = None,
        reply_to: str = "",
        attachments: List[Attachment] | None = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        tags: List[str] | None = None,
        wrap_html: bool = True,
        **variables: Any,
    ) -> EmailMessage:
        """Render the template with the given variables.

        Args:
            to: Recipient(s). Can be set later if building a batch.
            from_addr: Override default sender.
            variables: Template variables (passed as keyword arguments).
            wrap_html: Wrap HTML body in a responsive email wrapper.

        Returns:
            A fully-formed ``EmailMessage`` ready to send.
        """
        subject = self.subject_tpl.safe_substitute(variables)
        body = self.body_tpl.safe_substitute(variables) if self.body_tpl else ""
        html = ""
        if self.html_body_tpl:
            raw_html = self.html_body_tpl.safe_substitute(variables)
            html = _wrap_html(raw_html, subject) if wrap_html else raw_html

        # Normalise `to`
        if to is None:
            to_list: List[str] = []
        elif isinstance(to, str):
            to_list = [to]
        else:
            to_list = list(to)

        return EmailMessage(
            to=to_list,
            subject=subject,
            body=body,
            html=html,
            from_addr=from_addr or self.default_from,
            cc=cc or [],
            bcc=bcc or [],
            reply_to=reply_to,
            attachments=attachments or [],
            priority=priority,
            tags=(tags or []) + self.default_tags,
        )


class TemplateRegistry:
    """Named registry of email templates.

    Provides a central lookup for all application email templates,
    making it easy to manage and render emails by name.
    """

    def __init__(self) -> None:
        self._templates: Dict[str, EmailTemplate] = {}

    def register(self, name: str, template: EmailTemplate) -> None:
        """Register a template under a name."""
        self._templates[name] = template

    def get(self, name: str) -> EmailTemplate:
        """Get a template by name. Raises KeyError if not found."""
        return self._templates[name]

    def render(self, template_name: str, **kwargs: Any) -> EmailMessage:
        """Look up a template by name and render it.

        Args:
            template_name: Registered template name (positional to avoid
                colliding with template variables like ``name``).
            kwargs: Passed through to ``EmailTemplate.render()``.
        """
        tpl = self.get(template_name)
        return tpl.render(**kwargs)

    def list_templates(self) -> List[str]:
        """Return all registered template names."""
        return list(self._templates.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._templates

    def __len__(self) -> int:
        return len(self._templates)


def _wrap_html(content: str, title: str = "") -> str:
    """Wrap raw HTML in a responsive email container.

    Produces clean, portable HTML that works across major email clients.
    """
    return f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.5;
    color: #333333;
    background-color: #f4f4f4;
}}
.email-wrapper {{
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
    background-color: #ffffff;
}}
a {{
    color: #2563eb;
}}
</style>
</head>
<body>
<div class="email-wrapper">
{content}
</div>
</body>
</html>"""
