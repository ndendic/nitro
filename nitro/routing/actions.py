"""
Action string parsing and ActionRef dataclass.

Action string format:
    Entity:id.method    -> instance method call
    Entity.method       -> class method or prefixed standalone
    prefix.function     -> standalone with prefix
    function            -> standalone without prefix
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ActionRef:
    """Parsed representation of an action string."""
    entity: Optional[str] = None
    id: Optional[str] = None
    method: Optional[str] = None
    prefix: Optional[str] = None
    function: Optional[str] = None

    @property
    def is_instance_method(self) -> bool:
        return self.id is not None

    @property
    def event_name(self) -> str:
        if self.entity and self.method:
            return f"{self.entity}.{self.method}"
        if self.prefix and self.function:
            return f"{self.prefix}.{self.function}"
        if self.function:
            return self.function
        raise ValueError("ActionRef has no valid event name")


def parse_action(action: str) -> ActionRef:
    """
    Parse an action string into an ActionRef.

    Examples:
        Counter:abc123.increment -> entity="Counter", id="abc123", method="increment"
        Counter.load_all         -> prefix="Counter", function="load_all"
        auth.register_user       -> prefix="auth", function="register_user"
        health_check             -> function="health_check"
    """
    if ":" in action:
        entity_part, rest = action.split(":", 1)
        id_part, method_part = rest.rsplit(".", 1)
        return ActionRef(entity=entity_part, id=id_part, method=method_part)
    elif "." in action:
        prefix_part, func_part = action.rsplit(".", 1)
        return ActionRef(prefix=prefix_part, function=func_part)
    else:
        return ActionRef(function=action)
