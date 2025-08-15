#!/usr/bin/env python3
"""
Advanced example demonstrating the full power of structlite
"""

from typing import Annotated, List, Dict, Optional
from structlite import Struct, immutable, validator
import json


# Example 1: Configuration system with validation and metadata
class DatabaseConfig(Struct):
    host: Annotated[str, {"description": "Database host"}] = "localhost"
    port: Annotated[int, {"min": 1, "max": 65535}] = 5432
    username: str
    password: Annotated[str, {"sensitive": True}]
    max_connections: Annotated[int, {"min": 1, "max": 1000}] = 10
    
    @validator('port')
    def validate_port(self, value):
        metadata = self.get_field_metadata('port')[0]
        if not (metadata["min"] <= value <= metadata["max"]):
            raise ValueError(f"Port must be between {metadata['min']} and {metadata['max']}")
        return value
    
    @validator('password')
    def validate_password(self, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


# Example 2: Immutable data structures for API responses
class APIResponse(Struct, immutable):
    status: int
    message: str
    data: Optional[Dict] = None
    timestamp: str
    
    @validator('status')
    def validate_status(self, value):
        if not (100 <= value <= 599):
            raise ValueError("Invalid HTTP status code")
        return value


# Example 3: Complex nested structures with serialization
class Address(Struct):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"


class Contact(Struct):
    email: Annotated[str, {"format": "email"}]
    phone: Annotated[str, {"format": "phone"}] = ""
    
    @validator('email')
    def validate_email(self, value):
        if '@' not in value or '.' not in value.split('@')[1]:
            raise ValueError("Invalid email format")
        return value.lower()


class Person(Struct):
    first_name: str
    last_name: str
    age: Annotated[int, {"min": 0, "max": 150}]
    address: Address
    contact: Contact
    tags: List[str] = []
    
    @validator('first_name', 'last_name')
    def validate_names(self, value):
        if not value or not value.strip():
            raise ValueError("Name cannot be empty")
        return value.strip().title()
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


def demonstrate_features():
    print("=== Advanced structlite Features Demo ===\n")
    
    # 1. Configuration with validation
    print("1. Configuration System:")
    try:
        config = DatabaseConfig(
            username="admin",
            password="secretpassword123",
            port=5432,
            max_connections=50
        )
        print(f"   Valid config: {config}")
        
        # Show metadata
        port_meta = DatabaseConfig.get_field_metadata('port')
        print(f"   Port metadata: {port_meta}")
        
    except ValueError as e:
        print(f"   Validation error: {e}")
    
    # 2. Immutable API responses
    print("\n2. Immutable API Response:")
    response = APIResponse(
        status=200,
        message="Success",
        data={"users": [{"id": 1, "name": "Alice"}]},
        timestamp="2024-01-15T10:30:00Z"
    )
    print(f"   Response: {response}")
    
    # Create a hashable version without the dict data
    hashable_response = APIResponse(
        status=200,
        message="Success",
        data=None,  # None is hashable
        timestamp="2024-01-15T10:30:00Z"
    )
    print(f"   Hashable response: {hash(hashable_response) is not None}")
    
    # 3. Complex nested structures
    print("\n3. Complex Nested Structures:")
    address = Address(
        street="123 Main St",
        city="Springfield",
        state="IL",
        zip_code="62701"
    )
    
    contact = Contact(
        email="JOHN.DOE@EXAMPLE.COM",  # Will be lowercased
        phone="555-1234"
    )
    
    person = Person(
        first_name="  john  ",  # Will be trimmed and title-cased
        last_name="doe",       # Will be title-cased
        age=30,
        address=address,
        contact=contact,
        tags=["developer", "python"]
    )
    
    print(f"   Person: {person}")
    print(f"   Full name: {person.full_name}")
    print(f"   Email (normalized): {person.contact.email}")
    
    # 4. Serialization and deserialization
    print("\n4. Serialization:")
    person_dict = person.to_dict()
    print(f"   Serialized to dict: {json.dumps(person_dict, indent=2)}")
    
    # Restore from dict
    person_restored = Person.from_dict(person_dict)
    print(f"   Restored from dict: {person_restored}")
    print(f"   Are equal: {person == person_restored}")
    
    # 5. Copying with modifications
    print("\n5. Copying with Changes:")
    person_older = person.copy(age=35)
    person_moved = person.replace(
        address=Address("456 Oak Ave", "Chicago", "IL", "60601")
    )
    print(f"   Older person: {person_older}")
    print(f"   Moved person: {person_moved}")
    
    # 6. Utility methods
    print("\n6. Utility Methods:")
    print(f"   Field names: {person.get_field_names()}")
    print(f"   Field items: {person.get_field_items()[:2]}...")  # Show first 2
    
    # 7. Error handling
    print("\n7. Error Handling:")
    try:
        Person("", "Smith", 25, address, contact)
    except ValueError as e:
        print(f"   Caught validation error: {e}")
    
    try:
        invalid_response = APIResponse(999, "Invalid", timestamp="now")
    except ValueError as e:
        print(f"   Caught status validation error: {e}")


if __name__ == "__main__":
    demonstrate_features()