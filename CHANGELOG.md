# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-08

### Added
- Initial release of StructLite
- Core `Struct` class with type checking and validation
- `@validator` decorator for field validation
- `@transformer` decorator for field transformation
- `@async_validator` decorator for async validation
- `immutable` marker class for immutable structs
- Fluent builder pattern with `StructBuilder`
- Database integration with `from_db_row()`, `to_sql_insert()`, `to_sql_update()`
- Serialization with `to_dict()` and `from_dict()`
- Field metadata support with `Annotated` types
- Inheritance support for fields and defaults
- Memory-efficient implementation with `__slots__`
- Comprehensive error handling with detailed messages
- Support for Union and Optional types
- Utility methods: `copy()`, `replace()`, `get_field_names()`, etc.
- Full async/await support for validation
- Pure Python implementation with no external dependencies

### Features
- **Type Safety**: Automatic type checking based on annotations
- **Field Validation**: Custom sync and async validators
- **Field Transformers**: Automatic data conversion and normalization
- **Builder Pattern**: Fluent interface for creating instances
- **Database Integration**: SQL generation and row mapping
- **Immutability**: Optional immutable structs with hashing support
- **Serialization**: Recursive serialization of nested structures
- **Metadata**: Rich field metadata with `Annotated` types
- **Performance**: Optimized for speed and memory usage

### Supported Python Versions
- Python 3.8+
- Full type hint support
- Async/await compatibility

### Documentation
- Comprehensive README with examples
- API documentation with type hints
- Real-world usage examples
- Database integration examples
- Async validation examples