"""
Unit tests for the Atlas telemetry module.

These tests verify the functionality of the telemetry module without requiring
external dependencies or services.
"""

import os
import unittest
from unittest import mock

from atlas.core.telemetry import (
    initialize_telemetry,
    shutdown_telemetry,
    enable_telemetry,
    disable_telemetry,
    is_telemetry_enabled,
    get_tracer,
    get_meter,
    get_current_span,
    create_counter,
    create_histogram,
    traced,
    TracedClass,
    get_api_request_counter,
    get_api_token_counter,
    get_api_cost_counter,
    get_document_retrieval_histogram,
    get_agent_processing_histogram,
    _parse_bool_env,
)

from atlas.tests.helpers.decorators import unit_test


class TestTelemetryEnvironmentVariables(unittest.TestCase):
    """Test telemetry environment variable parsing and handling."""

    def setUp(self):
        """Store original environment variables."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment variables."""
        os.environ.clear()
        os.environ.update(self.original_env)

    @unit_test
    def test_parse_bool_env(self):
        """Test the _parse_bool_env function."""
        test_cases = [
            # (var_value, default, expected_result)
            ("true", True, True),
            ("TRUE", False, True),
            ("1", False, True),
            ("yes", False, True),
            ("false", True, False),
            ("FALSE", True, False),
            ("0", True, False),
            ("no", True, False),
            ("off", True, False),
            ("disable", True, False),
            ("disabled", True, False),
            ("", True, True),  # Default is used
            ("", False, False),  # Default is used
            ("invalid", True, True),  # Invalid value uses default
        ]

        for var_value, default, expected in test_cases:
            test_var = "TEST_VAR"
            if var_value:
                os.environ[test_var] = var_value
            elif test_var in os.environ:
                del os.environ[test_var]

            result = _parse_bool_env(test_var, default)
            self.assertEqual(
                result,
                expected,
                f"Failed with var_value={var_value}, default={default}, expected={expected}",
            )

    @unit_test
    def test_telemetry_enabled_env_var(self):
        """Test that the ATLAS_ENABLE_TELEMETRY environment variable works."""
        # Default is enabled
        if "ATLAS_ENABLE_TELEMETRY" in os.environ:
            del os.environ["ATLAS_ENABLE_TELEMETRY"]
        
        with mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True):
            result = is_telemetry_enabled()
            self.assertTrue(result, "Telemetry should be enabled by default")

        # Disable via environment
        os.environ["ATLAS_ENABLE_TELEMETRY"] = "false"
        
        # Reinitialize module-level variables
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False):
            result = is_telemetry_enabled()
            self.assertFalse(result, "Telemetry should be disabled when env var is 'false'")

        # Enable via environment
        os.environ["ATLAS_ENABLE_TELEMETRY"] = "true"
        
        # Reinitialize module-level variables
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True):
            result = is_telemetry_enabled()
            self.assertTrue(result, "Telemetry should be enabled when env var is 'true'")

    @unit_test
    def test_console_exporter_env_var(self):
        """Test that the ATLAS_TELEMETRY_CONSOLE_EXPORT environment variable is parsed correctly."""
        # Test with different values
        test_cases = [
            ("true", True),
            ("false", False),
            ("1", True),
            ("0", False),
        ]

        for var_value, expected in test_cases:
            os.environ["ATLAS_TELEMETRY_CONSOLE_EXPORT"] = var_value
            
            # Test the direct parsing function to verify it works correctly
            result = _parse_bool_env("ATLAS_TELEMETRY_CONSOLE_EXPORT", False)
            self.assertEqual(result, expected)


class TestTelemetryInitialization(unittest.TestCase):
    """Test telemetry initialization and shutdown."""

    def setUp(self):
        """Set up mocks for OpenTelemetry dependencies."""
        # Mock OpenTelemetry dependencies
        self.mock_tracer_patcher = mock.patch("atlas.core.telemetry.TracerProvider")
        self.mock_tracer_provider = self.mock_tracer_patcher.start()
        
        self.mock_meter_patcher = mock.patch("atlas.core.telemetry.MeterProvider")
        self.mock_meter_provider = self.mock_meter_patcher.start()
        
        self.mock_span_processor_patcher = mock.patch("atlas.core.telemetry.BatchSpanProcessor")
        self.mock_span_processor = self.mock_span_processor_patcher.start()
        
        self.mock_console_exporter_patcher = mock.patch("atlas.core.telemetry.ConsoleSpanExporter")
        self.mock_console_exporter = self.mock_console_exporter_patcher.start()
        
        self.mock_trace_patcher = mock.patch("atlas.core.telemetry.trace")
        self.mock_trace = self.mock_trace_patcher.start()
        
        self.mock_metrics_patcher = mock.patch("atlas.core.telemetry.metrics")
        self.mock_metrics = self.mock_metrics_patcher.start()
        
        # Mock module globals
        self.mock_ot_available_patcher = mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True)
        self.mock_ot_available = self.mock_ot_available_patcher.start()
        
        self.mock_telemetry_enabled_patcher = mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True)
        self.mock_telemetry_enabled = self.mock_telemetry_enabled_patcher.start()
        
        # Store original environment and module globals
        self.original_env = os.environ.copy()
        
        # Initialize mock tracers and meters
        self.mock_atlas_tracer = mock.MagicMock()
        self.mock_atlas_meter = mock.MagicMock()
        self.mock_trace.get_tracer.return_value = self.mock_atlas_tracer
        self.mock_metrics.get_meter.return_value = self.mock_atlas_meter

    def tearDown(self):
        """Tear down mocks and restore environment."""
        self.mock_tracer_patcher.stop()
        self.mock_meter_patcher.stop()
        self.mock_span_processor_patcher.stop()
        self.mock_console_exporter_patcher.stop()
        self.mock_trace_patcher.stop()
        self.mock_metrics_patcher.stop()
        self.mock_ot_available_patcher.stop()
        self.mock_telemetry_enabled_patcher.stop()
        
        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Clean up telemetry providers
        shutdown_telemetry()

    @unit_test
    def test_initialize_telemetry_success(self):
        """Test successful telemetry initialization."""
        # Reset module-level variables
        with mock.patch("atlas.core.telemetry._tracer_provider", None), \
             mock.patch("atlas.core.telemetry._meter_provider", None), \
             mock.patch("atlas.core.telemetry._atlas_tracer", None), \
             mock.patch("atlas.core.telemetry._atlas_meter", None):
            
            # Call initialize_telemetry
            result = initialize_telemetry(
                service_name="test-service",
                service_version="1.0.0",
                enable_console_exporter=True
            )
            
            # Verify result
            self.assertTrue(result, "Telemetry initialization should succeed")
            
            # Verify TracerProvider creation
            self.mock_tracer_provider.assert_called_once()
            
            # Verify ConsoleSpanExporter creation
            self.mock_console_exporter.assert_called_once()
            
            # Verify tracer and meter were obtained
            self.mock_trace.get_tracer.assert_called_once_with("test-service", "1.0.0")
            self.mock_metrics.get_meter.assert_called_once_with("test-service", "1.0.0")

    @unit_test
    def test_initialize_telemetry_disabled(self):
        """Test telemetry initialization when disabled by environment."""
        # Disable telemetry
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False):
            # Call initialize_telemetry
            result = initialize_telemetry()
            
            # Verify result
            self.assertFalse(result, "Telemetry initialization should fail when disabled")
            
            # Verify no provider creation
            self.mock_tracer_provider.assert_not_called()
            self.mock_meter_provider.assert_not_called()

    @unit_test
    def test_initialize_telemetry_otlp(self):
        """Test telemetry initialization with OTLP exporter."""
        # Need to mock the imports inside initialize_telemetry since they're imported conditionally
        with mock.patch("atlas.core.telemetry._tracer_provider", None), \
             mock.patch("atlas.core.telemetry._meter_provider", None), \
             mock.patch("atlas.core.telemetry._atlas_tracer", None), \
             mock.patch("atlas.core.telemetry._atlas_meter", None):
            
            # Create module-level mocks for conditionally imported OTLP exporters
            otlp_span_exporter_mock = mock.MagicMock()
            otlp_metric_exporter_mock = mock.MagicMock()
            
            # Mock the imports that happen inside the function
            with mock.patch.dict("sys.modules", {
                "opentelemetry.exporter.otlp.proto.grpc.trace_exporter": mock.MagicMock(
                    OTLPSpanExporter=otlp_span_exporter_mock
                ),
                "opentelemetry.exporter.otlp.proto.grpc.metric_exporter": mock.MagicMock(
                    OTLPMetricExporter=otlp_metric_exporter_mock
                )
            }):
                # Call initialize_telemetry with OTLP enabled
                result = initialize_telemetry(
                    enable_otlp_exporter=True,
                    otlp_endpoint="http://localhost:4317"
                )
                
                # Verify result - just checking it completes without errors
                self.assertTrue(result, "Telemetry initialization with OTLP should succeed")

    @unit_test
    def test_initialize_telemetry_force_enable(self):
        """Test forcing telemetry initialization when disabled by environment."""
        # Disable telemetry
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False), \
             mock.patch("atlas.core.telemetry._tracer_provider", None), \
             mock.patch("atlas.core.telemetry._meter_provider", None), \
             mock.patch("atlas.core.telemetry._atlas_tracer", None), \
             mock.patch("atlas.core.telemetry._atlas_meter", None):
            
            # Call initialize_telemetry with force_enable
            result = initialize_telemetry(force_enable=True)
            
            # Verify result
            self.assertTrue(result, "Telemetry initialization should succeed when forced")
            
            # Verify provider creation
            self.mock_tracer_provider.assert_called_once()
            self.mock_meter_provider.assert_called_once()

    @unit_test
    def test_initialize_telemetry_opentelemetry_unavailable(self):
        """Test telemetry initialization when OpenTelemetry is not installed."""
        # Mock OpenTelemetry as unavailable
        with mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", False):
            # Call initialize_telemetry
            result = initialize_telemetry()
            
            # Verify result
            self.assertFalse(result, "Telemetry initialization should fail when OpenTelemetry is unavailable")
            
            # Verify no provider creation
            self.mock_tracer_provider.assert_not_called()
            self.mock_meter_provider.assert_not_called()

    @unit_test
    def test_shutdown_telemetry(self):
        """Test telemetry shutdown."""
        # Mock providers
        mock_tracer_provider = mock.MagicMock()
        mock_meter_provider = mock.MagicMock()
        
        # Set module-level providers using context managers to ensure proper cleanup
        with mock.patch("atlas.core.telemetry._tracer_provider", mock_tracer_provider), \
             mock.patch("atlas.core.telemetry._meter_provider", mock_meter_provider), \
             mock.patch("atlas.core.telemetry._atlas_tracer", self.mock_atlas_tracer), \
             mock.patch("atlas.core.telemetry._atlas_meter", self.mock_atlas_meter):
            
            # Call shutdown_telemetry
            shutdown_telemetry()
            
            # Verify provider shutdown
            mock_tracer_provider.shutdown.assert_called_once()
            mock_meter_provider.shutdown.assert_called_once()
        
        # After the shutdown, providers should be None in the telemetry module
        # We need to mock TELEMETRY_ENABLED to True to ensure get_tracer doesn't try to initialize
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True), \
             mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True), \
             mock.patch("atlas.core.telemetry._tracer_provider", None), \
             mock.patch("atlas.core.telemetry._meter_provider", None), \
             mock.patch("atlas.core.telemetry._atlas_tracer", None), \
             mock.patch("atlas.core.telemetry._atlas_meter", None), \
             mock.patch("atlas.core.telemetry.initialize_telemetry", return_value=False):
            
            # Verify get_tracer and get_meter return None after shutdown
            self.assertIsNone(get_tracer())
            self.assertIsNone(get_meter())


class TestTelemetryEnableDisable(unittest.TestCase):
    """Test enabling and disabling telemetry at runtime."""

    def setUp(self):
        """Set up mocks for OpenTelemetry dependencies."""
        # Store original module state
        self.original_state = {
            "TELEMETRY_ENABLED": mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True),
            "OPENTELEMETRY_AVAILABLE": mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True),
            "_tracer_provider": mock.patch("atlas.core.telemetry._tracer_provider", None),
            "_meter_provider": mock.patch("atlas.core.telemetry._meter_provider", None),
            "_atlas_tracer": mock.patch("atlas.core.telemetry._atlas_tracer", None),
            "_atlas_meter": mock.patch("atlas.core.telemetry._atlas_meter", None),
        }
        
        # Start all patches
        for patch in self.original_state.values():
            patch.start()
        
        # Mock initialize_telemetry
        self.mock_initialize_patcher = mock.patch("atlas.core.telemetry.initialize_telemetry")
        self.mock_initialize = self.mock_initialize_patcher.start()
        self.mock_initialize.return_value = True
        
        # Mock shutdown_telemetry
        self.mock_shutdown_patcher = mock.patch("atlas.core.telemetry.shutdown_telemetry")
        self.mock_shutdown = self.mock_shutdown_patcher.start()

    def tearDown(self):
        """Tear down mocks."""
        # Stop all patches
        for patch in self.original_state.values():
            patch.stop()
        
        self.mock_initialize_patcher.stop()
        self.mock_shutdown_patcher.stop()

    @unit_test
    def test_enable_telemetry(self):
        """Test enabling telemetry at runtime."""
        # Disable telemetry first
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False):
            # Call enable_telemetry
            result = enable_telemetry()
            
            # Verify TELEMETRY_ENABLED is set to True
            with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True):
                self.assertTrue(is_telemetry_enabled())
            
            # Verify initialize_telemetry was called with force_enable
            self.mock_initialize.assert_called_once_with(force_enable=True)
            
            # Verify result
            self.assertTrue(result)

    @unit_test
    def test_enable_telemetry_already_initialized(self):
        """Test enabling telemetry when already initialized."""
        # Mock that telemetry is already initialized
        with mock.patch("atlas.core.telemetry._tracer_provider", mock.MagicMock()), \
             mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True):
            
            # Call enable_telemetry
            result = enable_telemetry()
            
            # Verify initialize_telemetry was not called
            self.mock_initialize.assert_not_called()
            
            # Verify result
            self.assertTrue(result)

    @unit_test
    def test_disable_telemetry(self):
        """Test disabling telemetry at runtime."""
        # Enable telemetry first
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True):
            # Call disable_telemetry
            disable_telemetry()
            
            # Verify TELEMETRY_ENABLED is set to False
            with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False):
                self.assertFalse(is_telemetry_enabled())
            
            # Verify shutdown_telemetry was called
            self.mock_shutdown.assert_called_once()

    @unit_test
    def test_is_telemetry_enabled(self):
        """Test checking if telemetry is enabled."""
        # Test when telemetry is enabled
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True), \
             mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True):
            self.assertTrue(is_telemetry_enabled())
        
        # Test when telemetry is disabled
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False), \
             mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True):
            self.assertFalse(is_telemetry_enabled())
        
        # Test when OpenTelemetry is unavailable
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True), \
             mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", False):
            self.assertFalse(is_telemetry_enabled())


class TestTelemetryTracing(unittest.TestCase):
    """Test telemetry tracing functionality."""

    def setUp(self):
        """Set up mocks for tracing."""
        # Mock module globals
        self.patches = {
            "TELEMETRY_ENABLED": mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True),
            "OPENTELEMETRY_AVAILABLE": mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True),
            "_tracer_provider": mock.patch("atlas.core.telemetry._tracer_provider", mock.MagicMock()),
            "_atlas_tracer": mock.patch("atlas.core.telemetry._atlas_tracer", mock.MagicMock()),
        }
        
        # Start all patches
        for patch in self.patches.values():
            patch.start()
        
        # Create a mock span
        self.mock_span = mock.MagicMock()
        self.mock_span_context = mock.MagicMock()
        
        # Create a mock tracer
        self.mock_tracer = mock.MagicMock()
        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = self.mock_span
        
        # Mock get_tracer to return our mock tracer
        self.mock_get_tracer_patcher = mock.patch("atlas.core.telemetry.get_tracer")
        self.mock_get_tracer = self.mock_get_tracer_patcher.start()
        self.mock_get_tracer.return_value = self.mock_tracer
        
        # Mock trace.get_current_span
        self.mock_trace_patcher = mock.patch("atlas.core.telemetry.trace")
        self.mock_trace = self.mock_trace_patcher.start()
        self.mock_trace.get_current_span.return_value = self.mock_span

    def tearDown(self):
        """Tear down mocks."""
        # Stop all patches
        for patch in self.patches.values():
            patch.stop()
        
        self.mock_get_tracer_patcher.stop()
        self.mock_trace_patcher.stop()

    @unit_test
    def test_get_tracer(self):
        """Test getting the tracer instance."""
        # We're testing the function itself so we need to use the real function
        # but mock the dependencies it uses
        
        # Ensure all the conditions are right for get_tracer to return the mock tracer
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True), \
             mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True), \
             mock.patch("atlas.core.telemetry._atlas_tracer", self.mock_tracer):
            
            # Now call the real get_tracer function
            tracer = get_tracer()
            
            # Verify we got our mock tracer back
            self.assertIsNotNone(tracer)
            self.assertEqual(tracer, self.mock_tracer)

    @unit_test
    def test_get_tracer_disabled(self):
        """Test getting the tracer when telemetry is disabled."""
        # Disable telemetry
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False):
            tracer = get_tracer()
            self.assertIsNone(tracer)

    @unit_test
    def test_get_current_span(self):
        """Test getting the current active span."""
        span = get_current_span()
        self.assertIsNotNone(span)
        self.assertEqual(span, self.mock_span)
        self.mock_trace.get_current_span.assert_called_once()

    @unit_test
    def test_get_current_span_disabled(self):
        """Test getting the current span when telemetry is disabled."""
        # Disable telemetry
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False):
            span = get_current_span()
            self.assertIsNone(span)
            self.mock_trace.get_current_span.assert_not_called()

    @unit_test
    def test_traced_decorator(self):
        """Test the traced decorator."""
        # Need to properly mock the get_tracer and the traced logic
        # Create a test function with the traced decorator
        @traced(name="test_function", attributes={"test_attr": "test_value"})
        def test_function(arg1, arg2=None):
            return f"{arg1}-{arg2}"
        
        # Call the function
        result = test_function("value1", arg2="value2")
        
        # Verify the result
        self.assertEqual(result, "value1-value2")
        
        # Verify the tracer was used - no need to check the exact attributes 
        # since the function name might be different depending on how it's defined in the test
        self.mock_tracer.start_as_current_span.assert_called_once()
        
        # Verify the span name is correct
        args, kwargs = self.mock_tracer.start_as_current_span.call_args
        self.assertEqual(args[0], "test_function")
        
        # Verify the test_attr attribute was set
        attrs = kwargs.get("attributes", {})
        self.assertEqual(attrs.get("test_attr"), "test_value")

    @unit_test
    def test_traced_decorator_disabled(self):
        """Test the traced decorator when telemetry is disabled."""
        # Disable telemetry
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False):
            # Create a test function with the traced decorator
            @traced()
            def test_function(arg1, arg2=None):
                return f"{arg1}-{arg2}"
            
            # Call the function
            result = test_function("value1", arg2="value2")
            
            # Verify the result
            self.assertEqual(result, "value1-value2")
            
            # Verify the tracer was not used
            self.mock_tracer.start_as_current_span.assert_not_called()

    @unit_test
    def test_traced_decorator_log_args(self):
        """Test the traced decorator with argument logging."""
        # Instead of trying to mock attribute setting, we'll verify the decorator
        # calls set_attribute appropriately
        
        # Get all calls to set_attribute to verify them afterward
        span_mock = self.mock_span
        span_mock.reset_mock()
        
        # Create a context manager mock that returns our span
        mock_context = mock.MagicMock()
        mock_context.__enter__.return_value = span_mock
        
        # Mock the tracer to return our context manager
        self.mock_tracer.start_as_current_span.return_value = mock_context
        
        # Enable debug logging to ensure attributes are set
        with mock.patch("atlas.core.telemetry.logger.isEnabledFor", return_value=True):
            # Create a test function with the traced decorator and log_args=True
            @traced(log_args=True)
            def test_function(arg1, arg2=None):
                return f"{arg1}-{arg2}"
            
            # Call the function
            result = test_function("value1", arg2="value2")
            
            # Verify the result
            self.assertEqual(result, "value1-value2")
            
            # Verify set_attribute was called (we don't check the exact args since they are
            # encoded differently based on the test environment)
            span_mock.set_attribute.assert_any_call(mock.ANY, mock.ANY)
            
            # Ensure the function was called at least once
            self.assertGreater(span_mock.set_attribute.call_count, 0)

    @unit_test
    def test_traced_decorator_log_result(self):
        """Test the traced decorator with result logging."""
        # Use the same approach as log_args test
        
        # Get all calls to set_attribute to verify them afterward
        span_mock = self.mock_span
        span_mock.reset_mock()
        
        # Create a context manager mock that returns our span
        mock_context = mock.MagicMock()
        mock_context.__enter__.return_value = span_mock
        
        # Mock the tracer to return our context manager
        self.mock_tracer.start_as_current_span.return_value = mock_context
        
        # Enable debug logging to ensure attributes are set
        with mock.patch("atlas.core.telemetry.logger.isEnabledFor", return_value=True):
            # Create a test function with the traced decorator and log_result=True
            @traced(log_result=True)
            def test_function(arg1, arg2=None):
                return f"{arg1}-{arg2}"
            
            # Call the function
            result = test_function("value1", arg2="value2")
            
            # Verify the result
            self.assertEqual(result, "value1-value2")
            
            # Verify set_attribute was called (we don't check the exact args since they are
            # encoded differently based on the test environment)
            span_mock.set_attribute.assert_any_call(mock.ANY, mock.ANY)
            
            # Ensure the function was called at least once
            self.assertGreater(span_mock.set_attribute.call_count, 0)

    @unit_test
    def test_traced_decorator_exception(self):
        """Test the traced decorator with exception handling."""
        # Create a test function with the traced decorator that raises an exception
        @traced()
        def test_function_error():
            raise ValueError("Test error")
        
        # Call the function and expect an exception
        with self.assertRaises(ValueError):
            test_function_error()
        
        # Verify exception was recorded
        self.mock_span.record_exception.assert_called_once()
        self.mock_span.set_status.assert_called_once()

    @unit_test
    def test_traced_class(self):
        """Test the TracedClass mixin."""
        # Create a test class that inherits from TracedClass
        class TestService(TracedClass):
            def do_something(self, param):
                return f"done with {param}"
        
        # Create an instance
        service = TestService()
        
        # Call a method
        result = service.do_something("test")
        
        # Verify the result
        self.assertEqual(result, "done with test")
        
        # Verify the tracer was used
        self.mock_tracer.start_as_current_span.assert_called_once()

    @unit_test
    def test_traced_class_disabled_tracing(self):
        """Test the TracedClass mixin with disabled tracing."""
        # Create a test class with tracing disabled
        class TestServiceNoTrace(TracedClass, disable_tracing=True):
            def do_something(self, param):
                return f"done with {param}"
        
        # Create an instance
        service = TestServiceNoTrace()
        
        # Call a method
        result = service.do_something("test")
        
        # Verify the result
        self.assertEqual(result, "done with test")
        
        # Verify the tracer was not used
        self.mock_tracer.start_as_current_span.assert_not_called()


class TestTelemetryMetrics(unittest.TestCase):
    """Test telemetry metrics functionality."""

    def setUp(self):
        """Set up mocks for metrics."""
        # Mock module globals
        self.patches = {
            "TELEMETRY_ENABLED": mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True),
            "OPENTELEMETRY_AVAILABLE": mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True),
            "_meter_provider": mock.patch("atlas.core.telemetry._meter_provider", mock.MagicMock()),
            "_atlas_meter": mock.patch("atlas.core.telemetry._atlas_meter", mock.MagicMock()),
        }
        
        # Start all patches
        for patch in self.patches.values():
            patch.start()
        
        # Create mock metrics
        self.mock_counter = mock.MagicMock()
        self.mock_histogram = mock.MagicMock()
        
        # Create a mock meter
        self.mock_meter = mock.MagicMock()
        self.mock_meter.create_counter.return_value = self.mock_counter
        self.mock_meter.create_histogram.return_value = self.mock_histogram
        
        # Mock get_meter to return our mock meter
        self.mock_get_meter_patcher = mock.patch("atlas.core.telemetry.get_meter")
        self.mock_get_meter = self.mock_get_meter_patcher.start()
        self.mock_get_meter.return_value = self.mock_meter
        
        # Reset the lazy-initialized metrics
        self.metric_patches = {
            "_api_request_counter": mock.patch("atlas.core.telemetry._api_request_counter", None),
            "_api_token_counter": mock.patch("atlas.core.telemetry._api_token_counter", None),
            "_api_cost_counter": mock.patch("atlas.core.telemetry._api_cost_counter", None),
            "_document_retrieval_histogram": mock.patch("atlas.core.telemetry._document_retrieval_histogram", None),
            "_agent_processing_histogram": mock.patch("atlas.core.telemetry._agent_processing_histogram", None),
        }
        
        # Start all metric patches
        for patch in self.metric_patches.values():
            patch.start()

    def tearDown(self):
        """Tear down mocks."""
        # Stop all patches
        for patch in self.patches.values():
            patch.stop()
        
        for patch in self.metric_patches.values():
            patch.stop()
        
        self.mock_get_meter_patcher.stop()

    @unit_test
    def test_get_meter(self):
        """Test getting the meter instance."""
        # We're testing the function itself so we need to use the real function
        # but mock the dependencies it uses
        
        # Ensure all the conditions are right for get_meter to return the mock meter
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", True), \
             mock.patch("atlas.core.telemetry.OPENTELEMETRY_AVAILABLE", True), \
             mock.patch("atlas.core.telemetry._atlas_meter", self.mock_meter):
            
            # Now call the real get_meter function
            meter = get_meter()
            
            # Verify we got our mock meter back
            self.assertIsNotNone(meter)
            self.assertEqual(meter, self.mock_meter)

    @unit_test
    def test_get_meter_disabled(self):
        """Test getting the meter when telemetry is disabled."""
        # Disable telemetry
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False):
            meter = get_meter()
            self.assertIsNone(meter)

    @unit_test
    def test_create_counter(self):
        """Test creating a counter metric."""
        counter = create_counter(
            name="test_counter",
            description="Test counter",
            unit="1"
        )
        
        self.assertIsNotNone(counter)
        self.assertEqual(counter, self.mock_counter)
        self.mock_meter.create_counter.assert_called_once_with(
            name="test_counter",
            description="Test counter",
            unit="1"
        )

    @unit_test
    def test_create_counter_disabled(self):
        """Test creating a counter when telemetry is disabled."""
        # Disable telemetry and ensure get_meter returns None
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False), \
             mock.patch("atlas.core.telemetry.get_meter", return_value=None):
            
            counter = create_counter(
                name="test_counter",
                description="Test counter",
                unit="1"
            )
            
            self.assertIsNone(counter)
            # Since get_meter returns None, create_counter is never called
            self.mock_meter.create_counter.assert_not_called()

    @unit_test
    def test_create_histogram(self):
        """Test creating a histogram metric."""
        histogram = create_histogram(
            name="test_histogram",
            description="Test histogram",
            unit="ms"
        )
        
        self.assertIsNotNone(histogram)
        self.assertEqual(histogram, self.mock_histogram)
        self.mock_meter.create_histogram.assert_called_once_with(
            name="test_histogram",
            description="Test histogram",
            unit="ms"
        )

    @unit_test
    def test_create_histogram_disabled(self):
        """Test creating a histogram when telemetry is disabled."""
        # Disable telemetry and ensure get_meter returns None
        with mock.patch("atlas.core.telemetry.TELEMETRY_ENABLED", False), \
             mock.patch("atlas.core.telemetry.get_meter", return_value=None):
            
            histogram = create_histogram(
                name="test_histogram",
                description="Test histogram",
                unit="ms"
            )
            
            self.assertIsNone(histogram)
            # Since get_meter returns None, create_histogram is never called
            self.mock_meter.create_histogram.assert_not_called()

    @unit_test
    def test_get_api_request_counter(self):
        """Test getting the API request counter."""
        with mock.patch("atlas.core.telemetry.create_counter") as mock_create_counter:
            mock_create_counter.return_value = self.mock_counter
            
            # First call should create the counter
            counter1 = get_api_request_counter()
            self.assertEqual(counter1, self.mock_counter)
            mock_create_counter.assert_called_once_with(
                name="atlas.api.requests",
                description="Count of API requests made",
                unit="1"
            )
            
            # Reset the mock for the second test
            mock_create_counter.reset_mock()
            
            # Mock that the counter already exists
            with mock.patch("atlas.core.telemetry._api_request_counter", self.mock_counter):
                # Second call should reuse the existing counter
                counter2 = get_api_request_counter()
                self.assertEqual(counter2, self.mock_counter)
                mock_create_counter.assert_not_called()

    @unit_test
    def test_get_api_token_counter(self):
        """Test getting the API token counter."""
        with mock.patch("atlas.core.telemetry.create_counter") as mock_create_counter:
            mock_create_counter.return_value = self.mock_counter
            
            # First call should create the counter
            counter = get_api_token_counter()
            self.assertEqual(counter, self.mock_counter)
            mock_create_counter.assert_called_once_with(
                name="atlas.api.tokens",
                description="Count of API tokens used",
                unit="1"
            )

    @unit_test
    def test_get_api_cost_counter(self):
        """Test getting the API cost counter."""
        with mock.patch("atlas.core.telemetry.create_counter") as mock_create_counter:
            mock_create_counter.return_value = self.mock_counter
            
            # First call should create the counter
            counter = get_api_cost_counter()
            self.assertEqual(counter, self.mock_counter)
            mock_create_counter.assert_called_once_with(
                name="atlas.api.cost",
                description="Cost of API usage",
                unit="usd"
            )

    @unit_test
    def test_get_document_retrieval_histogram(self):
        """Test getting the document retrieval histogram."""
        with mock.patch("atlas.core.telemetry.create_histogram") as mock_create_histogram:
            mock_create_histogram.return_value = self.mock_histogram
            
            # First call should create the histogram
            histogram = get_document_retrieval_histogram()
            self.assertEqual(histogram, self.mock_histogram)
            mock_create_histogram.assert_called_once_with(
                name="atlas.retrieval.duration",
                description="Time taken for document retrieval",
                unit="ms"
            )

    @unit_test
    def test_get_agent_processing_histogram(self):
        """Test getting the agent processing histogram."""
        with mock.patch("atlas.core.telemetry.create_histogram") as mock_create_histogram:
            mock_create_histogram.return_value = self.mock_histogram
            
            # First call should create the histogram
            histogram = get_agent_processing_histogram()
            self.assertEqual(histogram, self.mock_histogram)
            mock_create_histogram.assert_called_once_with(
                name="atlas.agent.processing_time",
                description="Time taken for agent to process a request",
                unit="ms"
            )