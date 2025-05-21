"""
Unit tests for resource lifecycle management.

This module tests the Resource, ResourceManager, and related functionality
to ensure proper resource lifecycle management.
"""

import threading
import time
import unittest
from threading import Event

from atlas.services.resources import (
    Resource,
    ResourceAcquisitionError,
    ResourceError,
    ResourceManager,
    ResourceReleaseError,
    create_resource_manager,
    managed_resource,
)


class TestResource(unittest.TestCase):
    """Test the Resource class."""

    def test_initialization(self):
        """Test resource initialization."""
        # Create a test resource
        resource = Resource(
            resource_id="test-resource", resource_type="test-type", value="test-value"
        )

        # Check initial state
        self.assertEqual(resource.resource_id, "test-resource")
        self.assertEqual(resource.resource_type, "test-type")
        self.assertEqual(resource.value, "test-value")
        self.assertEqual(resource.state, "initializing")
        self.assertIsNone(resource.owner_service)
        self.assertIsNone(resource.acquisition_time)
        self.assertIsNone(resource.release_time)
        self.assertIsNotNone(resource.create_time)

    def test_lifecycle(self):
        """Test resource lifecycle state transitions."""
        # Create a resource
        resource = Resource(
            resource_id="test-resource", resource_type="test-type", value="test-value"
        )

        # Initialize
        resource.initialize()
        self.assertEqual(resource.state, "ready")

        # Acquire
        value = resource.acquire("test-service")
        self.assertEqual(value, "test-value")
        self.assertEqual(resource.state, "in_use")
        self.assertEqual(resource.owner_service, "test-service")
        self.assertIsNotNone(resource.acquisition_time)

        # Release
        resource.release()
        self.assertEqual(resource.state, "released")
        self.assertIsNotNone(resource.release_time)

    def test_error_state(self):
        """Test setting resource to error state."""
        # Create a resource
        resource = Resource(
            resource_id="test-resource", resource_type="test-type", value="test-value"
        )

        # Set error state
        test_error = ValueError("Test error")
        resource.set_error(test_error)

        self.assertEqual(resource.state, "error")
        self.assertEqual(resource.metadata["error"], str(test_error))
        self.assertEqual(resource.metadata["error_type"], "ValueError")

    def test_invalid_transitions(self):
        """Test that invalid state transitions raise appropriate errors."""
        # Create a resource
        resource = Resource(
            resource_id="test-resource", resource_type="test-type", value="test-value"
        )

        # Can't acquire before initializing
        with self.assertRaises(ResourceAcquisitionError):
            resource.acquire("test-service")

        # Initialize
        resource.initialize()

        # Can't initialize twice
        with self.assertRaises(ResourceError):
            resource.initialize()

        # Acquire
        resource.acquire("test-service")

        # Can't acquire again
        with self.assertRaises(ResourceAcquisitionError):
            resource.acquire("another-service")

        # Can't release with wrong owner
        with self.assertRaises(ResourceReleaseError):
            resource.release("wrong-service")

        # Release properly
        resource.release("test-service")

        # Can't release twice
        with self.assertRaises(ResourceReleaseError):
            resource.release("test-service")

    def test_cleanup_function(self):
        """Test that cleanup function is called during release."""
        cleanup_called = False

        def cleanup_func(value):
            nonlocal cleanup_called
            cleanup_called = True

        # Create a resource with cleanup
        resource = Resource(
            resource_id="test-resource",
            resource_type="test-type",
            value="test-value",
            cleanup_func=cleanup_func,
        )

        # Initialize and acquire
        resource.initialize()
        resource.acquire("test-service")

        # Release should call cleanup
        resource.release()
        self.assertTrue(cleanup_called)

    def test_to_dict(self):
        """Test resource serialization to dictionary."""
        # Create a resource
        resource = Resource(
            resource_id="test-resource",
            resource_type="test-type",
            value="test-value",
            metadata={"tag": "test-tag"},
        )

        # Initialize and acquire
        resource.initialize()
        resource.acquire("test-service")

        # Serialize to dict
        resource_dict = resource.to_dict()

        # Check fields
        self.assertEqual(resource_dict["resource_id"], "test-resource")
        self.assertEqual(resource_dict["type"], "test-type")
        self.assertEqual(resource_dict["state"], "in_use")
        self.assertEqual(resource_dict["owner_service"], "test-service")
        self.assertIsNotNone(resource_dict["acquisition_time"])
        self.assertIsNone(resource_dict["release_time"])
        self.assertIsNotNone(resource_dict["create_time"])
        self.assertEqual(resource_dict["metadata"]["tag"], "test-tag")


class TestResourceManager(unittest.TestCase):
    """Test the ResourceManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ResourceManager()

    def test_register_resource(self):
        """Test registering a resource."""
        resource = self.manager.register_resource(
            resource_type="test-type", value="test-value"
        )

        # Resource should be registered
        self.assertEqual(resource.state, "ready")

        # Should be retrievable by ID
        retrieved = self.manager.get_resource(resource.resource_id)
        self.assertEqual(retrieved, resource)

    def test_create_resource(self):
        """Test creating a resource with factory function."""
        create_called = False
        cleanup_called = False

        def factory_func():
            nonlocal create_called
            create_called = True
            return "created-value"

        def cleanup_func(value):
            nonlocal cleanup_called
            cleanup_called = True

        # Create resource with factory
        resource = self.manager.create_resource(
            resource_type="test-type",
            factory_func=factory_func,
            cleanup_func=cleanup_func,
        )

        # Factory should have been called
        self.assertTrue(create_called)
        self.assertEqual(resource.value, "created-value")

        # Cleanup should be configured
        resource.acquire("test-service")
        resource.release()
        self.assertTrue(cleanup_called)

    def test_factory_error(self):
        """Test error handling in factory function."""

        def failing_factory():
            raise ValueError("Factory error")

        # Creating resource should propagate error
        with self.assertRaises(ResourceError):
            self.manager.create_resource(
                resource_type="test-type", factory_func=failing_factory
            )

    def test_find_resources(self):
        """Test finding resources by criteria."""
        # Create test resources
        res1 = self.manager.register_resource(resource_type="type1", value="value1")

        res2 = self.manager.register_resource(resource_type="type2", value="value2")

        res3 = self.manager.register_resource(resource_type="type1", value="value3")

        # Acquire one resource
        res1.acquire("service1")

        # Find by type
        type1_resources = self.manager.find_resources(resource_type="type1")
        self.assertEqual(len(type1_resources), 2)
        self.assertIn(res1, type1_resources)
        self.assertIn(res3, type1_resources)

        # Find by state
        in_use_resources = self.manager.find_resources(state="in_use")
        self.assertEqual(len(in_use_resources), 1)
        self.assertEqual(in_use_resources[0], res1)

        # Find by owner
        owned_resources = self.manager.find_resources(owner_service="service1")
        self.assertEqual(len(owned_resources), 1)
        self.assertEqual(owned_resources[0], res1)

        # Find by multiple criteria
        specific_resources = self.manager.find_resources(
            resource_type="type1", state="in_use", owner_service="service1"
        )
        self.assertEqual(len(specific_resources), 1)
        self.assertEqual(specific_resources[0], res1)

    def test_acquire_resource(self):
        """Test resource acquisition with manager."""
        # Register resources
        res1 = self.manager.register_resource(resource_type="test-type", value="value1")

        res2 = self.manager.register_resource(resource_type="test-type", value="value2")

        # Acquire a resource
        resource = self.manager.acquire_resource(
            resource_type="test-type", owner_service="test-service"
        )

        # Should have acquired one of the resources
        self.assertIn(resource, [res1, res2])
        self.assertEqual(resource.state, "in_use")
        self.assertEqual(resource.owner_service, "test-service")

        # Acquire another resource
        resource2 = self.manager.acquire_resource(
            resource_type="test-type", owner_service="test-service-2"
        )

        # Should get the other resource
        self.assertNotEqual(resource, resource2)
        self.assertIn(resource2, [res1, res2])

        # Try to acquire when none available
        with self.assertRaises(ResourceAcquisitionError):
            self.manager.acquire_resource(
                resource_type="test-type", owner_service="test-service-3", timeout=0.1
            )

    def test_wait_for_resource_type(self):
        """Test waiting for resource availability."""
        # Create event to signal resource creation
        resource_created = Event()

        def create_resource_later():
            time.sleep(0.1)
            self.manager.register_resource(
                resource_type="test-type", value="test-value"
            )
            resource_created.set()

        # Start thread to create resource
        thread = threading.Thread(target=create_resource_later)
        thread.daemon = True
        thread.start()

        # Wait for resource type
        result = self.manager.wait_for_resource_type(
            resource_type="test-type", timeout=1.0
        )

        # Should have successfully waited
        self.assertTrue(result)

        # Check that resource was created
        resource_created.wait(1.0)
        self.assertTrue(resource_created.is_set())

        resources = self.manager.find_resources(resource_type="test-type")
        self.assertEqual(len(resources), 1)

    def test_wait_timeout(self):
        """Test timeout during resource wait."""
        # Wait for a non-existent resource
        result = self.manager.wait_for_resource_type(
            resource_type="non-existent", timeout=0.1
        )

        # Should have timed out
        self.assertFalse(result)

    def test_remove_resource(self):
        """Test removing a resource."""
        # Register a resource
        resource = self.manager.register_resource(
            resource_type="test-type", value="test-value"
        )

        # Remove resource
        result = self.manager.remove_resource(resource.resource_id)
        self.assertTrue(result)

        # Resource should be gone
        self.assertIsNone(self.manager.get_resource(resource.resource_id))

        # Remove again should fail
        result = self.manager.remove_resource(resource.resource_id)
        self.assertFalse(result)

    def test_cleanup_resources(self):
        """Test cleaning up resources."""
        # Register resources
        res1 = self.manager.register_resource(resource_type="type1", value="value1")

        res2 = self.manager.register_resource(resource_type="type2", value="value2")

        res3 = self.manager.register_resource(resource_type="type1", value="value3")

        # Release one resource
        res1.acquire("service1")
        res1.release()

        # Set one to error
        res2.set_error(ValueError("Test error"))

        # Cleanup released and error resources
        count = self.manager.cleanup_resources()
        self.assertEqual(count, 2)

        # Only res3 should remain
        remaining = self.manager.find_resources()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0], res3)

    def test_cleanup_by_type(self):
        """Test cleaning up resources by type."""
        # Register resources
        res1 = self.manager.register_resource(resource_type="type1", value="value1")

        res2 = self.manager.register_resource(resource_type="type2", value="value2")

        # Release both
        res1.acquire("service1")
        res1.release()

        res2.acquire("service2")
        res2.release()

        # Cleanup only type1
        count = self.manager.cleanup_resources(resource_type="type1")
        self.assertEqual(count, 1)

        # Only res2 should remain
        remaining = self.manager.find_resources()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0], res2)

    def test_stats(self):
        """Test resource manager statistics."""
        # Register resources
        res1 = self.manager.register_resource(resource_type="type1", value="value1")

        res2 = self.manager.register_resource(resource_type="type2", value="value2")

        res3 = self.manager.register_resource(resource_type="type1", value="value3")

        # Acquire one resource
        res1.acquire("service1")

        # Get stats
        stats = self.manager.stats()

        # Check counts
        self.assertEqual(stats["total_resources"], 3)
        self.assertIn("type1", stats["resource_counts"])
        self.assertIn("type2", stats["resource_counts"])
        self.assertEqual(stats["resource_counts"]["type1"]["ready"], 1)
        self.assertEqual(stats["resource_counts"]["type1"]["in_use"], 1)
        self.assertEqual(stats["resource_counts"]["type2"]["ready"], 1)
        self.assertIn("service1", stats["owner_counts"])
        self.assertEqual(stats["owner_counts"]["service1"], 1)
        self.assertIn("type1", stats["resource_types"])
        self.assertIn("type2", stats["resource_types"])


class TestManagedResource(unittest.TestCase):
    """Test the managed_resource context manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ResourceManager()

    def test_acquire_release(self):
        """Test automatic acquisition and release."""
        # Register a resource
        self.manager.register_resource(resource_type="test-type", value="test-value")

        # Use context manager
        with managed_resource(
            manager=self.manager,
            resource_type="test-type",
            owner_service="test-service",
        ) as value:
            # Resource should be acquired
            self.assertEqual(value, "test-value")

            # Find the resource
            resources = self.manager.find_resources(
                resource_type="test-type", state="in_use", owner_service="test-service"
            )
            self.assertEqual(len(resources), 1)
            resource = resources[0]

        # After context, resource should be released
        self.assertEqual(resource.state, "released")

    def test_factory_creation(self):
        """Test creating a resource with factory inside context."""
        factory_called = False
        cleanup_called = False

        def factory_func():
            nonlocal factory_called
            factory_called = True
            return "created-value"

        def cleanup_func(value):
            nonlocal cleanup_called
            cleanup_called = True

        # Use context manager with factory
        with managed_resource(
            manager=self.manager,
            resource_type="test-type",
            owner_service="test-service",
            factory_func=factory_func,
            cleanup_func=cleanup_func,
        ) as value:
            # Factory should have been called
            self.assertTrue(factory_called)
            self.assertEqual(value, "created-value")

            # Find the resource
            resources = self.manager.find_resources(
                resource_type="test-type", state="in_use"
            )
            self.assertEqual(len(resources), 1)

        # Cleanup should have been called
        self.assertTrue(cleanup_called)

    def test_exception_handling(self):
        """Test that resources are released even if an exception occurs."""
        # Register a resource
        resource = self.manager.register_resource(
            resource_type="test-type", value="test-value"
        )

        try:
            # Use context manager with exception
            with managed_resource(
                manager=self.manager,
                resource_type="test-type",
                owner_service="test-service",
            ):
                # Resource should be acquired
                self.assertEqual(resource.state, "in_use")

                # Raise an exception
                raise ValueError("Test exception")

        except ValueError:
            # Exception should propagate
            pass

        # Resource should still be released
        self.assertEqual(resource.state, "released")


class TestGlobalResourceManager(unittest.TestCase):
    """Test global resource manager functions."""

    def test_create_resource_manager(self):
        """Test creating a new resource manager."""
        manager = create_resource_manager()

        # Should be a ResourceManager instance
        self.assertIsInstance(manager, ResourceManager)

        # Should be empty
        self.assertEqual(manager.find_resources(), [])

        # Should be able to register resources
        resource = manager.register_resource(
            resource_type="test-type", value="test-value"
        )
        self.assertEqual(resource.value, "test-value")


if __name__ == "__main__":
    unittest.main()
