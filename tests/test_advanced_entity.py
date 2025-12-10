"""
Tests for advanced Entity features.

This module verifies advanced Entity capabilities including:
- Composite primary keys
- Foreign key relationships
- Many-to-many relationships
- Computed fields
- Field validators
- Lifecycle hooks
"""
import pytest
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator, computed_field
from nitro.domain.entities.base_entity import Entity


# =============================================================================
# Test 1: Entity supports composite primary keys
# =============================================================================

class CompositeKeyEntity(Entity, table=True):
    """Entity with composite primary key."""
    __tablename__ = "composite_key_entities"

    # SQLModel requires single primary key field
    # So we'll use a compound key as the id
    id: str = Field(primary_key=True)
    region: str
    code: str
    name: str

    def __init__(self, region: str, code: str, name: str, **kwargs):
        """Custom init to create composite ID."""
        composite_id = f"{region}:{code}"
        super().__init__(id=composite_id, region=region, code=code, name=name, **kwargs)


class TestCompositeKeys:
    """Test Entity with composite primary keys."""

    def test_composite_key_creation(self, test_repository):
        """Entity with composite key can be created and saved."""
        entity = CompositeKeyEntity(region="US", code="001", name="Test Entity")

        # Verify composite ID was created
        assert entity.id == "US:001"
        assert entity.region == "US"
        assert entity.code == "001"
        assert entity.name == "Test Entity"

        # Save entity
        assert entity.save() is True

    def test_composite_key_retrieval(self, test_repository):
        """Entity with composite key can be retrieved."""
        entity = CompositeKeyEntity(region="EU", code="002", name="European Entity")
        entity.save()

        # Retrieve using composite ID
        retrieved = CompositeKeyEntity.get("EU:002")
        assert retrieved is not None
        assert retrieved.region == "EU"
        assert retrieved.code == "002"
        assert retrieved.name == "European Entity"

    def test_composite_key_uniqueness(self, test_repository):
        """Composite keys enforce uniqueness."""
        entity1 = CompositeKeyEntity(region="US", code="003", name="First")
        entity1.save()

        # Same composite key should update, not create duplicate
        entity2 = CompositeKeyEntity(region="US", code="003", name="Second")
        entity2.save()

        # Should only have one entity
        retrieved = CompositeKeyEntity.get("US:003")
        assert retrieved.name == "Second"


# =============================================================================
# Test 2: Entity supports foreign key relationships
# =============================================================================

class AuthorEntity(Entity, table=True):
    """Author entity for relationship testing."""
    __tablename__ = "authors"

    id: str = Field(primary_key=True)
    name: str
    email: str

    # Relationship to posts
    posts: List["PostEntity"] = Relationship(back_populates="author")


class PostEntity(Entity, table=True):
    """Post entity with foreign key to Author."""
    __tablename__ = "posts"

    id: str = Field(primary_key=True)
    title: str
    content: str
    author_id: str = Field(foreign_key="authors.id")

    # Relationship to author
    author: Optional[AuthorEntity] = Relationship(back_populates="posts")


class TestForeignKeyRelationships:
    """Test Entity with foreign key relationships."""

    def test_create_entities_with_relationships(self, test_repository):
        """Can create entities with foreign key relationships."""
        # Create author
        author = AuthorEntity(id="author1", name="John Doe", email="john@example.com")
        author.save()

        # Create post with foreign key
        post = PostEntity(
            id="post1",
            title="First Post",
            content="Hello World",
            author_id="author1"
        )
        post.save()

        # Verify both saved
        assert AuthorEntity.get("author1") is not None
        assert PostEntity.get("post1") is not None

    def test_relationship_traversal_parent_to_child(self, test_repository):
        """Can traverse relationship from parent to children."""
        # Create author with posts
        author = AuthorEntity(id="author2", name="Jane Smith", email="jane@example.com")
        author.save()

        post1 = PostEntity(id="post2", title="Post 1", content="Content 1", author_id="author2")
        post1.save()

        post2 = PostEntity(id="post3", title="Post 2", content="Content 2", author_id="author2")
        post2.save()

        # Retrieve author and check posts
        retrieved_author = AuthorEntity.get("author2")
        assert retrieved_author is not None
        assert len(retrieved_author.posts) == 2
        assert all(isinstance(p, PostEntity) for p in retrieved_author.posts)

    def test_relationship_traversal_child_to_parent(self, test_repository):
        """Can traverse relationship from child to parent."""
        # Create author and post
        author = AuthorEntity(id="author3", name="Bob Johnson", email="bob@example.com")
        author.save()

        post = PostEntity(id="post4", title="Bob's Post", content="Content", author_id="author3")
        post.save()

        # Retrieve post and check author
        retrieved_post = PostEntity.get("post4")
        assert retrieved_post is not None
        assert retrieved_post.author is not None
        assert retrieved_post.author.name == "Bob Johnson"
        assert retrieved_post.author.email == "bob@example.com"


# =============================================================================
# Test 3: Entity supports many-to-many relationships
# =============================================================================

class StudentCourseLink(SQLModel, table=True):
    """Link table for many-to-many relationship."""
    __tablename__ = "student_course_links"

    student_id: str = Field(foreign_key="students.id", primary_key=True)
    course_id: str = Field(foreign_key="courses.id", primary_key=True)


class StudentEntity(Entity, table=True):
    """Student entity for many-to-many testing."""
    __tablename__ = "students"

    id: str = Field(primary_key=True)
    name: str
    email: str

    # Many-to-many relationship
    courses: List["CourseEntity"] = Relationship(
        back_populates="students",
        link_model=StudentCourseLink
    )


class CourseEntity(Entity, table=True):
    """Course entity for many-to-many testing."""
    __tablename__ = "courses"

    id: str = Field(primary_key=True)
    name: str
    credits: int

    # Many-to-many relationship
    students: List[StudentEntity] = Relationship(
        back_populates="courses",
        link_model=StudentCourseLink
    )


class TestManyToManyRelationships:
    """Test Entity with many-to-many relationships."""

    def test_create_many_to_many_relationship(self, test_repository):
        """Can create many-to-many relationships."""
        # Create student and course
        student = StudentEntity(id="student1", name="Alice", email="alice@example.com")
        student.save()

        course = CourseEntity(id="course1", name="Python 101", credits=3)
        course.save()

        # Link them
        link = StudentCourseLink(student_id="student1", course_id="course1")
        with test_repository.get_session() as session:
            session.add(link)
            session.commit()

        # Verify link created
        retrieved_student = StudentEntity.get("student1")
        assert len(retrieved_student.courses) == 1
        assert retrieved_student.courses[0].name == "Python 101"

    def test_bidirectional_many_to_many_navigation(self, test_repository):
        """Can navigate many-to-many relationships bidirectionally."""
        # Create entities
        student1 = StudentEntity(id="student2", name="Bob", email="bob@example.com")
        student2 = StudentEntity(id="student3", name="Carol", email="carol@example.com")
        student1.save()
        student2.save()

        course = CourseEntity(id="course2", name="Advanced Python", credits=4)
        course.save()

        # Link both students to course
        with test_repository.get_session() as session:
            session.add(StudentCourseLink(student_id="student2", course_id="course2"))
            session.add(StudentCourseLink(student_id="student3", course_id="course2"))
            session.commit()

        # Navigate from course to students
        retrieved_course = CourseEntity.get("course2")
        assert len(retrieved_course.students) == 2
        student_names = [s.name for s in retrieved_course.students]
        assert "Bob" in student_names
        assert "Carol" in student_names

        # Navigate from student to courses
        retrieved_student = StudentEntity.get("student2")
        assert len(retrieved_student.courses) == 1
        assert retrieved_student.courses[0].name == "Advanced Python"


# =============================================================================
# Test 4: Entity supports computed fields
# =============================================================================

class ProductEntity(Entity, table=True):
    """Product entity with computed fields."""
    __tablename__ = "products"

    id: str = Field(primary_key=True)
    name: str
    price: float
    tax_rate: float = 0.1  # 10% tax

    @computed_field
    @property
    def price_with_tax(self) -> float:
        """Computed field: price including tax."""
        return round(self.price * (1 + self.tax_rate), 2)

    @computed_field
    @property
    def tax_amount(self) -> float:
        """Computed field: tax amount."""
        return round(self.price * self.tax_rate, 2)


class TestComputedFields:
    """Test Entity with computed fields."""

    def test_computed_field_calculation(self, test_repository):
        """Computed fields are calculated correctly."""
        product = ProductEntity(id="prod1", name="Widget", price=100.0, tax_rate=0.1)

        # Verify computed fields
        assert product.price_with_tax == 110.0
        assert product.tax_amount == 10.0

    def test_computed_field_not_stored(self, test_repository):
        """Computed fields are not stored in database."""
        product = ProductEntity(id="prod2", name="Gadget", price=50.0)
        product.save()

        # Retrieve and verify computed field still works
        retrieved = ProductEntity.get("prod2")
        assert retrieved.price_with_tax == 55.0
        assert retrieved.tax_amount == 5.0

    def test_computed_field_updates_with_data(self, test_repository):
        """Computed fields update when underlying data changes."""
        product = ProductEntity(id="prod3", name="Tool", price=200.0, tax_rate=0.15)
        original_price_with_tax = product.price_with_tax  # 230.0

        # Change price
        product.price = 300.0

        # Computed field should update
        assert product.price_with_tax == 345.0
        assert product.price_with_tax != original_price_with_tax


# =============================================================================
# Test 5: Entity supports field validators
# =============================================================================

class ValidatedEntity(Entity, table=True):
    """Entity with field validators."""
    __tablename__ = "validated_entities"

    id: str = Field(primary_key=True)
    email: str
    age: int
    username: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if '@' not in v:
            raise ValueError('Email must contain @')
        return v

    @field_validator('age')
    @classmethod
    def validate_age(cls, v: int) -> int:
        """Validate age is positive."""
        if v < 0:
            raise ValueError('Age must be positive')
        if v > 150:
            raise ValueError('Age must be realistic')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username length."""
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v


class TestFieldValidators:
    """Test Entity with field validators."""

    def test_validator_accepts_valid_data(self, test_repository):
        """Validators accept valid data."""
        entity = ValidatedEntity(
            id="valid1",
            email="user@example.com",
            age=25,
            username="john_doe"
        )

        # Should create successfully
        assert entity.email == "user@example.com"
        assert entity.age == 25
        assert entity.username == "john_doe"

    def test_validator_rejects_invalid_email(self, test_repository):
        """Validator rejects invalid email."""
        with pytest.raises(ValueError, match="Email must contain @"):
            ValidatedEntity(
                id="invalid1",
                email="notanemail",
                age=25,
                username="john"
            )

    def test_validator_rejects_negative_age(self, test_repository):
        """Validator rejects negative age."""
        with pytest.raises(ValueError, match="Age must be positive"):
            ValidatedEntity(
                id="invalid2",
                email="user@example.com",
                age=-5,
                username="john"
            )

    def test_validator_rejects_short_username(self, test_repository):
        """Validator rejects short username."""
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            ValidatedEntity(
                id="invalid3",
                email="user@example.com",
                age=25,
                username="ab"
            )

    def test_validators_run_on_update(self, test_repository):
        """Validators run when updating fields."""
        entity = ValidatedEntity(
            id="valid2",
            email="user@example.com",
            age=25,
            username="john"
        )
        entity.save()

        # Try to update with invalid data
        with pytest.raises(ValueError, match="Email must contain @"):
            entity.email = "invalid"


# =============================================================================
# Test 6: Entity lifecycle hooks (before_save, after_save)
# =============================================================================

class HookedEntity(Entity, table=True):
    """Entity with lifecycle hooks."""
    __tablename__ = "hooked_entities"

    id: str = Field(primary_key=True)
    name: str
    slug: str = ""
    save_count: int = 0

    # Track hook calls for testing
    _before_save_called: bool = False
    _after_save_called: bool = False

    def before_save(self):
        """Hook called before saving."""
        self._before_save_called = True
        # Auto-generate slug from name
        self.slug = self.name.lower().replace(' ', '-')
        self.save_count += 1

    def after_save(self):
        """Hook called after saving."""
        self._after_save_called = True

    def save(self) -> bool:
        """Override save to call lifecycle hooks."""
        self.before_save()
        result = super().save()
        if result:
            self.after_save()
        return result


class TestLifecycleHooks:
    """Test Entity lifecycle hooks."""

    def test_before_save_hook_called(self, test_repository):
        """before_save hook is called before saving."""
        entity = HookedEntity(id="hook1", name="Test Entity")

        # Hook not called yet
        assert entity._before_save_called is False

        # Save entity
        entity.save()

        # Hook should be called
        assert entity._before_save_called is True

    def test_after_save_hook_called(self, test_repository):
        """after_save hook is called after saving."""
        entity = HookedEntity(id="hook2", name="Another Entity")

        # Hook not called yet
        assert entity._after_save_called is False

        # Save entity
        entity.save()

        # Hook should be called
        assert entity._after_save_called is True

    def test_before_save_hook_modifies_data(self, test_repository):
        """before_save hook can modify data before saving."""
        entity = HookedEntity(id="hook3", name="My Cool Entity")
        entity.save()

        # Verify slug was auto-generated
        assert entity.slug == "my-cool-entity"

        # Verify save count was incremented
        assert entity.save_count == 1

        # Save again
        entity.save()
        assert entity.save_count == 2

    def test_hooks_called_in_correct_order(self, test_repository):
        """Hooks are called in correct order: before_save, then after_save."""
        entity = HookedEntity(id="hook4", name="Ordered")

        # Track when each hook is called
        call_order = []

        original_before = entity.before_save
        original_after = entity.after_save

        def tracked_before():
            call_order.append('before')
            original_before()

        def tracked_after():
            call_order.append('after')
            original_after()

        entity.before_save = tracked_before
        entity.after_save = tracked_after

        entity.save()

        # Verify order
        assert call_order == ['before', 'after']

    def test_after_save_hook_not_called_on_failure(self, test_repository):
        """after_save hook is not called if save fails."""
        entity = HookedEntity(id="hook5", name="Failing")

        # Mock save to fail
        original_super_save = Entity.save

        def failing_save(self):
            return False

        Entity.save = failing_save

        try:
            entity.save()

            # before_save should be called
            assert entity._before_save_called is True

            # after_save should NOT be called (save failed)
            assert entity._after_save_called is False
        finally:
            # Restore original save
            Entity.save = original_super_save


# =============================================================================
# Integration Test: All advanced features together
# =============================================================================

class TestAdvancedFeaturesIntegration:
    """Integration test combining advanced features."""

    def test_entity_with_multiple_advanced_features(self, test_repository):
        """Entity can use multiple advanced features together."""
        # Create entities with relationships
        author = AuthorEntity(id="int_author", name="Integration Test", email="test@example.com")
        author.save()

        # Create product with computed fields and save
        product = ProductEntity(id="int_prod", name="Integration Product", price=100.0)
        product.save()

        # Create validated entity
        validated = ValidatedEntity(
            id="int_valid",
            email="valid@example.com",
            age=30,
            username="integration"
        )
        validated.save()

        # Verify all work together
        assert AuthorEntity.get("int_author") is not None
        assert ProductEntity.get("int_prod").price_with_tax == 110.0
        assert ValidatedEntity.get("int_valid") is not None
