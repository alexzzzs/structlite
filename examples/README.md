# StructLite Examples

This directory contains comprehensive examples demonstrating all features of StructLite.

## Files

- **`main.py`** - Basic functionality tests and examples
- **`advanced_example.py`** - Advanced features with nested structures
- **`cool_features_demo.py`** - Demonstration of the 4 cool features:
  - Field Transformers
  - Async Validation
  - Builder Pattern
  - Database Integration

## Running Examples

```bash
# Basic functionality
python examples/main.py

# Advanced features
python examples/advanced_example.py

# Cool features demo
python examples/cool_features_demo.py
```

## What You'll Learn

### Basic Features
- Creating structs with type checking
- Field validation with `@validator`
- Immutable structs
- Serialization and deserialization
- Copying and field modification

### Advanced Features
- Field metadata with `Annotated` types
- Complex nested structures
- Inheritance and field propagation
- Error handling and validation

### Cool Features
- **Transformers**: Automatic data cleaning and conversion
- **Async Validation**: Database checks and API validation
- **Builder Pattern**: Fluent interface for readable code
- **Database Integration**: SQL generation and row mapping

Each example is fully documented and demonstrates real-world usage patterns.