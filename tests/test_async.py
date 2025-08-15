"""Tests for async validation functionality."""

import pytest
import asyncio
from structlite import Struct, async_validator, transformer, validator


class TestAsyncValidation:
    """Test async validation features."""
    
    @pytest.mark.asyncio
    async def test_async_validator(self):
        """Test basic async validation."""
        class User(Struct):
            username: str
            email: str
            
            # Simulate existing usernames
            _existing_usernames = {"admin", "root", "test"}
            
            @async_validator('username')
            async def validate_username_unique(self, value):
                await asyncio.sleep(0.01)  # Simulate async operation
                if value in self._existing_usernames:
                    raise ValueError(f"Username '{value}' already exists")
                return value
        
        # Test successful creation
        user = await User.create_async(
            username="newuser",
            email="user@example.com"
        )
        assert user.username == "newuser"
        
        # Test validation failure
        with pytest.raises(ValueError, match="Username 'admin' already exists"):
            await User.create_async(
                username="admin",
                email="admin@example.com"
            )
    
    @pytest.mark.asyncio
    async def test_async_builder(self):
        """Test async builder pattern."""
        class User(Struct):
            username: str
            email: str
            
            @async_validator('email')
            async def validate_email_format(self, value):
                await asyncio.sleep(0.01)
                if '@' not in value:
                    raise ValueError("Invalid email format")
                return value
        
        # Test successful async build
        user = await (User.builder()
            .username("testuser")
            .email("test@example.com")
            .build_async())
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        
        # Test validation failure in builder
        with pytest.raises(ValueError, match="Invalid email format"):
            await (User.builder()
                .username("testuser")
                .email("invalid-email")
                .build_async())
    
    @pytest.mark.asyncio
    async def test_combined_sync_async_validation(self):
        """Test combination of sync and async validators."""
        class User(Struct):
            username: str
            password: str
            
            @transformer('username')
            def normalize_username(self, value):
                return value.strip().lower()
            
            @validator('password')
            def validate_password_strength(self, value):
                if len(value) < 8:
                    raise ValueError("Password too short")
                return value
            
            @async_validator('username')
            async def validate_username_available(self, value):
                await asyncio.sleep(0.01)
                if value == "taken":
                    raise ValueError("Username not available")
                return value
        
        # Test successful creation with all validations
        user = await User.create_async(
            username="  ValidUser  ",  # Will be transformed to "validuser"
            password="SecurePass123"
        )
        assert user.username == "validuser"
        
        # Test sync validation failure
        with pytest.raises(ValueError, match="Password too short"):
            await User.create_async(
                username="user",
                password="short"
            )
        
        # Test async validation failure
        with pytest.raises(ValueError, match="Username not available"):
            await User.create_async(
                username="taken",
                password="SecurePass123"
            )