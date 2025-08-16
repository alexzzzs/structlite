# StructLite 🚀

[![PyPI version](https://badge.fury.io/py/structlite.svg)](https://badge.fury.io/py/structlite)
[![Python versions](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/structlite/workflows/Tests/badge.svg)](https://github.com/yourusername/structlite/actions)

A powerful, flexible struct-like class for Python with validation, immutability, serialization, async validation, builder pattern, database integration, and field transformers.

## ✨ Features

- **🔒 Type Safety**: Automatic type checking based on annotations
- **✅ Field Validation**: Custom validators with `@validator` decorator  
- **🔄 Field Transformers**: Automatic data conversion and normalization
- **⚡ Async Validation**: Support for async validators (database checks, API calls)
- **🏗️ Builder Pattern**: Fluent interface for creating instances
- **🗄️ Database Integration**: Built-in SQL generation and row mapping
- **❄️ Immutability**: Optional immutability with `immutable` base class
- **📦 Serialization**: Built-in `to_dict()` and `from_dict()` methods
- **🧬 Inheritance**: Support for field and default inheritance
- **📊 Field Metadata**: Support for `Annotated` types with metadata
- **⚡ Performance**: Uses `__slots__` for memory efficiency
- **🐍 Pure Python**: No external dependencies

## 🚀 Quick Start

```bash
pip install structlite
```

```python
from structlite import Struct, validator, transformer
from typing import Annotated
from datetime import date

class Person(Struct):
    name: str
    birth_date: date
    email: Annotated[str, {"format": "email"}]
    age: int = 0
    
    @transformer('name')
    def normalize_name(self, value):
        return value.strip().title()
    
    @transformer('birth_date')
    def parse_date(self, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()
        return value
    
    @validator('age')
    def validate_age(self, value):
        if value < 0:
            raise ValueError("Age cannot be negative")
        return value

# Create with automatic transformations
person = Person(
    name="  john doe  ",        # → "John Doe"
    birth_date="1990-05-15",    # → date(1990, 5, 15)
    email="john@example.com",
    age=25
)

print(person)
# Person(name='John Doe', birth_date=datetime.date(1990, 5, 15), email='john@example.com', age=25)
```

## 🏗️ Builder Pattern

Create instances with a fluent, readable interface:

```python
person = (Person.builder()
    .name("Alice Smith")
    .birth_date("1985-03-20")
    .email("alice@example.com")
    .age(30)
    .build())
```

## ⚡ Async Validation

Perfect for database uniqueness checks and API validation:

```python
from structlite import Struct, async_validator

class User(Struct):
    username: str
    email: str
    
    @async_validator('username')
    async def validate_username_unique(self, value):
        exists = await database.check_username_exists(value)
        if exists:
            raise ValueError(f"Username '{value}' already exists")
        return value

# Create with async validation
user = await User.create_async(
    username="newuser",
    email="user@example.com"
)
```

## 🗄️ Database Integration

Seamless SQL database integration:

```python
class Product(Struct):
    id: Optional[int] = None
    name: str
    price: float
    category: str

# Create from database row
product = Product.from_db_row(cursor.fetchone())

# Generate SQL statements
sql, values = product.to_sql_insert('products', exclude_fields=['id'])
cursor.execute(sql, values)

# Update statements
sql, values = product.to_sql_update('products', 'id')
cursor.execute(sql, values)
```

## ❄️ Immutability

Create immutable data structures:

```python
from structlite import Struct, immutable

class Point(Struct, immutable):
    x: int
    y: int

point = Point(10, 20)
# point.x = 30  # ❌ Raises AttributeError - immutable!

# Immutable structs are hashable
points = {point}  # ✅ Works!
```

## 📦 Serialization

Built-in serialization with nested struct support:

```python
# Convert to dictionary
data = person.to_dict()

# Create from dictionary  
person2 = Person.from_dict(data)

# Works with nested structures
class Company(Struct):
    name: str
    employees: List[Person]

company = Company("Tech Corp", [person])
company_data = company.to_dict(recursive=True)
```

## 🔄 Field Transformers

Automatically clean and convert data:

```python
class User(Struct):
    email: str
    phone: str
    
    @transformer('email')
    def normalize_email(self, value):
        return value.strip().lower()
    
    @transformer('phone')
    def format_phone(self, value):
        # Remove all non-digits and format
        digits = ''.join(filter(str.isdigit, value))
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return value

user = User(
    email="  ALICE@EXAMPLE.COM  ",  # → "alice@example.com"
    phone="5551234567"              # → "(555) 123-4567"
)
```

## 📊 Field Metadata

Rich metadata support with `Annotated` types:

```python
from typing import Annotated

class Product(Struct):
    name: Annotated[str, {"min_length": 1}, "Product name"]
    price: Annotated[float, {"min": 0, "currency": "USD"}]

# Access metadata
metadata = Product.get_field_metadata('price')
# ({'min': 0, 'currency': 'USD'},)
```

## 🧬 Inheritance

Full support for inheritance with field and default propagation:

```python
class BaseModel(Struct):
    id: int
    created_at: datetime

class User(BaseModel):
    username: str
    email: str

# User inherits id and created_at fields
user = User(1, datetime.now(), "alice", "alice@example.com")
```

## 🎯 Real-World Example

Here's a complete example showing multiple features working together:

```python
import asyncio
from datetime import datetime, date
from typing import Optional, Annotated
from structlite import Struct, validator, async_validator, transformer

class User(Struct):
    id: Optional[int] = None
    username: Annotated[str, {"min_length": 3, "max_length": 20}]
    email: Annotated[str, {"format": "email"}]
    full_name: str
    birth_date: date
    created_at: Optional[datetime] = None
    is_verified: bool = False
    
    # Transform input data
    @transformer('username', 'email')
    def normalize_credentials(self, value):
        return value.strip().lower()
    
    @transformer('full_name')
    def normalize_name(self, value):
        return value.strip().title()
    
    @transformer('birth_date')
    def parse_birth_date(self, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()
        return value
    
    # Sync validation
    @validator('username')
    def validate_username_format(self, value):
        if not value.isalnum():
            raise ValueError("Username must be alphanumeric")
        return value
    
    # Async validation for uniqueness
    @async_validator('username')
    async def validate_username_unique(self, value):
        exists = await check_username_exists(value)
        if exists:
            raise ValueError("Username already exists")
        return value
    
    @async_validator('email')
    async def validate_email_unique(self, value):
        exists = await check_email_exists(value)
        if exists:
            raise ValueError("Email already registered")
        return value

async def register_user(data):
    # Create user with fluent builder and async validation
    user = await (User.builder()
        .username(data['username'])
        .email(data['email'])
        .full_name(data['full_name'])
        .birth_date(data['birth_date'])
        .build_async())
    
    # Save to database
    sql, values = user.to_sql_insert('users', exclude_fields=['id', 'created_at'])
    await database.execute(sql, values)
    
    return user
```

## 📚 Documentation

### Core Classes

- **`Struct`**: Main struct class with all features
- **`StructBuilder`**: Fluent builder for creating instances
- **`immutable`**: Marker class for immutable structs

### Decorators

- **`@validator(*fields)`**: Sync field validation
- **`@async_validator(*fields)`**: Async field validation  
- **`@transformer(*fields)`**: Field transformation

### Methods

- **`to_dict(recursive=True)`**: Convert to dictionary
- **`from_dict(data)`**: Create from dictionary
- **`copy(**changes)`**: Create copy with modifications
- **`builder()`**: Create fluent builder
- **`create_async(**kwargs)`**: Create with async validation
- **`from_db_row(row)`**: Create from database row
- **`to_sql_insert(table, exclude_fields)`**: Generate INSERT SQL
- **`to_sql_update(table, where_field)`**: Generate UPDATE SQL

## 🧪 Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=structlite

# Type checking
mypy structlite

# Code formatting
black structlite
isort structlite
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Python's `dataclasses` and `attrs`
- Built with modern Python type hints and async/await
- Designed for developer productivity and code clarity

## 📈 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

---

**StructLite** - Making Python structs powerful, flexible, and fun to use! 🚀