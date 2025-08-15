#!/usr/bin/env python3
"""
Demo of the cool new features in structlite:
1. Async Validation
2. Struct Builders (Fluent Interface)
3. Database Integration
4. Field Transformers
"""

import asyncio
import sqlite3
from datetime import datetime, date
from typing import Annotated, Optional
from structlite import Struct, immutable, validator, async_validator, transformer


# --- Feature 1: Field Transformers ---
class Person(Struct):
    name: str
    birth_date: date
    age: Optional[int] = None
    email: str = ""
    
    @transformer('birth_date')
    def parse_birth_date(self, value):
        """Transform string dates to date objects."""
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                # Try ISO format
                return datetime.fromisoformat(value).date()
        return value
    
    @transformer('name')
    def normalize_name(self, value):
        """Normalize names to title case."""
        if isinstance(value, str):
            return value.strip().title()
        return value
    
    @transformer('email')
    def normalize_email(self, value):
        """Normalize email to lowercase."""
        if isinstance(value, str):
            return value.strip().lower()
        return value
    
    @validator('birth_date')
    def validate_birth_date(self, value):
        """Validate birth date is not in the future."""
        if value > date.today():
            raise ValueError("Birth date cannot be in the future")
        return value


# --- Feature 2: Async Validation ---
class User(Struct):
    username: str
    email: str
    password: str
    is_verified: bool = False
    
    # Simulate async database/API calls
    _existing_usernames = {"admin", "root", "test"}
    _existing_emails = {"admin@example.com", "test@example.com"}
    
    @transformer('username', 'email')
    def normalize_fields(self, value):
        """Normalize username and email."""
        return value.strip().lower()
    
    @validator('password')
    def validate_password(self, value):
        """Validate password strength."""
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit")
        return value
    
    @async_validator('username')
    async def validate_username_unique(self, value):
        """Simulate async check for username uniqueness."""
        print(f"  🔍 Checking username '{value}' availability...")
        await asyncio.sleep(0.1)  # Simulate network delay
        
        if value in self._existing_usernames:
            raise ValueError(f"Username '{value}' is already taken")
        return value
    
    @async_validator('email')
    async def validate_email_unique(self, value):
        """Simulate async check for email uniqueness."""
        print(f"  📧 Checking email '{value}' availability...")
        await asyncio.sleep(0.1)  # Simulate network delay
        
        if value in self._existing_emails:
            raise ValueError(f"Email '{value}' is already registered")
        return value


# --- Feature 3: Database Integration ---
class Product(Struct):
    id: Optional[int] = None
    name: str
    price: float
    category: str
    created_at: Optional[datetime] = None
    
    @transformer('price')
    def parse_price(self, value):
        """Convert string prices to float."""
        if isinstance(value, str):
            # Remove currency symbols and convert
            cleaned = value.replace('$', '').replace(',', '')
            return float(cleaned)
        return value
    
    @transformer('created_at')
    def parse_created_at(self, value):
        """Convert string timestamps to datetime objects."""
        if isinstance(value, str) and value:
            try:
                # Try SQLite timestamp format
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    # Try ISO format
                    return datetime.fromisoformat(value)
                except ValueError:
                    return value
        return value
    
    @validator('price')
    def validate_price(self, value):
        """Validate price is positive."""
        if value <= 0:
            raise ValueError("Price must be positive")
        return value


# --- Demo Functions ---

async def demo_transformers():
    """Demonstrate field transformers."""
    print("=== 🔄 Field Transformers Demo ===")
    
    # Test date transformation
    person1 = Person(
        name="  john doe  ",  # Will be title-cased
        birth_date="1990-05-15",  # String will be converted to date
        email="JOHN.DOE@EXAMPLE.COM"  # Will be lowercased
    )
    
    print(f"Original input: name='  john doe  ', birth_date='1990-05-15', email='JOHN.DOE@EXAMPLE.COM'")
    print(f"After transformation: {person1}")
    print(f"Birth date type: {type(person1.birth_date)}")
    print()


async def demo_async_validation():
    """Demonstrate async validation."""
    print("=== ⚡ Async Validation Demo ===")
    
    try:
        print("Creating user with unique credentials...")
        user = await User.create_async(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123"
        )
        print(f"✅ User created successfully: {user}")
        
    except ValueError as e:
        print(f"❌ Validation failed: {e}")
    
    print("\nTrying to create user with existing username...")
    try:
        user = await User.create_async(
            username="admin",  # This exists in _existing_usernames
            email="unique@example.com",
            password="SecurePass123"
        )
    except ValueError as e:
        print(f"❌ Expected validation failure: {e}")
    
    print()


async def demo_builder_pattern():
    """Demonstrate fluent builder interface."""
    print("=== 🏗️ Builder Pattern Demo ===")
    
    # Synchronous builder
    person = (Person.builder()
        .name("alice smith")
        .birth_date("1985-03-20")
        .email("ALICE@EXAMPLE.COM")
        .build())
    
    print(f"Built with fluent interface: {person}")
    
    # Async builder
    print("\nBuilding user with async validation...")
    try:
        user = await (User.builder()
            .username("builderuser")
            .email("builder@example.com")
            .password("BuilderPass123")
            .build_async())
        
        print(f"✅ Async built user: {user}")
    except ValueError as e:
        print(f"❌ Async validation failed: {e}")
    
    print()


def demo_database_integration():
    """Demonstrate database integration features."""
    print("=== 🗄️ Database Integration Demo ===")
    
    # Create in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create product
    product = Product(
        name="Laptop",
        price="$1,299.99",  # Will be transformed to float
        category="Electronics"
    )
    
    print(f"Original product: {product}")
    
    # Insert into database
    sql, values = product.to_sql_insert('products', exclude_fields=['id', 'created_at'])
    print(f"Generated SQL: {sql}")
    print(f"Values: {values}")
    
    cursor.execute(sql, values)
    product_id = cursor.lastrowid
    
    # Fetch from database
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    row = cursor.fetchone()
    
    # Create product from database row
    db_product = Product.from_db_row(row)
    db_product = db_product.copy(id=row['id'])  # Add the ID
    
    print(f"Product from database: {db_product}")
    
    # Update product
    updated_product = db_product.copy(price=1199.99, category="Computers")
    sql, values = updated_product.to_sql_update('products', 'id')
    print(f"Update SQL: {sql}")
    print(f"Update values: {values}")
    
    cursor.execute(sql, values)
    
    # Verify update
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    updated_row = cursor.fetchone()
    final_product = Product.from_db_row(updated_row)
    final_product = final_product.copy(id=updated_row['id'])
    
    print(f"Updated product: {final_product}")
    
    conn.close()
    print()


def demo_builder_with_validation():
    """Demonstrate builder with validation errors."""
    print("=== 🚨 Builder with Validation Errors ===")
    
    try:
        # This should fail validation
        person = (Person.builder()
            .name("Future Person")
            .birth_date("2030-01-01")  # Future date - should fail
            .build())
    except ValueError as e:
        print(f"❌ Builder validation caught error: {e}")
    
    print()


async def main():
    """Run all demos."""
    print("🚀 Cool Features Demo for StructLite\n")
    
    await demo_transformers()
    await demo_async_validation()
    await demo_builder_pattern()
    demo_database_integration()
    demo_builder_with_validation()
    
    print("🎉 All demos completed!")


if __name__ == "__main__":
    asyncio.run(main())