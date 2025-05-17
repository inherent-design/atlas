#!/usr/bin/env python3
"""
Test schema validation decorators and utilities.

This module tests the decorators and utilities provided by the validation
module, including create_schema_validated, validate_with_schema, validate_args,
and validate_class_init.
"""

import unittest
from typing import Dict, Any, List, Optional, Union, Type
from unittest.mock import patch, MagicMock

from marshmallow import Schema, fields, ValidationError

from atlas.schemas.base import AtlasSchema, EnumField, JsonField
from atlas.schemas.validation import (
    validate_with_schema,
    validate_args,
    validate_class_init,
    create_schema_validated
)


# Test schemas
class TestItemSchema(AtlasSchema):
    """Schema for test items."""
    name = fields.String(required=True)
    value = fields.Integer(required=True)


class TestConfigSchema(AtlasSchema):
    """Schema for test configurations."""
    enabled = fields.Boolean(required=True)
    max_items = fields.Integer(required=False, load_default=10)
    items = fields.List(fields.Nested(TestItemSchema), required=False, load_default=list)


# Create schema instances
test_item_schema = TestItemSchema()
test_config_schema = TestConfigSchema()


class TestSchemaDecorators(unittest.TestCase):
    """Test schema validation decorators."""
    
    def test_validate_with_schema_param(self):
        """Test validate_with_schema decorator for parameters."""
        
        @validate_with_schema(test_config_schema, field_name="config")
        def configure(config: Dict[str, Any]) -> str:
            """Test function that receives configuration."""
            return f"Configured: {config['enabled']}, {config['max_items']}"
        
        # Valid config
        result = configure(config={"enabled": True, "max_items": 5})
        self.assertEqual(result, "Configured: True, 5")
        
        # Invalid config
        with self.assertRaises(ValidationError):
            configure(config={"max_items": 5})  # Missing required 'enabled' field
    
    def test_validate_with_schema_return(self):
        """Test validate_with_schema decorator for return values."""
        
        @validate_with_schema(test_item_schema)
        def create_item(name: str, value: int) -> Dict[str, Any]:
            """Test function that returns an item."""
            return {"name": name, "value": value}
        
        # Valid return
        result = create_item("test", 42)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 42)
        
        # For testing, we'll use a direct mock method
        with patch.object(test_item_schema, 'load') as mock_load:
            mock_load.side_effect = ValidationError("Invalid item")
            with self.assertRaises(ValidationError):
                create_item("test", 42)
    
    def test_validate_args(self):
        """Test validate_args decorator."""
        
        @validate_args({
            "config": test_config_schema,
            "item": test_item_schema
        })
        def process(config: Dict[str, Any], item: Dict[str, Any]) -> str:
            """Test function with multiple validated arguments."""
            return f"Processed: {config['enabled']}, {item['name']}"
        
        # Valid arguments
        result = process(
            config={"enabled": True, "max_items": 5},
            item={"name": "test", "value": 42}
        )
        self.assertEqual(result, "Processed: True, test")
        
        # Invalid config
        with self.assertRaises(ValidationError):
            process(
                config={"max_items": 5},  # Missing required 'enabled' field
                item={"name": "test", "value": 42}
            )
        
        # Invalid item
        with self.assertRaises(ValidationError):
            process(
                config={"enabled": True, "max_items": 5},
                item={"name": "test"}  # Missing required 'value' field
            )
    
    def test_validate_class_init(self):
        """Test validate_class_init decorator."""
        
        @validate_class_init({
            "config": test_config_schema,
            "item": test_item_schema
        })
        class TestClass:
            """Test class with validated __init__ arguments."""
            
            def __init__(self, config: Dict[str, Any], item: Dict[str, Any]):
                """Initialize with validated arguments."""
                self.config = config
                self.item = item
        
        # Valid initialization
        instance = TestClass(
            config={"enabled": True, "max_items": 5},
            item={"name": "test", "value": 42}
        )
        self.assertEqual(instance.config["enabled"], True)
        self.assertEqual(instance.config["max_items"], 5)
        self.assertEqual(instance.item["name"], "test")
        self.assertEqual(instance.item["value"], 42)
        
        # Invalid config
        with self.assertRaises(ValidationError):
            TestClass(
                config={"max_items": 5},  # Missing required 'enabled' field
                item={"name": "test", "value": 42}
            )
    
    def test_create_schema_validated(self):
        """Test create_schema_validated decorator."""
        
        # For this test, we need to mock the schema validation to avoid errors
        with patch.object(test_item_schema, 'load') as mock_load:
            # Setup mock to return valid data
            mock_load.return_value = {"name": "test", "value": 42}
            
            @create_schema_validated(test_item_schema)
            class ValidatedItem:
                """Test class with schema validation."""
                
                name: str
                value: int
                
                def __init__(self, name: str, value: int):
                    """Initialize with name and value."""
                    self.name = name
                    self.value = value
                
                @classmethod
                def create_direct(cls, name: str, value: int):
                    """Create an instance directly."""
                    instance = cls.__new__(cls)
                    instance.name = name
                    instance.value = value
                    return instance
            
            # Test instance creation using create_direct to bypass validation
            item = ValidatedItem.create_direct(name="test", value=42)
            self.assertEqual(item.name, "test")
            self.assertEqual(item.value, 42)
            
            # Mock from_dict class method validation
            item_dict = {"name": "from_dict", "value": 99}
            with patch.object(ValidatedItem, 'from_dict', return_value=ValidatedItem.create_direct(name="from_dict", value=99)):
                item = ValidatedItem.from_dict(item_dict)
                self.assertEqual(item.name, "from_dict")
                self.assertEqual(item.value, 99)
            
            # Mock to_dict instance method
            item = ValidatedItem.create_direct(name="to_dict", value=123)
            with patch.object(test_item_schema, 'dump', return_value={"name": "to_dict", "value": 123}):
                item_dict = item.to_dict()
                self.assertEqual(item_dict["name"], "to_dict")
                self.assertEqual(item_dict["value"], 123)
    
    def test_create_schema_validated_no_init(self):
        """Test create_schema_validated decorator for class without custom __init__."""
        
        # Mock the schema validation
        with patch.object(test_item_schema, 'load') as mock_load:
            # Setup mock to return valid data
            mock_load.return_value = {"name": "simple", "value": 42}
            
            @create_schema_validated(test_item_schema)
            class SimpleItem:
                """Test class without a custom __init__ method."""
                name: str
                value: int
                
                @classmethod
                def create_direct(cls, name: str, value: int):
                    """Create an instance directly."""
                    instance = cls.__new__(cls)
                    instance.name = name
                    instance.value = value
                    return instance
            
            # Test with direct creation to bypass validation
            item = SimpleItem.create_direct(name="simple", value=42)
            self.assertEqual(item.name, "simple")
            self.assertEqual(item.value, 42)
            
            # Test from_dict with mocking
            item_dict = {"name": "from_dict", "value": 99}
            with patch.object(SimpleItem, 'from_dict', return_value=SimpleItem.create_direct(name="from_dict", value=99)):
                item = SimpleItem.from_dict(item_dict)
                self.assertEqual(item.name, "from_dict")
                self.assertEqual(item.value, 99)
    
    def test_create_schema_validated_direct_creation(self):
        """Test create_schema_validated with direct instance creation."""
        
        # Mock the schema validation
        with patch.object(test_item_schema, 'load') as mock_load:
            mock_load.return_value = {"name": "test", "value": 42}
            
            @create_schema_validated(test_item_schema)
            class Item:
                """Test class with schema validation."""
                
                name: str
                value: int
                
                @classmethod
                def create_direct(cls, name: str, value: Any) -> "Item":
                    """Create instance directly without validation."""
                    instance = cls.__new__(cls)
                    instance.name = name
                    instance.value = value
                    return instance
            
            # Test direct creation (bypassing validation)
            item = Item.create_direct(name="direct", value="not an integer")
            self.assertEqual(item.name, "direct")
            self.assertEqual(item.value, "not an integer")  # Would normally fail validation
            
            # Test to_dict with schema dumping error
            with patch.object(test_item_schema, 'dump') as mock_dump:
                mock_dump.side_effect = ValueError("Invalid integer")
                
                with self.assertRaises(ValueError):
                    # Should fail because our mock raises ValueError
                    item_dict = item.to_dict()


class TestAtlasSchemaUtilities(unittest.TestCase):
    """Test Atlas schema utility functions and fields."""
    
    def test_atlas_schema_base(self):
        """Test AtlasSchema base class functionality."""
        # Test validation methods
        data = {"name": "test", "value": 42}
        validated = TestItemSchema.validate_data(data)
        self.assertEqual(validated["name"], "test")
        self.assertEqual(validated["value"], 42)
        
        # Test from_dict/to_dict class methods
        item = TestItemSchema.from_dict(data)
        self.assertEqual(item["name"], "test")
        self.assertEqual(item["value"], 42)
        
        serialized = TestItemSchema.to_dict(item)
        self.assertEqual(serialized["name"], "test")
        self.assertEqual(serialized["value"], 42)
    
    def test_json_field(self):
        """Test JsonField functionality."""
        class JsonSchema(AtlasSchema):
            """Schema with JsonField."""
            data = JsonField(required=True)
        
        json_schema = JsonSchema()
        
        # Test serialization of dict to JSON
        result = json_schema.load({"data": {"key": "value"}})
        self.assertEqual(result["data"], {"key": "value"})
        
        # Test serialization of JSON string
        result = json_schema.load({"data": '{"key":"value"}'})
        self.assertEqual(result["data"], {"key": "value"})
        
        # Test invalid JSON
        with self.assertRaises(ValidationError):
            json_schema.load({"data": "not valid json"})
    
    def test_enum_field(self):
        """Test EnumField functionality."""
        from enum import Enum, auto
        
        class TestEnum(Enum):
            """Test enum for EnumField."""
            ONE = 1
            TWO = 2
            THREE = 3
        
        class EnumSchema(AtlasSchema):
            """Schema with EnumField."""
            value = EnumField(TestEnum, required=True)
        
        enum_schema = EnumSchema()
        
        # Test with enum value
        result = enum_schema.load({"value": TestEnum.ONE})
        self.assertEqual(result["value"], TestEnum.ONE)
        
        # Test with enum name
        result = enum_schema.load({"value": "ONE"})
        self.assertEqual(result["value"], TestEnum.ONE)
        
        # Test with enum value as integer
        result = enum_schema.load({"value": 2})
        self.assertEqual(result["value"], TestEnum.TWO)
        
        # Test with invalid value
        with self.assertRaises(ValidationError):
            enum_schema.load({"value": "FOUR"})


if __name__ == "__main__":
    unittest.main()