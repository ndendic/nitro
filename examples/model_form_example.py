"""Example demonstrating ModelForm component usage.

This example shows:
- Creating a form from an Entity class
- Pre-populating a form with instance values
- Displaying validation errors
- Using custom signals
"""

from pydantic import Field
from nitro.domain.entities.base_entity import Entity
from nitro.html.components.model_views import ModelForm
from rusty_tags.datastar import Signals


# Define an example Entity
class User(Entity, table=True):
    """Example user entity."""
    __tablename__ = "users"

    name: str = Field(
        title="Full Name",
        description="Enter your full name"
    )
    email: str = Field(
        title="Email Address",
        json_schema_extra={'format': 'email'}
    )
    age: int = Field(
        default=0,
        ge=0,
        le=150,
        title="Age",
        description="Your age in years"
    )
    is_active: bool = Field(
        default=True,
        title="Active Status"
    )
    bio: str = Field(
        default="",
        description="Tell us about yourself",
        json_schema_extra={'component': 'textarea', 'order': 10}
    )


def example_create_form():
    """Example: Create mode - new entity form."""
    print("=== Create Mode ===")
    form = ModelForm(User)
    print(str(form)[:500] + "...")
    print()


def example_edit_form():
    """Example: Edit mode - pre-populated form."""
    print("=== Edit Mode ===")

    # Create a user instance
    user = User(
        id="user-1",
        name="John Doe",
        email="john@example.com",
        age=30,
        is_active=True,
        bio="Software developer"
    )

    form = ModelForm(User, instance=user)
    print(str(form)[:500] + "...")
    print()


def example_validation_errors():
    """Example: Form with validation errors."""
    print("=== Validation Errors ===")

    # Create a valid instance first
    user = User(
        id="user-2",
        name="Test User",
        email="test@example.com",
        age=30,
        is_active=False,
        bio=""
    )

    # Simulate validation errors that would come from form submission
    errors = {
        'name': 'Name is required',
        'email': 'Invalid email format',
        'age': 'Age must be between 0 and 150'
    }

    form = ModelForm(User, instance=user, errors=errors)
    html = str(form)

    # Show that errors are in the output
    print("Errors present in form:")
    for field, error in errors.items():
        if error in html:
            print(f"  ✓ {field}: {error}")
    print()


def example_custom_signals():
    """Example: Using external signals."""
    print("=== External Signals ===")

    # Create signals with custom values
    my_signals = Signals(
        name='Alice Smith',
        email='alice@example.com',
        age=25,
        is_active=True,
        bio='Designer'
    )

    form = ModelForm(User, signals=my_signals)
    print(str(form)[:500] + "...")
    print()


def example_read_only():
    """Example: Read-only form."""
    print("=== Read-Only Mode ===")

    user = User(
        id="user-3",
        name="Bob Johnson",
        email="bob@example.com",
        age=35,
        is_active=True,
        bio="Manager"
    )

    form = ModelForm(User, instance=user, read_only=True)
    html = str(form)

    # Check for disabled attribute
    if 'disabled' in html:
        print("✓ All fields are disabled")
    print()


def example_exclude_fields():
    """Example: Excluding specific fields."""
    print("=== Exclude Fields ===")

    form = ModelForm(User, exclude_fields=['id', 'bio'])
    html = str(form)

    # Verify bio is not in output
    if 'bio' not in html:
        print("✓ Bio field successfully excluded")
    if 'name' in html:
        print("✓ Other fields present")
    print()


if __name__ == "__main__":
    print("ModelForm Component Examples")
    print("=" * 50)
    print()

    example_create_form()
    example_edit_form()
    example_validation_errors()
    example_custom_signals()
    example_read_only()
    example_exclude_fields()

    print("=" * 50)
    print("All examples completed successfully!")
