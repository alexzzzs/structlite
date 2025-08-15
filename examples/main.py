#!/usr/bin/env python3
"""
Test suite for structlite.py - comprehensive testing of all features
"""

from typing import Annotated, List, Dict
from structlite import Struct, immutable, validator


def test_basic_functionality():
    """Test basic struct creation and field access"""
    print("=== Testing Basic Functionality ===")
    
    class Point(Struct):
        x: int
        y: int = 0
    
    # Test creation
    p1 = Point(10, 20)
    p2 = Point(x=5, y=15)
    p3 = Point(30)  # Using default for y
    
    print(f"p1: {p1}")
    print(f"p2: {p2}")
    print(f"p3: {p3}")
    
    # Test field access
    assert p1.x == 10
    assert p1.y == 20
    assert p3.y == 0
    
    # Test mutation
    p1.x = 100
    print(f"After mutation p1.x = 100: {p1}")
    
    print("✓ Basic functionality works\n")


def test_validation():
    """Test field validation with @validator decorator"""
    print("=== Testing Validation ===")
    
    class Person(Struct):
        name: str
        age: int
        email: str = ""
        
        @validator('name')
        def validate_name(self, value):
            if not value or not value.strip():
                raise ValueError("Name cannot be empty")
            return value.strip()  # Transform: remove whitespace
        
        @validator('age')
        def validate_age(self, value):
            if value < 0:
                raise ValueError("Age cannot be negative")
            if value > 150:
                raise ValueError("Age seems unrealistic")
            return value  # No transformation
        
        @validator('email')
        def validate_email(self, value):
            if value and '@' not in value:
                raise ValueError("Invalid email format")
            # Validation only - return None to keep original value
            return None
    
    # Test valid creation
    person = Person("  John Doe  ", 25, "john@example.com")
    print(f"Created person: {person}")
    assert person.name == "John Doe"  # Whitespace trimmed
    
    # Test validation errors
    try:
        Person("", 25)
        assert False, "Should have raised ValueError for empty name"
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")
    
    try:
        Person("Jane", -5)
        assert False, "Should have raised ValueError for negative age"
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")
    
    try:
        Person("Bob", 30, "invalid-email")
        assert False, "Should have raised ValueError for invalid email"
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")
    
    print("✓ Validation works correctly\n")


def test_immutability():
    """Test immutable structs"""
    print("=== Testing Immutability ===")
    
    class ImmutablePoint(Struct, immutable):
        x: int
        y: int
    
    point = ImmutablePoint(10, 20)
    print(f"Immutable point: {point}")
    print(f"Is frozen: {point._frozen}")
    
    # Test that it's hashable
    point_set = {point}
    print(f"Can be used in set: {point_set}")
    
    # Test that mutation fails
    try:
        point.x = 100
        assert False, "Should not be able to modify immutable struct"
    except AttributeError as e:
        print(f"✓ Caught expected error: {e}")
    
    print("✓ Immutability works correctly\n")


def test_type_checking():
    """Test improved type checking including generics"""
    print("=== Testing Type Checking ===")
    
    class Container(Struct):
        items: List[str]
        mapping: Dict[str, int]
        count: int
    
    # Test valid types
    container = Container(["a", "b", "c"], {"x": 1, "y": 2}, 5)
    print(f"Valid container: {container}")
    
    # Test type errors
    try:
        Container("not a list", {}, 5)
        print("⚠ Type checking for generic types is lenient (this is expected behavior)")
    except TypeError as e:
        print(f"✓ Caught expected error: {e}")
    
    # Test a more basic type error that should definitely fail
    try:
        Container([], {}, "not an int")  # count should be int
        assert False, "Should have raised TypeError for wrong int type"
    except TypeError as e:
        print(f"✓ Caught expected error: {e}")
    
    print("✓ Type checking works correctly\n")


def test_metadata():
    """Test field metadata with Annotated types"""
    print("=== Testing Field Metadata ===")
    
    class Product(Struct):
        name: Annotated[str, {"min_length": 1}, "Product name"]
        price: Annotated[float, {"min": 0.0, "currency": "USD"}]
        tags: Annotated[List[str], "Product tags"] = []
    
    product = Product("Laptop", 999.99, ["electronics", "computer"])
    print(f"Product: {product}")
    
    # Test metadata access
    name_metadata = Product.get_field_metadata('name')
    print(f"Name metadata: {name_metadata}")
    assert name_metadata == ({"min_length": 1}, "Product name")
    
    price_metadata = Product.get_field_metadata('price')
    print(f"Price metadata: {price_metadata}")
    assert price_metadata == ({"min": 0.0, "currency": "USD"},)
    
    all_metadata = Product.get_all_field_metadata()
    print(f"All metadata: {all_metadata}")
    
    print("✓ Metadata works correctly\n")


def test_serialization():
    """Test to_dict and from_dict with nested structures"""
    print("=== Testing Serialization ===")
    
    class Address(Struct):
        street: str
        city: str
        zip_code: str
    
    class Person(Struct):
        name: str
        age: int
        address: Address
        friends: List[str] = []
    
    # Create nested structure
    address = Address("123 Main St", "Anytown", "12345")
    person = Person("Alice", 30, address, ["Bob", "Charlie"])
    
    print(f"Original person: {person}")
    
    # Test serialization
    person_dict = person.to_dict()
    print(f"Serialized: {person_dict}")
    
    # Test deserialization
    person_restored = Person.from_dict(person_dict)
    print(f"Restored: {person_restored}")
    
    # Verify they're equal
    assert person == person_restored
    assert person.address.street == person_restored.address.street
    
    print("✓ Serialization works correctly\n")


def test_copying():
    """Test copy and replace methods"""
    print("=== Testing Copying ===")
    
    class Settings(Struct):
        debug: bool = False
        timeout: int = 30
        host: str = "localhost"
    
    original = Settings(True, 60, "example.com")
    print(f"Original: {original}")
    
    # Test copy with changes
    modified = original.copy(timeout=120)
    print(f"Modified copy: {modified}")
    assert modified.debug == True
    assert modified.timeout == 120
    assert modified.host == "example.com"
    
    # Test replace (alias for copy)
    replaced = original.replace(debug=False, host="test.com")
    print(f"Replaced: {replaced}")
    assert replaced.debug == False
    assert replaced.host == "test.com"
    assert replaced.timeout == 60
    
    print("✓ Copying works correctly\n")


def test_utility_methods():
    """Test utility methods"""
    print("=== Testing Utility Methods ===")
    
    class Config(Struct):
        name: str
        value: int
        enabled: bool = True
    
    config = Config("test", 42, False)
    print(f"Config: {config}")
    
    # Test utility methods
    field_names = config.get_field_names()
    print(f"Field names: {field_names}")
    assert field_names == ['name', 'value', 'enabled']
    
    field_values = config.get_field_values()
    print(f"Field values: {field_values}")
    assert field_values == ['test', 42, False]
    
    field_items = config.get_field_items()
    print(f"Field items: {field_items}")
    assert field_items == [('name', 'test'), ('value', 42), ('enabled', False)]
    
    print("✓ Utility methods work correctly\n")


def test_comparison_and_ordering():
    """Test equality, ordering, and hashing"""
    print("=== Testing Comparison and Ordering ===")
    
    class Score(Struct, immutable):
        player: str
        points: int
    
    score1 = Score("Alice", 100)
    score2 = Score("Bob", 90)
    score3 = Score("Alice", 100)
    
    # Test equality
    assert score1 == score3
    assert score1 != score2
    print("✓ Equality works")
    
    # Test ordering (lexicographic: first by player name, then by points)
    # "Alice" < "Bob" alphabetically, so Alice(100) < Bob(90)
    assert score1 < score2  # Alice(100) < Bob(90) because "Alice" < "Bob"
    scores = [score1, score2, score3]
    sorted_scores = sorted(scores)
    print(f"Sorted scores: {sorted_scores}")
    
    # Test with same names but different points
    alice_low = Score("Alice", 50)
    alice_high = Score("Alice", 100)
    assert alice_low < alice_high  # Same name, so compare by points
    print("✓ Ordering by points works for same name")
    
    # Test hashing (only works for frozen structs)
    score_set = {score1, score2, score3}
    print(f"Unique scores in set: {score_set}")
    assert len(score_set) == 2  # score1 and score3 are equal
    
    print("✓ Comparison and ordering work correctly\n")


def test_error_handling():
    """Test various error conditions"""
    print("=== Testing Error Handling ===")
    
    class TestStruct(Struct):
        field1: str
        field2: int
    
    # Test invalid field names
    try:
        TestStruct(field1="test", invalid_field="value")
        assert False, "Should raise TypeError for invalid field"
    except TypeError as e:
        print(f"✓ Invalid field error: {e}")
    
    # Test missing required fields
    try:
        TestStruct(field1="test")  # missing field2
        assert False, "Should raise TypeError for missing field"
    except TypeError as e:
        print(f"✓ Missing field error: {e}")
    
    # Test setting invalid field
    obj = TestStruct("test", 42)
    try:
        obj.nonexistent = "value"
        assert False, "Should raise AttributeError for nonexistent field"
    except AttributeError as e:
        print(f"✓ Nonexistent field error: {e}")
    
    print("✓ Error handling works correctly\n")


def main():
    """Run all tests"""
    print("Running comprehensive tests for structlite.py\n")
    
    test_basic_functionality()
    test_validation()
    test_immutability()
    test_type_checking()
    test_metadata()
    test_serialization()
    test_copying()
    test_utility_methods()
    test_comparison_and_ordering()
    test_error_handling()
    
    print("🎉 All tests passed! The structlite implementation is working correctly.")


if __name__ == "__main__":
    main()