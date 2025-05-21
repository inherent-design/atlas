"""
Unit tests for the service registry functionality.

This module contains tests for the ServiceRegistry class and its related
functionality in the atlas.core.services.registry module.
"""

import threading
import unittest
import uuid
from unittest.mock import MagicMock

from atlas.services.registry import (
    BaseService,
    DuplicateServiceError,
    Service,
    ServiceError,
    ServiceRegistry,
    get_registry,
    get_service,
    get_service_by_name,
    list_services,
    register_service,
    unregister_service,
)


class TestServiceRegistry(unittest.TestCase):
    """Test cases for the ServiceRegistry class."""

    def setUp(self):
        """Set up test fixtures."""
        self.registry = ServiceRegistry()

        # Create a test service
        self.test_service = MagicMock(spec=Service)
        self.test_service.service_id = str(uuid.uuid4())
        self.test_service.name = "test_service"
        self.test_service.status = "initializing"
        self.test_service.capabilities = {"test": True}

    def test_register_service(self):
        """Test registering a service."""
        self.registry.register_service(self.test_service)

        # Verify service was registered
        self.assertEqual(
            self.registry.get_service(self.test_service.service_id), self.test_service
        )

    def test_register_duplicate_service(self):
        """Test registering a duplicate service."""
        self.registry.register_service(self.test_service)

        # Try to register again with same ID
        with self.assertRaises(DuplicateServiceError):
            self.registry.register_service(self.test_service)

        # Test with replace=True
        self.registry.register_service(self.test_service, replace=True)

    def test_get_service(self):
        """Test getting a service by ID."""
        self.registry.register_service(self.test_service)

        # Get service by ID
        service = self.registry.get_service(self.test_service.service_id)
        self.assertEqual(service, self.test_service)

        # Test non-existent service
        self.assertIsNone(self.registry.get_service("non_existent"))

    def test_get_service_by_name(self):
        """Test getting a service by name."""
        self.registry.register_service(self.test_service)

        # Get service by name
        service = self.registry.get_service_by_name(self.test_service.name)
        self.assertEqual(service, self.test_service)

        # Test non-existent service
        self.assertIsNone(self.registry.get_service_by_name("non_existent"))

    def test_get_service_by_name_with_capabilities(self):
        """Test getting a service by name with specific capabilities."""
        self.registry.register_service(self.test_service)

        # Get service by name with matching capability
        service = self.registry.get_service_by_name(
            self.test_service.name, capabilities=["test"]
        )
        self.assertEqual(service, self.test_service)

        # Get service by name with non-matching capability
        service = self.registry.get_service_by_name(
            self.test_service.name, capabilities=["non_existent"]
        )
        self.assertIsNone(service)

    def test_get_services_by_name(self):
        """Test getting all services with a given name."""
        self.registry.register_service(self.test_service)

        # Create another service with the same name but different ID
        test_service2 = MagicMock(spec=Service)
        test_service2.service_id = str(uuid.uuid4())
        test_service2.name = self.test_service.name
        test_service2.status = "initializing"
        test_service2.capabilities = {"test": True, "extra": True}

        self.registry.register_service(test_service2)

        # Get services by name
        services = self.registry.get_services_by_name(self.test_service.name)
        self.assertEqual(len(services), 2)
        self.assertIn(self.test_service, services)
        self.assertIn(test_service2, services)

        # Get services by name with capabilities
        services = self.registry.get_services_by_name(
            self.test_service.name, capabilities=["extra"]
        )
        self.assertEqual(len(services), 1)
        self.assertIn(test_service2, services)

    def test_get_services_by_capability(self):
        """Test getting all services with a given capability."""
        self.registry.register_service(self.test_service)

        # Create another service with different capability
        test_service2 = MagicMock(spec=Service)
        test_service2.service_id = str(uuid.uuid4())
        test_service2.name = "other_service"
        test_service2.status = "initializing"
        test_service2.capabilities = {"other": True}

        self.registry.register_service(test_service2)

        # Get services by capability
        services = self.registry.get_services_by_capability("test")
        self.assertEqual(len(services), 1)
        self.assertIn(self.test_service, services)

        # Get services by non-existent capability
        services = self.registry.get_services_by_capability("non_existent")
        self.assertEqual(len(services), 0)

    def test_list_services(self):
        """Test listing all registered services."""
        self.registry.register_service(self.test_service)

        # List services
        services = self.registry.list_services()
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["service_id"], self.test_service.service_id)
        self.assertEqual(services[0]["name"], self.test_service.name)

    def test_list_service_names(self):
        """Test listing all registered service names."""
        self.registry.register_service(self.test_service)

        # List service names
        names = self.registry.list_service_names()
        self.assertEqual(len(names), 1)
        self.assertIn(self.test_service.name, names)

    def test_list_capabilities(self):
        """Test listing all registered capabilities."""
        self.registry.register_service(self.test_service)

        # List capabilities
        capabilities = self.registry.list_capabilities()
        self.assertEqual(len(capabilities), 1)
        self.assertIn("test", capabilities)

    def test_unregister_service(self):
        """Test unregistering a service."""
        self.registry.register_service(self.test_service)

        # Unregister service
        result = self.registry.unregister_service(self.test_service.service_id)
        self.assertTrue(result)

        # Verify service was unregistered
        self.assertIsNone(self.registry.get_service(self.test_service.service_id))

        # Try to unregister non-existent service
        result = self.registry.unregister_service("non_existent")
        self.assertFalse(result)

    def test_start_service(self):
        """Test starting a service."""
        self.test_service.start = MagicMock()
        self.registry.register_service(self.test_service)

        # Start service
        result = self.registry.start_service(self.test_service.service_id)
        self.assertTrue(result)
        self.test_service.start.assert_called_once()

        # Try to start non-existent service
        result = self.registry.start_service("non_existent")
        self.assertFalse(result)

    def test_start_service_error(self):
        """Test starting a service that raises an error."""
        self.test_service.start = MagicMock(side_effect=Exception("Test error"))
        self.registry.register_service(self.test_service)

        # Start service
        with self.assertRaises(ServiceError):
            self.registry.start_service(self.test_service.service_id)

    def test_stop_service(self):
        """Test stopping a service."""
        self.test_service.stop = MagicMock()
        self.registry.register_service(self.test_service)

        # Stop service
        result = self.registry.stop_service(self.test_service.service_id)
        self.assertTrue(result)
        self.test_service.stop.assert_called_once()

        # Try to stop non-existent service
        result = self.registry.stop_service("non_existent")
        self.assertFalse(result)

    def test_stop_service_error(self):
        """Test stopping a service that raises an error."""
        self.test_service.stop = MagicMock(side_effect=Exception("Test error"))
        self.registry.register_service(self.test_service)

        # Stop service
        with self.assertRaises(ServiceError):
            self.registry.stop_service(self.test_service.service_id)

    def test_restart_service(self):
        """Test restarting a service."""
        self.test_service.stop = MagicMock()
        self.test_service.start = MagicMock()
        self.registry.register_service(self.test_service)

        # Restart service
        result = self.registry.restart_service(self.test_service.service_id)
        self.assertTrue(result)
        self.test_service.stop.assert_called_once()
        self.test_service.start.assert_called_once()

        # Try to restart non-existent service
        result = self.registry.restart_service("non_existent")
        self.assertFalse(result)

    def test_clear(self):
        """Test clearing all services from the registry."""
        self.registry.register_service(self.test_service)

        # Clear registry
        self.registry.clear()

        # Verify registry is empty
        self.assertEqual(len(self.registry.list_services()), 0)

    def test_thread_safety(self):
        """Test thread safety of the registry."""
        # Create multiple services with unique IDs
        services = []
        for i in range(10):
            service = MagicMock(spec=Service)
            service.service_id = str(uuid.uuid4())
            service.name = f"test_service_{i}"
            service.status = "initializing"
            service.capabilities = {"test": True}
            services.append(service)

        # Register services from multiple threads
        def register_services(services_to_register):
            for service in services_to_register:
                self.registry.register_service(service)

        threads = []
        for i in range(5):
            start_idx = i * 2
            end_idx = start_idx + 2
            thread = threading.Thread(
                target=register_services, args=(services[start_idx:end_idx],)
            )
            threads.append(thread)

        # Start threads
        for thread in threads:
            thread.start()

        # Wait for threads to complete
        for thread in threads:
            thread.join()

        # Verify all services were registered
        for service in services:
            self.assertEqual(self.registry.get_service(service.service_id), service)


class TestBaseService(unittest.TestCase):
    """Test cases for the BaseService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = BaseService(
            name="test_service",
            capabilities={"test": True},
            service_id="test_id",
            metadata={"version": "1.0"},
        )

    def test_initialization(self):
        """Test service initialization."""
        self.assertEqual(self.service.service_id, "test_id")
        self.assertEqual(self.service.name, "test_service")
        self.assertEqual(self.service.status, "initializing")
        self.assertEqual(self.service.capabilities, {"test": True})
        self.assertEqual(self.service.metadata, {"version": "1.0"})

    def test_start(self):
        """Test starting the service."""
        self.service.start()
        self.assertEqual(self.service.status, "running")

    def test_stop(self):
        """Test stopping the service."""
        self.service.start()  # Start first
        self.service.stop()
        self.assertEqual(self.service.status, "stopped")

    def test_start_error(self):
        """Test starting the service with an error."""

        # Create a subclass that overrides _start
        class ErrorService(BaseService):
            def _start(self):
                raise Exception("Test error")

        service = ErrorService(name="error_service")

        with self.assertRaises(ServiceError):
            service.start()

        self.assertEqual(service.status, "error")

    def test_stop_error(self):
        """Test stopping the service with an error."""

        # Create a subclass that overrides _stop
        class ErrorService(BaseService):
            def _stop(self):
                raise Exception("Test error")

        service = ErrorService(name="error_service")
        service.start()  # Start first

        with self.assertRaises(ServiceError):
            service.stop()

        self.assertEqual(service.status, "error")

    def test_to_dict(self):
        """Test converting the service to a dictionary."""
        service_dict = self.service.to_dict()

        self.assertEqual(service_dict["service_id"], "test_id")
        self.assertEqual(service_dict["name"], "test_service")
        self.assertEqual(service_dict["status"], "initializing")
        self.assertEqual(service_dict["capabilities"], {"test": True})
        self.assertEqual(service_dict["metadata"], {"version": "1.0"})


class TestGlobalRegistryFunctions(unittest.TestCase):
    """Test cases for the global registry functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test service
        self.test_service = MagicMock(spec=Service)
        self.test_service.service_id = str(uuid.uuid4())
        self.test_service.name = "test_service"
        self.test_service.status = "initializing"
        self.test_service.capabilities = {"test": True}

        # Clear the global registry
        get_registry().clear()

    def test_register_service(self):
        """Test registering a service with the global registry."""
        register_service(self.test_service)

        # Verify service was registered
        self.assertEqual(get_service(self.test_service.service_id), self.test_service)

    def test_get_service(self):
        """Test getting a service from the global registry."""
        register_service(self.test_service)

        # Get service
        service = get_service(self.test_service.service_id)
        self.assertEqual(service, self.test_service)

    def test_get_service_by_name(self):
        """Test getting a service by name from the global registry."""
        register_service(self.test_service)

        # Get service by name
        service = get_service_by_name(self.test_service.name)
        self.assertEqual(service, self.test_service)

    def test_list_services(self):
        """Test listing all services in the global registry."""
        register_service(self.test_service)

        # List services
        services = list_services()
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["service_id"], self.test_service.service_id)

    def test_unregister_service(self):
        """Test unregistering a service from the global registry."""
        register_service(self.test_service)

        # Unregister service
        result = unregister_service(self.test_service.service_id)
        self.assertTrue(result)

        # Verify service was unregistered
        self.assertIsNone(get_service(self.test_service.service_id))


if __name__ == "__main__":
    unittest.main()
