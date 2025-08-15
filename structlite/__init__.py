"""
StructLite - A powerful, flexible struct-like class for Python

A comprehensive struct implementation with validation, immutability, serialization,
async validation, builder pattern, database integration, and field transformers.

Example:
    from structlite import Struct, validator, transformer
    
    class Person(Struct):
        name: str
        age: int
        email: str = ""
        
        @transformer('name')
        def normalize_name(self, value):
            return value.strip().title()
        
        @validator('age')
        def validate_age(self, value):
            if value < 0:
                raise ValueError("Age must be non-negative")
            return value
    
    person = Person("john doe", 25, "john@example.com")
    # name is automatically transformed to "John Doe"
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

from .core import (
    Struct,
    StructBuilder,
    StructMeta,
    immutable,
    validator,
    async_validator,
    transformer,
)

__all__ = [
    "Struct",
    "StructBuilder", 
    "StructMeta",
    "immutable",
    "validator",
    "async_validator",
    "transformer",
]