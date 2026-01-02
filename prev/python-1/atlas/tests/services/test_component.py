"""
Unit tests for the service-enabled component functionality.

This module contains tests for the ServiceEnabledComponent class and its related
functionality in the atlas.core.services.component module.
"""

import threading
import unittest
from unittest.mock import MagicMock

from atlas.services.component import (
    ServiceAware,
    ServiceEnabledComponent,
    ServiceInitializationError,
    ServiceMissingError,
)
from atlas.services.registry import ServiceRegistry


class TestServiceEnabledComponent(unittest.TestCase):
    """Test cases for the ServiceEnabledComponent class."""

    def setUp(self):
        """Set up test fixtures."""

        # Create custom subclass for testing
        class TestComponent(ServiceEnabledComponent):
            def _setup_service_references(self):
                # Simple implementation that does nothing
                pass

        self.component = TestComponent(
            component_id="test_component", component_type="test_type"
        )

        # Mock registry and register it
        self.registry = ServiceRegistry()
        self.component._service_registry = self.registry

    def test_initialization(self):
        """Test component initialization."""
        self.assertEqual(self.component.component_id, "test_component")
        self.assertEqual(self.component.component_type, "test_type")
        self.assertEqual(self.component.service_registry, self.registry)
        self.assertFalse(self.component._initialized_services)

    def test_initialization_with_generated_id(self):
        """Test component initialization with generated ID."""

        class TestComponent(ServiceEnabledComponent):
            def _setup_service_references(self):
                pass

        component = TestComponent(component_type="test_type")
        self.assertIsNotNone(component.component_id)
        self.assertNotEqual(component.component_id, "")
        self.assertEqual(component.component_type, "test_type")

    def test_initialize_services(self):
        """Test initializing service references."""
        # Create a component with a mock _setup_service_references
        setup_mock = MagicMock()

        class TestComponent(ServiceEnabledComponent):
            def _setup_service_references(self):
                setup_mock()

        component = TestComponent()

        # Initialize services
        component.initialize_services()

        # Verify _setup_service_references was called
        setup_mock.assert_called_once()
        self.assertTrue(component._initialized_services)

        # Call again to verify it's only called once
        component.initialize_services()
        setup_mock.assert_called_once()

    def test_initialize_services_error(self):
        """Test error during service initialization."""

        # Create a component with a failing _setup_service_references
        class TestComponent(ServiceEnabledComponent):
            def _setup_service_references(self):
                raise Exception("Test error")

        component = TestComponent()

        # Initialize services should raise an error
        with self.assertRaises(ServiceInitializationError):
            component.initialize_services()

        self.assertFalse(component._initialized_services)

    def test_get_service(self):
        """Test getting a service from the registry."""
        # Create a mock service
        service = MagicMock()
        service_class = MagicMock()
        service_class.__name__ = "TestService"

        # Mock registry's get_service_by_name method
        self.registry.get_service_by_name = MagicMock(return_value=service)

        # Get service from component
        result = self.component.get_service(service_class)

        # Verify registry method was called
        self.registry.get_service_by_name.assert_called_once_with("TestService")
        self.assertEqual(result, service)

        # Verify service was cached
        self.assertEqual(self.component._services.get("TestService"), service)

    def test_get_service_cached(self):
        """Test getting a cached service."""
        # Create a mock service
        service = MagicMock()
        service_class = MagicMock()
        service_class.__name__ = "TestService"

        # Add service to cache
        self.component._services["TestService"] = service

        # Mock registry's get_service_by_name method
        self.registry.get_service_by_name = MagicMock()

        # Get service from component
        result = self.component.get_service(service_class)

        # Verify registry method was not called
        self.registry.get_service_by_name.assert_not_called()
        self.assertEqual(result, service)

    def test_get_service_by_capability(self):
        """Test getting a service by capability."""
        # Create a mock service
        service = MagicMock()
        service_class = MagicMock()
        service_class.__name__ = "TestService"

        # Mock registry's get_service_by_name and get_services_by_capability methods
        self.registry.get_service_by_name = MagicMock(return_value=None)
        self.registry.get_services_by_capability = MagicMock(return_value=[service])

        # Get service from component
        result = self.component.get_service(service_class)

        # Verify registry methods were called
        self.registry.get_service_by_name.assert_called_once_with("TestService")
        self.registry.get_services_by_capability.assert_called_once_with("TestService")
        self.assertEqual(result, service)

        # Verify service was cached
        self.assertEqual(self.component._services.get("TestService"), service)

    def test_get_service_missing(self):
        """Test getting a missing service."""
        # Create a service class
        service_class = MagicMock()
        service_class.__name__ = "TestService"

        # Mock registry's get_service_by_name and get_services_by_capability methods
        self.registry.get_service_by_name = MagicMock(return_value=None)
        self.registry.get_services_by_capability = MagicMock(return_value=[])

        # Get non-required service from component
        result = self.component.get_service(service_class, required=False)
        self.assertIsNone(result)

        # Get required service should raise an error
        with self.assertRaises(ServiceMissingError):
            self.component.get_service(service_class, required=True)

    def test_thread_safety(self):
        """Test thread safety of the component."""
        # Create a component with a thread-safe _setup_service_references
        setup_count = 0
        setup_lock = threading.RLock()

        class TestComponent(ServiceEnabledComponent):
            def _setup_service_references(self):
                nonlocal setup_count
                with setup_lock:
                    setup_count += 1
                    # Simulate some work
                    import time

                    time.sleep(0.01)

        component = TestComponent()

        # Initialize services from multiple threads
        def initialize_services():
            component.initialize_services()

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=initialize_services)
            threads.append(thread)

        # Start threads
        for thread in threads:
            thread.start()

        # Wait for threads to complete
        for thread in threads:
            thread.join()

        # Verify _setup_service_references was only called once
        self.assertEqual(setup_count, 1)
        self.assertTrue(component._initialized_services)


class TestServiceAware(unittest.TestCase):
    """Test cases for the ServiceAware protocol."""

    def test_service_aware_protocol(self):
        """Test the ServiceAware protocol."""

        # Create a class that implements the protocol
        class TestServiceAware:
            @property
            def service_registry(self):
                return ServiceRegistry()

        # Verify it implements the protocol
        self.assertTrue(isinstance(TestServiceAware(), ServiceAware))

        # Create a class that doesn't implement the protocol
        class TestNotServiceAware:
            pass

        # Verify it doesn't implement the protocol
        self.assertFalse(isinstance(TestNotServiceAware(), ServiceAware))


if __name__ == "__main__":
    unittest.main()
