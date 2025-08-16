"""Basic tests for structlite functionality."""

import sys
from typing import List

import pytest

# Python 3.8 compatibility
if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    try:
        from typing_extensions import Annotated
    except ImportError:
        Annotated = None

from structlite import Struct, immutable, transformer, validator


class TestBasicFunctionality:
    """Test basic struct creation and field access."""

    def test_simple_struct(self):
        """Test creating a simple struct."""

        class Point(Struct):
            x: int
            y: int = 0

        p1 = Point(10, 20)
        p2 = Point(x=5, y=15)
        p3 = Point(30)  # Using default for y

        assert p1.x == 10
        assert p1.y == 20
        assert p2.x == 5
        assert p2.y == 15
        assert p3.x == 30
        assert p3.y == 0

    def test_field_mutation(self):
        """Test field mutation on mutable structs."""

        class Point(Struct):
            x: int
            y: int

        point = Point(10, 20)
        point.x = 100
        assert point.x == 100

    def test_validation(self):
        """Test field validation."""

        class Person(Struct):
            name: str
            age: int

            @validator("age")
            def validate_age(self, value):
                if value < 0:
                    raise ValueError("Age cannot be negative")
                return value

        # Valid creation
        person = Person("Alice", 25)
        assert person.age == 25

        # Invalid creation
        with pytest.raises(ValueError, match="Age cannot be negative"):
            Person("Bob", -5)

    def test_transformers(self):
        """Test field transformers."""

        class Person(Struct):
            name: str
            email: str

            @transformer("name")
            def normalize_name(self, value):
                return value.strip().title()

            @transformer("email")
            def normalize_email(self, value):
                return value.strip().lower()

        person = Person("  john doe  ", "JOHN@EXAMPLE.COM")
        assert person.name == "John Doe"
        assert person.email == "john@example.com"

    def test_immutability(self):
        """Test immutable structs."""

        class ImmutablePoint(Struct, immutable):
            x: int
            y: int

        point = ImmutablePoint(10, 20)
        assert point._frozen is True

        # Test that mutation fails
        with pytest.raises(AttributeError):
            point.x = 100

        # Test that it's hashable
        point_set = {point}
        assert len(point_set) == 1

    def test_serialization(self):
        """Test to_dict and from_dict."""

        class Person(Struct):
            name: str
            age: int
            tags: List[str] = []

        person = Person("Alice", 30, ["developer", "python"])

        # Test serialization
        data = person.to_dict()
        expected = {"name": "Alice", "age": 30, "tags": ["developer", "python"]}
        assert data == expected

        # Test deserialization
        person2 = Person.from_dict(data)
        assert person == person2

    def test_builder_pattern(self):
        """Test fluent builder interface."""

        class Person(Struct):
            name: str
            age: int
            email: str = ""

        person = (
            Person.builder().name("Alice").age(30).email("alice@example.com").build()
        )

        assert person.name == "Alice"
        assert person.age == 30
        assert person.email == "alice@example.com"

    def test_copy_and_replace(self):
        """Test copy and replace methods."""

        class Settings(Struct):
            debug: bool = False
            timeout: int = 30
            host: str = "localhost"

        original = Settings(True, 60, "example.com")

        # Test copy with changes
        modified = original.copy(timeout=120)
        assert modified.debug is True
        assert modified.timeout == 120
        assert modified.host == "example.com"

        # Test replace (alias for copy)
        replaced = original.replace(debug=False, host="test.com")
        assert replaced.debug is False
        assert replaced.host == "test.com"
        assert replaced.timeout == 60

    def test_metadata(self):
        """Test field metadata with Annotated types."""
        if Annotated is None:
            pytest.skip(
                "Annotated not available in Python 3.8 without typing_extensions"
            )

        class Product(Struct):
            name: Annotated[str, {"min_length": 1}, "Product name"]
            price: Annotated[float, {"min": 0.0, "currency": "USD"}]

        # Test metadata access
        name_metadata = Product.get_field_metadata("name")
        assert name_metadata == ({"min_length": 1}, "Product name")

        price_metadata = Product.get_field_metadata("price")
        assert price_metadata == ({"min": 0.0, "currency": "USD"},)

    def test_error_handling(self):
        """Test various error conditions."""

        class TestStruct(Struct):
            field1: str
            field2: int

        # Test invalid field names
        with pytest.raises(TypeError, match="Invalid field"):
            TestStruct(field1="test", invalid_field="value")

        # Test missing required fields
        with pytest.raises(TypeError, match="Missing required field"):
            TestStruct(field1="test")

        # Test setting invalid field
        obj = TestStruct("test", 42)
        with pytest.raises(AttributeError, match="has no field"):
            obj.nonexistent = "value"
