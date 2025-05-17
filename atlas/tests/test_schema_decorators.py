#!/usr/bin/env python3
"""
Test schema validation decorators and utilities.

This module tests the core schema validation decorators and utilities in
Atlas, including decorator factories, schema-validated class creation,
and validation utilities for functions and objects.
"""

import unittest
from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
from dataclasses import dataclass
from unittest.mock import patch, MagicMock

from marshmallow import Schema, fields, ValidationError, post_load

from atlas.schemas.base import AtlasSchema, JsonField, EnumField
from atlas.schemas.validation import (
    validate_with_schema,
    validate_args,
    validate_class_init,
    create_schema_validated
)
from atlas.schemas.types import SchemaValidated


# Define some test schemas
class UserSchema(AtlasSchema):
    """Test schema for a user object."""
    
    name = fields.String(required=True)
    email = fields.Email(required=True)
    age = fields.Integer(required=False, validate=lambda n: n >= 0)
    roles = fields.List(fields.String(), required=False)


class ConfigSchema(AtlasSchema):
    """Test schema for a configuration object."""
    
    debug = fields.Boolean(required=False, default=False)
    log_level = fields.String(required=False, default="info")
    max_retries = fields.Integer(required=False, default=3, validate=lambda n: n >= 0)
    options = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False)


class TestValidateWithSchema(unittest.TestCase):
    """Test the validate_with_schema decorator."""

    def setUp(self):
        """Set up test fixtures."""
        # Create schemas
        self.user_schema = UserSchema()
        self.config_schema = ConfigSchema()
        
        # Create decorated functions
        @validate_with_schema(self.user_schema, field_name="user")
        def create_user_profile(user: Dict[str, Any]) -> Dict[str, Any]:
            """Create a user profile with schema validation."""
            return {"profile": user, "created": True}
        
        @validate_with_schema(self.config_schema)
        def get_default_config() -> Dict[str, Any]:
            """Get a default configuration with schema validation."""
            return {
                "debug": False,
                "log_level": "info",
                "max_retries": 3,
                "options": {"timeout": 30}
            }
        
        self.create_user_profile = create_user_profile
        self.get_default_config = get_default_config
    
    def test_parameter_validation(self):
        """Test validation of a function parameter."""
        # Call with valid parameter
        valid_user = {
            "name": "Test User",
            "email": "test@example.com",
            "age": 30
        }
        result = self.create_user_profile(user=valid_user)
        
        # Check result
        self.assertTrue(result["created"])
        self.assertEqual(result["profile"]["name"], "Test User")
        
        # Call with invalid parameter
        invalid_user = {
            "name": "Invalid User",
            "email": "not-an-email"  # Invalid email format
        }
        with self.assertRaises(ValidationError):
            self.create_user_profile(user=invalid_user)
    
    def test_return_value_validation(self):
        """Test validation of a function return value."""
        # Function returns valid config
        config = self.get_default_config()
        self.assertEqual(config["log_level"], "info")
        self.assertEqual(config["max_retries"], 3)
        
        # Mock a function to return invalid config
        @validate_with_schema(self.config_schema)
        def get_invalid_config() -> Dict[str, Any]:
            """Get an invalid configuration."""
            return {
                "debug": "not-a-boolean",  # Invalid boolean
                "log_level": "debug",
                "max_retries": -1  # Invalid negative value
            }
        
        # Call function - should raise
        with self.assertRaises(ValidationError):
            get_invalid_config()


class TestValidateArgs(unittest.TestCase):
    """Test the validate_args decorator."""

    def setUp(self):
        """Set up test fixtures."""
        # Create schemas
        self.user_schema = UserSchema()
        self.config_schema = ConfigSchema()
        
        # Create decorated function
        @validate_args({
            "user": self.user_schema,
            "config": self.config_schema
        })
        def create_user_with_config(user, config):
            """Create a user with configuration, both validated."""
            return {
                "user": user,
                "config": config,
                "created": True
            }
        
        self.create_user_with_config = create_user_with_config
    
    def test_multiple_args_validation(self):
        """Test validation of multiple function arguments."""
        # Valid arguments
        valid_user = {
            "name": "Test User",
            "email": "test@example.com",
            "age": 30
        }
        valid_config = {
            "debug": True,
            "log_level": "debug",
            "options": {"timeout": 60}
        }
        
        # Call with valid arguments
        result = self.create_user_with_config(
            user=valid_user,
            config=valid_config
        )
        
        # Check result
        self.assertTrue(result["created"])
        self.assertEqual(result["user"]["name"], "Test User")
        self.assertEqual(result["config"]["log_level"], "debug")
        
        # Call with invalid user but valid config
        invalid_user = {
            "name": "Invalid User",
            # Missing required email field
        }
        with self.assertRaises(ValidationError):
            self.create_user_with_config(
                user=invalid_user,
                config=valid_config
            )
        
        # Call with valid user but invalid config
        invalid_config = {
            "debug": True,
            "max_retries": -5  # Invalid negative value
        }
        with self.assertRaises(ValidationError):
            self.create_user_with_config(
                user=valid_user,
                config=invalid_config
            )
    
    def test_positional_args(self):
        """Test validation of positional arguments."""
        # Valid arguments
        valid_user = {
            "name": "Test User",
            "email": "test@example.com"
        }
        valid_config = {
            "debug": True,
            "log_level": "debug"
        }
        
        # Call with positional arguments
        result = self.create_user_with_config(valid_user, valid_config)
        
        # Check result
        self.assertTrue(result["created"])
        self.assertEqual(result["user"]["name"], "Test User")
        self.assertEqual(result["config"]["log_level"], "debug")
        
        # Call with invalid first positional argument
        invalid_user = {
            "name": "Invalid User",
            # Missing required email field
        }
        with self.assertRaises(ValidationError):
            self.create_user_with_config(invalid_user, valid_config)


class TestValidateClassInit(unittest.TestCase):
    """Test the validate_class_init decorator."""

    def setUp(self):
        """Set up test fixtures."""
        # Create schemas
        self.user_schema = UserSchema()
        self.config_schema = ConfigSchema()
        
        # Create decorated class
        @validate_class_init({
            "user": self.user_schema,
            "config": self.config_schema
        })
        class UserService:
            """Service class with validated initialization."""
            
            def __init__(self, user, config, name=None):
                """Initialize with validated user and config."""
                self.user = user
                self.config = config
                self.name = name or "default-service"
        
        self.user_service_class = UserService
    
    def test_class_init_validation(self):
        """Test validation during class initialization."""
        # Valid initialization arguments
        valid_user = {
            "name": "Test User",
            "email": "test@example.com",
            "age": 30
        }
        valid_config = {
            "debug": True,
            "log_level": "debug",
            "options": {"timeout": 60}
        }
        
        # Create instance with valid arguments
        service = self.user_service_class(
            user=valid_user,
            config=valid_config,
            name="test-service"
        )
        
        # Check instance attributes
        self.assertEqual(service.user["name"], "Test User")
        self.assertEqual(service.config["log_level"], "debug")
        self.assertEqual(service.name, "test-service")
        
        # Create instance with invalid user
        invalid_user = {
            "name": "Invalid User",
            # Missing required email field
        }
        with self.assertRaises(ValidationError):
            self.user_service_class(
                user=invalid_user,
                config=valid_config
            )
        
        # Create instance with invalid config
        invalid_config = {
            "debug": "not-a-boolean",  # Invalid boolean
            "max_retries": -5  # Invalid negative value
        }
        with self.assertRaises(ValidationError):
            self.user_service_class(
                user=valid_user,
                config=invalid_config
            )


class TestCreateSchemaValidated(unittest.TestCase):
    """Test the create_schema_validated decorator for class creation."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test schema
        class PersonSchema(Schema):
            """Schema for a person object."""
            
            name = fields.String(required=True)
            age = fields.Integer(required=True, validate=lambda n: n >= 0)
            email = fields.Email(required=False)
            
            @post_load
            def make_person(self, data, **kwargs):
                """Return the data as is for testing."""
                return data
        
        self.schema = PersonSchema()
        
        # Create schema-validated class
        @create_schema_validated(self.schema)
        class Person:
            """A schema-validated person class."""
            
            def __init__(self, name, age, email=None, **kwargs):
                """Initialize a person."""
                self.name = name
                self.age = age
                self.email = email
                
                # Store any additional kwargs
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        self.person_class = Person
    
    def test_class_initialization(self):
        """Test initialization of a schema-validated class."""
        # Create with valid data
        person = self.person_class(name="Test Person", age=30, email="test@example.com")
        
        # Check attributes
        self.assertEqual(person.name, "Test Person")
        self.assertEqual(person.age, 30)
        self.assertEqual(person.email, "test@example.com")
        
        # Create with invalid data
        with self.assertRaises(ValidationError):
            self.person_class(name="Invalid Person", age=-5)  # Negative age
            
        with self.assertRaises(ValidationError):
            self.person_class(age=25)  # Missing required name
    
    def test_from_dict(self):
        """Test from_dict class method added by decorator."""
        # Create from valid dict
        data = {"name": "Dict Person", "age": 25, "email": "dict@example.com"}
        person = self.person_class.from_dict(data)
        
        # Check attributes
        self.assertEqual(person.name, "Dict Person")
        self.assertEqual(person.age, 25)
        self.assertEqual(person.email, "dict@example.com")
        
        # Create from invalid dict
        invalid_data = {"name": "Invalid Dict", "age": "not-a-number"}
        with self.assertRaises(ValidationError):
            self.person_class.from_dict(invalid_data)
    
    def test_to_dict(self):
        """Test to_dict instance method added by decorator."""
        # Create instance
        person = self.person_class(name="To Dict Person", age=40, extra_field="extra value")
        
        # Convert to dict
        person_dict = person.to_dict()
        
        # Check dict contents
        self.assertEqual(person_dict["name"], "To Dict Person")
        self.assertEqual(person_dict["age"], 40)
        # Note: extra_field might not be included depending on schema dumping behavior
    
    def test_schema_access(self):
        """Test schema access through class attribute."""
        # Check schema attribute
        self.assertTrue(hasattr(self.person_class, "schema"))
        self.assertIsNotNone(self.person_class.schema)
        
        # Check can use schema directly
        data = {"name": "Schema Test", "age": 50}
        validated = self.person_class.schema.load(data)
        self.assertEqual(validated["name"], "Schema Test")
        self.assertEqual(validated["age"], 50)
    
    def test_schema_validated_interface(self):
        """Test SchemaValidated protocol conformance."""
        # Create instance
        person = self.person_class(name="Interface Test", age=35)
        
        # Check instance has expected methods and attributes
        self.assertTrue(hasattr(person, "to_dict"))
        self.assertTrue(callable(person.to_dict))
        
        # Check class has expected methods and attributes
        self.assertTrue(hasattr(self.person_class, "from_dict"))
        self.assertTrue(callable(self.person_class.from_dict))
        self.assertTrue(hasattr(self.person_class, "schema"))


class TestSchemaValidatedWithCustomInit(unittest.TestCase):
    """Test @create_schema_validated with custom __init__ implementations."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test schema
        class CustomSchema(Schema):
            """Schema for a custom object."""
            type = fields.String(required=True)
            value = fields.Integer(required=True)
            metadata = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False)
        
        # Create schema-validated class with custom __init__
        @create_schema_validated(CustomSchema())
        class CustomObject:
            """A custom object with schema validation."""
            
            def __init__(self, **kwargs):
                """Custom init that sets attributes from kwargs."""
                self.initialized = True
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # Create schema-validated class with parent class __init__
        class BaseObject:
            """Base class with __init__."""
            
            def __init__(self, base_value=None):
                """Initialize base object."""
                self.base_initialized = True
                self.base_value = base_value
        
        @create_schema_validated(CustomSchema())
        class DerivedObject(BaseObject):
            """Derived object with schema validation."""
            
            def __init__(self, base_value=None, **kwargs):
                """Initialize derived object."""
                super().__init__(base_value)
                self.derived_initialized = True
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        self.custom_class = CustomObject
        self.derived_class = DerivedObject
    
    def test_custom_init(self):
        """Test schema-validated class with custom __init__."""
        # Create with valid data
        obj = self.custom_class(type="test", value=42, metadata={"extra": "data"})
        
        # Check attributes
        self.assertTrue(obj.initialized)
        self.assertEqual(obj.type, "test")
        self.assertEqual(obj.value, 42)
        self.assertEqual(obj.metadata["extra"], "data")
        
        # Create with invalid data
        with self.assertRaises(ValidationError):
            self.custom_class(type="invalid")  # Missing required value
    
    def test_derived_init(self):
        """Test schema-validated class with parent class __init__."""
        # Create with valid data
        obj = self.derived_class(
            base_value="parent data",
            type="derived",
            value=100,
            metadata={"source": "test"}
        )
        
        # Check attributes from all inheritance levels
        self.assertTrue(obj.base_initialized)
        self.assertEqual(obj.base_value, "parent data")
        self.assertTrue(obj.derived_initialized)
        self.assertEqual(obj.type, "derived")
        self.assertEqual(obj.value, 100)
        self.assertEqual(obj.metadata["source"], "test")
        
        # Create with invalid data
        with self.assertRaises(ValidationError):
            self.derived_class(
                base_value="parent data",
                type="invalid"  # Missing required value
            )


class TestAtlasSchemaBase(unittest.TestCase):
    """Test AtlasSchema base class and utility fields."""

    def test_atlas_schema_base(self):
        """Test AtlasSchema base class."""
        # Create a schema using AtlasSchema
        class TestSchema(AtlasSchema):
            """Test schema extending AtlasSchema."""
            name = fields.String(required=True)
            value = fields.Integer(required=True)
        
        schema = TestSchema()
        
        # Test validation
        valid_data = {"name": "test", "value": 42}
        validated = schema.load(valid_data)
        self.assertEqual(validated["name"], "test")
        self.assertEqual(validated["value"], 42)
        
        # Test validation with errors
        invalid_data = {"name": "test"}  # Missing required value
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)
        
        # Test dump
        obj = {"name": "test", "value": 42, "extra": "ignored"}
        dumped = schema.dump(obj)
        self.assertEqual(dumped["name"], "test")
        self.assertEqual(dumped["value"], 42)
        self.assertNotIn("extra", dumped)  # Should be excluded
    
    def test_json_field(self):
        """Test JsonField for serializing/deserializing JSON."""
        # Create a schema with JsonField
        class JsonSchema(AtlasSchema):
            """Schema with a JsonField."""
            name = fields.String(required=True)
            data = JsonField(required=True)
        
        schema = JsonSchema()
        
        # Test with dict data
        dict_data = {"name": "test", "data": {"key": "value", "nested": {"num": 42}}}
        validated = schema.load(dict_data)
        self.assertEqual(validated["name"], "test")
        self.assertEqual(validated["data"]["key"], "value")
        self.assertEqual(validated["data"]["nested"]["num"], 42)
        
        # Test with JSON string
        json_data = {"name": "test", "data": '{"key": "value", "nested": {"num": 42}}'}
        validated = schema.load(json_data)
        self.assertEqual(validated["name"], "test")
        self.assertEqual(validated["data"]["key"], "value")
        self.assertEqual(validated["data"]["nested"]["num"], 42)
        
        # Test with invalid JSON
        invalid_json = {"name": "test", "data": '{"key": unclosed quote}'}
        with self.assertRaises(ValidationError):
            schema.load(invalid_json)
    
    def test_enum_field(self):
        """Test EnumField for serializing/deserializing enums."""
        # Create enum class
        from enum import Enum, auto
        
        class Color(Enum):
            """Color enum for testing."""
            RED = "red"
            GREEN = "green"
            BLUE = "blue"
        
        # Create a schema with EnumField
        class EnumSchema(AtlasSchema):
            """Schema with an EnumField."""
            name = fields.String(required=True)
            color = EnumField(enum_class=Color, required=True)
        
        schema = EnumSchema()
        
        # Test with enum value
        enum_data = {"name": "test", "color": Color.RED}
        validated = schema.load(enum_data)
        self.assertEqual(validated["name"], "test")
        self.assertEqual(validated["color"], Color.RED)
        
        # Test with string value
        string_data = {"name": "test", "color": "green"}
        validated = schema.load(string_data)
        self.assertEqual(validated["name"], "test")
        self.assertEqual(validated["color"], Color.GREEN)
        
        # Test with invalid enum value
        invalid_data = {"name": "test", "color": "purple"}
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)


if __name__ == "__main__":
    unittest.main()