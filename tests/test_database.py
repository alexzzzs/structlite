"""Tests for database integration functionality."""

import pytest
import sqlite3
from datetime import datetime
from typing import Optional
from structlite import Struct, transformer


class TestDatabaseIntegration:
    """Test database integration features."""
    
    def test_from_db_row_dict_like(self):
        """Test creating struct from dict-like database row."""
        class User(Struct):
            id: int
            name: str
            email: str
            created_at: Optional[datetime] = None
        
        # Simulate database row as dict
        row_data = {
            'id': 1,
            'name': 'Alice',
            'email': 'alice@example.com',
            'created_at': None
        }
        
        user = User.from_db_row(row_data)
        assert user.id == 1
        assert user.name == 'Alice'
        assert user.email == 'alice@example.com'
        assert user.created_at is None
    
    def test_from_db_row_sequence(self):
        """Test creating struct from sequence database row."""
        class User(Struct):
            id: int
            name: str
            email: str
        
        # Simulate database row as tuple
        row_data = (1, 'Bob', 'bob@example.com')
        
        user = User.from_db_row(row_data)
        assert user.id == 1
        assert user.name == 'Bob'
        assert user.email == 'bob@example.com'
    
    def test_from_db_row_with_column_mapping(self):
        """Test creating struct with column mapping."""
        class User(Struct):
            name: str
            email: str
        
        # Database has different column names
        row_data = {
            'user_name': 'Charlie',
            'user_email': 'charlie@example.com',
            'other_field': 'ignored'
        }
        
        column_mapping = {
            'user_name': 'name',
            'user_email': 'email'
        }
        
        user = User.from_db_row(row_data, column_mapping)
        assert user.name == 'Charlie'
        assert user.email == 'charlie@example.com'
    
    def test_to_sql_insert(self):
        """Test SQL INSERT generation."""
        class Product(Struct):
            id: Optional[int] = None
            name: str
            price: float
            category: str
        
        product = Product(name="Laptop", price=999.99, category="Electronics")
        
        sql, values = product.to_sql_insert('products', exclude_fields=['id'])
        
        expected_sql = "INSERT INTO products (name, price, category) VALUES (?, ?, ?)"
        expected_values = ('Laptop', 999.99, 'Electronics')
        
        assert sql == expected_sql
        assert values == expected_values
    
    def test_to_sql_update(self):
        """Test SQL UPDATE generation."""
        class Product(Struct):
            id: int
            name: str
            price: float
            category: str
        
        product = Product(1, "Laptop", 1199.99, "Computers")
        
        sql, values = product.to_sql_update('products', 'id')
        
        expected_sql = "UPDATE products SET name = ?, price = ?, category = ? WHERE id = ?"
        expected_values = ('Laptop', 1199.99, 'Computers', 1)
        
        assert sql == expected_sql
        assert values == expected_values
    
    def test_database_roundtrip(self):
        """Test complete database roundtrip with transformers."""
        class Product(Struct):
            id: Optional[int] = None
            name: str
            price: float
            created_at: Optional[str] = None  # SQLite returns strings
            
            @transformer('price')
            def parse_price(self, value):
                if isinstance(value, str):
                    return float(value.replace('$', '').replace(',', ''))
                return value
        
        # Create in-memory database
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                price REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create product
        product = Product(name="Test Product", price=29.99)
        
        # Insert
        sql, values = product.to_sql_insert('products', exclude_fields=['id', 'created_at'])
        cursor.execute(sql, values)
        
        # Fetch back
        cursor.execute('SELECT * FROM products WHERE id = ?', (cursor.lastrowid,))
        row = cursor.fetchone()
        
        # Create from row
        db_product = Product.from_db_row(row)
        
        assert db_product.name == "Test Product"
        assert db_product.price == 29.99
        assert db_product.id == cursor.lastrowid
        assert db_product.created_at is not None  # Should have timestamp
        
        conn.close()