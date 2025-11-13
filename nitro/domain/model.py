from pydantic import BaseModel, ConfigDict
from datetime import datetime

class Model(BaseModel):
    """
    Pure validation and serialization layer (like Rails ActiveModel).
    NO persistence, NO signals - just data validation.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        validate_assignment=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

    id: str