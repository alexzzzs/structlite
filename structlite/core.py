import copy
import asyncio
import inspect
from functools import total_ordering
from typing import get_type_hints, get_origin, get_args, Annotated, Any, Dict, List, Union, Callable, Optional
import sys

# structlite.py
# --- Helper Decorator for Validators ---
def validator(*field_names: str):
    """Decorator to mark a method as a validator for one or more fields.
    
    Args:
        *field_names: Names of fields this validator should apply to
        
    Returns:
        Decorated function with _validator_for attribute
        
    Example:
        @validator('age')
        def validate_age(self, value):
            if value < 0:
                raise ValueError("Age must be non-negative")
            return value
    """
    if not all(isinstance(name, str) for name in field_names):
        raise TypeError("validator field names must be strings.")
    
    def decorator(func):
        func._validator_for = field_names
        return func
    return decorator


# --- NEW: Async Validator Decorator ---
def async_validator(*field_names: str):
    """Decorator to mark a method as an async validator for one or more fields.
    
    Args:
        *field_names: Names of fields this validator should apply to
        
    Returns:
        Decorated async function with _async_validator_for attribute
        
    Example:
        @async_validator('email')
        async def validate_email_unique(self, value):
            exists = await check_email_exists(value)
            if exists:
                raise ValueError("Email already exists")
            return value
    """
    if not all(isinstance(name, str) for name in field_names):
        raise TypeError("async_validator field names must be strings.")
    
    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("async_validator can only be applied to async functions")
        func._async_validator_for = field_names
        return func
    return decorator


# --- NEW: Field Transformer Decorator ---
def transformer(*field_names: str):
    """Decorator to mark a method as a field transformer.
    
    Transformers are applied before validation and can convert input values
    to the expected type or format.
    
    Args:
        *field_names: Names of fields this transformer should apply to
        
    Returns:
        Decorated function with _transformer_for attribute
        
    Example:
        @transformer('birth_date')
        def parse_date(self, value):
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value
    """
    if not all(isinstance(name, str) for name in field_names):
        raise TypeError("transformer field names must be strings.")
    
    def decorator(func):
        func._transformer_for = field_names
        return func
    return decorator

# --- Base Marker Class ---
class immutable:
    """Marker base class to make structs immutable by default.
    
    Usage:
        class Point(Struct, immutable):
            x: int
            y: int
    """
    pass

# --- Metaclass ---
class StructMeta(type):
    """Metaclass for Struct that handles field collection, validation setup, and type processing."""
    
    def __new__(mcls, name: str, bases: tuple, namespace: dict):
        # --- Field and Default Collection (from original) ---
        fields = []
        defaults = {}
        for base in bases:
            if hasattr(base, '_fields'):
                fields.extend(base._fields)
            if hasattr(base, '_defaults'):
                defaults.update(base._defaults)

        annotations = namespace.get('__annotations__', {})
        new_fields = list(annotations.keys())
        fields.extend(new_fields)

        for k in new_fields:
            if k in namespace:
                defaults[k] = namespace.pop(k)

        seen = set()
        fields = [f for f in fields if not (f in seen or seen.add(f))]
        
        namespace['__slots__'] = fields + ['_frozen']
        namespace['_fields'] = fields
        namespace['_defaults'] = defaults

        # --- NEW: Collect Validators, Async Validators, and Transformers ---
        validators = {}
        async_validators = {}
        transformers = {}
        
        for key, value in namespace.items():
            # Regular validators
            if hasattr(value, '_validator_for'):
                for field_name in value._validator_for:
                    if field_name not in fields:
                        raise NameError(f"Validator defined for non-existent field '{field_name}'")
                    validators.setdefault(field_name, []).append(value)
            
            # Async validators
            if hasattr(value, '_async_validator_for'):
                for field_name in value._async_validator_for:
                    if field_name not in fields:
                        raise NameError(f"Async validator defined for non-existent field '{field_name}'")
                    async_validators.setdefault(field_name, []).append(value)
            
            # Transformers
            if hasattr(value, '_transformer_for'):
                for field_name in value._transformer_for:
                    if field_name not in fields:
                        raise NameError(f"Transformer defined for non-existent field '{field_name}'")
                    transformers.setdefault(field_name, []).append(value)
        
        namespace['_validators'] = validators
        namespace['_async_validators'] = async_validators
        namespace['_transformers'] = transformers

        # --- Frozen Flag  ---
        if any(base is immutable for base in bases):
            namespace.setdefault('frozen', True)
        else:
            namespace.setdefault('frozen', False)

        cls = super().__new__(mcls, name, bases, namespace)
        
        # Use include_extras=True to handle Annotated types for metadata
        cls._types = get_type_hints(cls, include_extras=True)
        
        # Extract field metadata from Annotated types
        cls._field_metadata = {}
        for field_name, field_type in cls._types.items():
            if get_origin(field_type) is Annotated:
                args = get_args(field_type)
                if len(args) > 1:
                    # Store metadata (everything after the first arg which is the actual type)
                    cls._field_metadata[field_name] = args[1:]
                    # Update _types to use the actual type without Annotated wrapper
                    cls._types[field_name] = args[0]
        
        return cls

# --- NEW: Struct Builder Class ---
class StructBuilder:
    """Fluent interface builder for creating Struct instances.
    
    Example:
        person = (Person.builder()
            .name("Alice")
            .age(30)
            .email("alice@example.com")
            .build())
    """
    
    def __init__(self, struct_class):
        self._struct_class = struct_class
        self._values = {}
    
    def __getattr__(self, name: str):
        """Create a fluent setter method for any field."""
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        def setter(value):
            self._values[name] = value
            return self  # Return self for chaining
        
        return setter
    
    def build(self, **additional_kwargs):
        """Build the final struct instance.
        
        Args:
            **additional_kwargs: Additional field values to set
            
        Returns:
            New struct instance
        """
        final_values = {**self._values, **additional_kwargs}
        return self._struct_class(**final_values)
    
    def build_async(self, **additional_kwargs):
        """Build the final struct instance with async validation.
        
        Args:
            **additional_kwargs: Additional field values to set
            
        Returns:
            Awaitable that resolves to new struct instance
        """
        final_values = {**self._values, **additional_kwargs}
        return self._struct_class.create_async(**final_values)


# --- Main Struct Class ---
@total_ordering
class Struct(metaclass=StructMeta):
    """A flexible struct-like class with validation, immutability, and serialization support.
    
    Features:
    - Type checking based on annotations
    - Field validation with @validator decorator
    - Optional immutability (inherit from immutable or set frozen=True)
    - Serialization to/from dictionaries
    - Equality, ordering, and hashing support
    - Inheritance of fields and defaults
    
    Example:
        class Person(Struct):
            name: str
            age: int = 0
            
            @validator('age')
            def validate_age(self, value):
                if value < 0:
                    raise ValueError("Age must be non-negative")
                return value
    """
    frozen = False  # Default mutability

    def __init__(self, *args, frozen: bool = None, **kwargs) -> None:
        """Initialize a new struct instance.
        
        Args:
            *args: Positional arguments for fields (in declaration order)
            frozen: Override the default frozen state for this instance
            **kwargs: Keyword arguments for fields
            
        Raises:
            TypeError: If wrong number of arguments or duplicate field assignments
            AttributeError: If invalid field names provided
        """
        total_fields = len(self._fields)

        # Check for invalid keyword arguments
        invalid_fields = [k for k in kwargs if k not in self._fields]
        if invalid_fields:
            raise TypeError(
                f"Invalid field(s) for {self.__class__.__name__}: {', '.join(invalid_fields)}. "
                f"Valid fields are: {', '.join(self._fields)}."
            )

        # Check the total number of arguments
        if len(args) + len(kwargs) > total_fields:
            raise TypeError(
                f"Too many arguments for {self.__class__.__name__}. "
                f"Expected at most {total_fields}, got {len(args) + len(kwargs)}. "
                f"Fields: {', '.join(self._fields)}."
            )

        assigned_fields = set()

        # Positional arguments
        for name, value in zip(self._fields, args):
            self._validate_and_set(name, value, initial_set=True)
            assigned_fields.add(name)

        # Keyword arguments
        for name, value in kwargs.items():
            if name in assigned_fields:
                raise TypeError(
                    f"Duplicate value for field '{name}' in {self.__class__.__name__}. "
                    f"Fields can only be assigned once."
                )
            self._validate_and_set(name, value, initial_set=True)
            assigned_fields.add(name)

        # Default values for any remaining fields
        for name in self._fields:
            if name not in assigned_fields:
                if name in self._defaults:
                    default = self._defaults[name]
                    value = default() if callable(default) else default
                    self._validate_and_set(name, value, initial_set=True)
                else:
                    raise TypeError(
                        f"Missing required field '{name}' for {self.__class__.__name__}. "
                        f"Fields: {', '.join(self._fields)}."
                    )

        # Set frozen status
        if frozen is None:
            frozen = getattr(self, 'frozen', False)
        super().__setattr__('_frozen', frozen)

    def _validate_type(self, name: str, value: Any, expected: Any) -> None:
        """Validate that value matches the expected type annotation."""
        if not expected:
            return
        
        origin_type = get_origin(expected)
        
        # Handle Union types (including Optional which is Union[T, None])
        if origin_type is Union:
            union_args = get_args(expected)
            # Check if value matches any of the union types
            for union_type in union_args:
                try:
                    if union_type is type(None) and value is None:
                        return  # None is valid for Optional types
                    elif union_type is not type(None) and isinstance(value, union_type):
                        return  # Value matches one of the union types
                except TypeError:
                    # Handle cases where isinstance fails (e.g., with generic types)
                    continue
            # If we get here, value doesn't match any union type
            raise TypeError(f"Field '{name}' expects {expected}, got {type(value).__name__}")
        
        elif origin_type:
            # For other generic types like list[int], dict[str, int], just check the origin
            try:
                if not isinstance(value, origin_type):
                    raise TypeError(f"Field '{name}' expects {expected}, got {type(value).__name__}")
            except TypeError:
                # Some generic types can't be used with isinstance
                pass
        else:
            # For simple types and classes
            if not isinstance(value, expected):
                raise TypeError(f"Field '{name}' expects {expected}, got {type(value).__name__}")

    def _validate_and_set(self, name: str, value: Any, initial_set: bool = False) -> None:
        """Helper to centralize type checks, validation, and setting.
        
        Args:
            name: Field name
            value: Value to set
            initial_set: True during __init__, False for normal attribute setting
        """
        # On first creation (__init__), don't check frozen status
        if not initial_set and getattr(self, '_frozen', False):
            raise AttributeError(f"Cannot modify frozen '{self.__class__.__name__}' instance")

        # Apply transformers first
        if name in getattr(self, '_transformers', {}):
            for t_func in self._transformers[name]:
                result = t_func(self, value)
                if result is not None:
                    value = result

        # Type checking
        expected = self._types.get(name)
        self._validate_type(name, value, expected)
        
        # Field Validators - handle both transforming and non-transforming validators
        if name in getattr(self, '_validators', {}):
            for v_func in self._validators[name]:
                result = v_func(self, value)
                # If validator returns a value, use it (transformation)
                # If it returns None, keep original value (validation only)
                if result is not None:
                    value = result

        super().__setattr__(name, value)
    
    async def _validate_and_set_async(self, name: str, value: Any, initial_set: bool = False) -> None:
        """Async version of _validate_and_set that includes async validators.
        
        Args:
            name: Field name
            value: Value to set
            initial_set: True during __init__, False for normal attribute setting
        """
        # First do all synchronous validation
        self._validate_and_set(name, value, initial_set)
        
        # Then run async validators
        if name in getattr(self, '_async_validators', {}):
            for av_func in self._async_validators[name]:
                result = await av_func(self, getattr(self, name))
                # If async validator returns a value, use it
                if result is not None:
                    super().__setattr__(name, result)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute with validation and frozen check."""
        if name not in self._fields:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no field '{name}'. "
                f"Valid fields are: {', '.join(self._fields)}."
            )
        self._validate_and_set(name, value)

    # --- Equality and Comparison ---
    def __eq__(self, other: object) -> bool:
        """Check equality by comparing all field values."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return all(getattr(self, f) == getattr(other, f) for f in self._fields)

    def __lt__(self, other: 'Struct') -> bool:
        """Compare structs lexicographically by field values."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        # Avoid creating tuples for better performance - compare field by field
        for field in self._fields:
            self_val = getattr(self, field)
            other_val = getattr(other, field)
            if self_val < other_val:
                return True
            elif self_val > other_val:
                return False
        return False  # All fields are equal

    # --- Hashing ---
    def __hash__(self) -> int:
        """Return hash of struct. Only available for frozen instances."""
        if not self._frozen:
            raise TypeError(f"Mutable '{self.__class__.__name__}' is unhashable")
        return hash(tuple(getattr(self, f) for f in self._fields))

    # --- Serialization ---
    def to_dict(self, recursive: bool = True) -> Dict[str, Any]:
        """Convert the struct to a dictionary.
        
        Args:
            recursive: If True, recursively convert nested Struct instances
            
        Returns:
            Dictionary representation of the struct
        """
        d = {}
        for name in self._fields:
            value = getattr(self, name)
            if recursive:
                if isinstance(value, Struct):
                    value = value.to_dict(recursive=True)
                elif isinstance(value, (list, tuple)):
                    value = type(value)(
                        v.to_dict(recursive=True) if isinstance(v, Struct) else v for v in value
                    )
                elif isinstance(value, dict):
                    value = {
                        k: v.to_dict(recursive=True) if isinstance(v, Struct) else v 
                        for k, v in value.items()
                    }
            d[name] = value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Struct':
        """Create a struct instance from a dictionary.
        
        Args:
            data: Dictionary containing field values
            
        Returns:
            New struct instance
            
        Raises:
            TypeError: If required fields are missing or invalid data provided
        """
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")
            
        processed_data = {}
        for name, value in data.items():
            if name not in cls._types:
                processed_data[name] = value
                continue
            
            field_type = cls._types[name]
            origin = get_origin(field_type)
            args = get_args(field_type)
            
            try:
                # Handle nested Structs
                if isinstance(value, dict) and isinstance(field_type, type) and issubclass(field_type, Struct):
                    processed_data[name] = field_type.from_dict(value)
                # Handle lists/tuples of Structs (e.g., list[Point])
                elif origin in (list, tuple) and args and isinstance(args[0], type) and issubclass(args[0], Struct):
                    item_cls = args[0]
                    processed_data[name] = origin(item_cls.from_dict(item) if isinstance(item, dict) else item for item in value)
                # Handle dicts with Struct values (e.g., dict[str, Point])
                elif origin is dict and len(args) == 2 and isinstance(args[1], type) and issubclass(args[1], Struct):
                    value_cls = args[1]
                    processed_data[name] = {
                        k: value_cls.from_dict(v) if isinstance(v, dict) else v 
                        for k, v in value.items()
                    }
                else:
                    processed_data[name] = value
            except (TypeError, AttributeError) as e:
                raise TypeError(f"Error processing field '{name}': {e}")
                
        return cls(**processed_data)

    # --- Copying ---
    def copy(self, **changes: Any) -> 'Struct':
        """Return a shallow copy of the struct, optionally with field changes.
        
        Args:
            **changes: Field values to change in the copy
            
        Returns:
            New struct instance
            
        Example:
            person2 = person1.copy(age=30)
        """
        values = {f: getattr(self, f) for f in self._fields}
        values.update(changes)
        return self.__class__(**values)

    def __deepcopy__(self, memo: Dict[int, Any]) -> 'Struct':
        """Integration with Python's copy.deepcopy()."""
        new_obj = self.__class__.__new__(self.__class__)
        memo[id(self)] = new_obj
        for name in self._fields:
            value = getattr(self, name)
            setattr(new_obj, name, copy.deepcopy(value, memo))
        
        # Important: also copy the _frozen state
        super(Struct, new_obj).__setattr__('_frozen', self._frozen)
        return new_obj

    # --- String Representation ---
    def __repr__(self) -> str:
        """Return a detailed string representation of the struct."""
        fields_str = ", ".join(f"{f}={getattr(self, f)!r}" for f in self._fields)
        return f"{self.__class__.__name__}({fields_str})"
    
    def __str__(self) -> str:
        """Return a user-friendly string representation."""
        return self.__repr__()
    
    # --- Metadata Access ---
    @classmethod
    def get_field_metadata(cls, field_name: str) -> tuple:
        """Get metadata for a specific field from Annotated type hints.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Tuple of metadata objects, empty tuple if no metadata
            
        Example:
            class Person(Struct):
                age: Annotated[int, {"min": 0, "max": 150}, "Age in years"]
                
            Person.get_field_metadata('age')  # ({'min': 0, 'max': 150}, 'Age in years')
        """
        return getattr(cls, '_field_metadata', {}).get(field_name, ())
    
    @classmethod
    def get_all_field_metadata(cls) -> Dict[str, tuple]:
        """Get metadata for all fields.
        
        Returns:
            Dictionary mapping field names to their metadata tuples
        """
        return getattr(cls, '_field_metadata', {}).copy()
    
    # --- NEW: Builder Pattern Support ---
    @classmethod
    def builder(cls) -> StructBuilder:
        """Create a fluent builder for this struct type.
        
        Returns:
            StructBuilder instance for fluent construction
            
        Example:
            person = (Person.builder()
                .name("Alice")
                .age(30)
                .build())
        """
        return StructBuilder(cls)
    
    # --- NEW: Async Creation Support ---
    @classmethod
    async def create_async(cls, *args, **kwargs) -> 'Struct':
        """Create a struct instance with async validation.
        
        This method runs all synchronous validation first, then async validation.
        
        Args:
            *args: Positional arguments for fields
            **kwargs: Keyword arguments for fields
            
        Returns:
            New struct instance after all validation passes
        """
        # Create instance with sync validation only
        instance = cls.__new__(cls)
        
        # Initialize without async validation first
        total_fields = len(instance._fields)
        
        # Check for invalid keyword arguments
        invalid_fields = [k for k in kwargs if k not in instance._fields]
        if invalid_fields:
            raise TypeError(
                f"Invalid field(s) for {cls.__name__}: {', '.join(invalid_fields)}. "
                f"Valid fields are: {', '.join(instance._fields)}."
            )

        # Check the total number of arguments
        if len(args) + len(kwargs) > total_fields:
            raise TypeError(
                f"Too many arguments for {cls.__name__}. "
                f"Expected at most {total_fields}, got {len(args) + len(kwargs)}. "
                f"Fields: {', '.join(instance._fields)}."
            )

        assigned_fields = set()

        # Positional arguments
        for name, value in zip(instance._fields, args):
            instance._validate_and_set(name, value, initial_set=True)
            assigned_fields.add(name)

        # Keyword arguments
        for name, value in kwargs.items():
            if name in assigned_fields:
                raise TypeError(
                    f"Duplicate value for field '{name}' in {cls.__name__}. "
                    f"Fields can only be assigned once."
                )
            instance._validate_and_set(name, value, initial_set=True)
            assigned_fields.add(name)

        # Default values for any remaining fields
        for name in instance._fields:
            if name not in assigned_fields:
                if name in instance._defaults:
                    default = instance._defaults[name]
                    value = default() if callable(default) else default
                    instance._validate_and_set(name, value, initial_set=True)
                else:
                    raise TypeError(
                        f"Missing required field '{name}' for {cls.__name__}. "
                        f"Fields: {', '.join(instance._fields)}."
                    )

        # Set frozen status
        frozen = kwargs.get('frozen', getattr(instance, 'frozen', False))
        super(Struct, instance).__setattr__('_frozen', frozen)
        
        # Now run async validation for all fields
        for field_name in instance._fields:
            if field_name in getattr(instance, '_async_validators', {}):
                await instance._validate_and_set_async(field_name, getattr(instance, field_name), initial_set=True)
        
        return instance
    
    # --- Additional Utility Methods ---
    def get_field_names(self) -> List[str]:
        """Get list of all field names for this struct."""
        return list(self._fields)
    
    def get_field_values(self) -> List[Any]:
        """Get list of all field values for this struct."""
        return [getattr(self, f) for f in self._fields]
    
    def get_field_items(self) -> List[tuple]:
        """Get list of (field_name, value) tuples."""
        return [(f, getattr(self, f)) for f in self._fields]
    
    def replace(self, **changes: Any) -> 'Struct':
        """Create a new instance with specified field changes (alias for copy)."""
        return self.copy(**changes)
    
    # --- NEW: Database Integration Methods ---
    @classmethod
    def from_db_row(cls, row, column_mapping: Optional[Dict[str, str]] = None) -> 'Struct':
        """Create a struct instance from a database row.
        
        Args:
            row: Database row (dict-like or sequence)
            column_mapping: Optional mapping from database columns to field names
            
        Returns:
            New struct instance
            
        Example:
            user = User.from_db_row(cursor.fetchone())
            # or with column mapping
            user = User.from_db_row(row, {'user_name': 'name', 'user_email': 'email'})
        """
        if hasattr(row, 'keys'):  # Dict-like (e.g., sqlite3.Row)
            data = dict(row)
        else:  # Sequence (tuple, list)
            # Assume columns are in field order
            data = dict(zip(cls._fields, row))
        
        # Apply column mapping if provided
        if column_mapping:
            mapped_data = {}
            for db_col, field_name in column_mapping.items():
                if db_col in data:
                    mapped_data[field_name] = data[db_col]
            # Add unmapped fields
            for key, value in data.items():
                if key not in column_mapping and key in cls._fields:
                    mapped_data[key] = value
            data = mapped_data
        
        return cls.from_dict(data)
    
    def to_sql_insert(self, table_name: str, exclude_fields: Optional[List[str]] = None) -> tuple:
        """Generate SQL INSERT statement and values.
        
        Args:
            table_name: Name of the database table
            exclude_fields: Fields to exclude (e.g., auto-increment IDs)
            
        Returns:
            Tuple of (sql_statement, values_tuple)
            
        Example:
            sql, values = user.to_sql_insert('users', exclude_fields=['id'])
            cursor.execute(sql, values)
        """
        exclude_fields = exclude_fields or []
        fields = [f for f in self._fields if f not in exclude_fields]
        values = [getattr(self, f) for f in fields]
        
        placeholders = ', '.join(['?' for _ in fields])
        columns = ', '.join(fields)
        
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return sql, tuple(values)
    
    def to_sql_update(self, table_name: str, where_field: str, exclude_fields: Optional[List[str]] = None) -> tuple:
        """Generate SQL UPDATE statement and values.
        
        Args:
            table_name: Name of the database table
            where_field: Field to use in WHERE clause
            exclude_fields: Fields to exclude from SET clause
            
        Returns:
            Tuple of (sql_statement, values_tuple)
            
        Example:
            sql, values = user.to_sql_update('users', 'id')
            cursor.execute(sql, values)
        """
        exclude_fields = exclude_fields or []
        exclude_fields.append(where_field)  # Don't update the WHERE field
        
        update_fields = [f for f in self._fields if f not in exclude_fields]
        update_values = [getattr(self, f) for f in update_fields]
        where_value = getattr(self, where_field)
        
        set_clause = ', '.join([f"{f} = ?" for f in update_fields])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_field} = ?"
        
        return sql, tuple(update_values + [where_value])

