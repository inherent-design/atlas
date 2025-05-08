"""
Telemetry module for Atlas framework.

This module provides OpenTelemetry integration for tracing, metrics, and
logging throughout the Atlas framework. Telemetry can be enabled/disabled
at runtime and through environment variables.

Environment variables:
    ATLAS_ENABLE_TELEMETRY: Set to "0" or "false" to disable telemetry (default: enabled)
    ATLAS_TELEMETRY_CONSOLE_EXPORT: Set to "0" or "false" to disable console exporting (default: enabled)
    ATLAS_TELEMETRY_LOG_LEVEL: Set the log level for telemetry (default: INFO)
"""

import os
import logging
import inspect
import functools
from typing import Optional, Dict, Any, Callable, TypeVar

# Import OpenTelemetry modules
try:
    from opentelemetry import trace, metrics
    from opentelemetry.trace import Span, Tracer, StatusCode
    from opentelemetry.metrics import Meter, Counter, Histogram
    from opentelemetry.trace.propagation.tracecontext import (
        TraceContextTextMapPropagator,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )

    # Flag to track if OpenTelemetry is available
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    # Provide stub classes for type checking when OpenTelemetry is not installed
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    metrics = None
    Span = Any
    Tracer = Any
    StatusCode = Any
    Meter = Any
    Counter = Any
    Histogram = Any
    TraceContextTextMapPropagator = Any
    Resource = Any
    TracerProvider = Any
    BatchSpanProcessor = Any
    ConsoleSpanExporter = Any
    MeterProvider = Any
    ConsoleMetricExporter = Any
    PeriodicExportingMetricReader = Any

# Type variable for function return type
T = TypeVar("T")

# Configure logger
logger = logging.getLogger(__name__)


# Parse environment variables
def _parse_bool_env(var_name: str, default: bool = True) -> bool:
    """Parse a boolean environment variable."""
    val = os.environ.get(var_name, str(default)).lower()
    return val not in ("0", "false", "no", "off", "disable", "disabled")


# Check if telemetry is enabled through environment variables
TELEMETRY_ENABLED = _parse_bool_env("ATLAS_ENABLE_TELEMETRY", True)
CONSOLE_EXPORT_ENABLED = _parse_bool_env("ATLAS_TELEMETRY_CONSOLE_EXPORT", False)

# Set log level from environment (default to INFO)
log_level_name = os.environ.get("ATLAS_TELEMETRY_LOG_LEVEL", "INFO").upper()
try:
    LOG_LEVEL = getattr(logging, log_level_name)
except AttributeError:
    LOG_LEVEL = logging.INFO
    logger.warning(f"Invalid log level: {log_level_name}, defaulting to INFO")

# Configure logger with the specified level
logger.setLevel(LOG_LEVEL)

# Global variables for telemetry provider instances
_tracer_provider = None
_meter_provider = None
_atlas_tracer = None
_atlas_meter = None

# Constants
SERVICE_NAME = "atlas"
SERVICE_VERSION = "0.1.0"  # Should be imported from version.py in the future


def initialize_telemetry(
    service_name: str = SERVICE_NAME,
    service_version: str = SERVICE_VERSION,
    enable_console_exporter: Optional[bool] = None,
    enable_otlp_exporter: bool = False,
    otlp_endpoint: Optional[str] = None,
    sampling_ratio: float = 1.0,
    force_enable: bool = False,
) -> bool:
    """Initialize OpenTelemetry for the Atlas service.

    Args:
        service_name: Name of the service for telemetry.
        service_version: Version of the service.
        enable_console_exporter: Whether to enable console exporters. If None, uses CONSOLE_EXPORT_ENABLED.
        enable_otlp_exporter: Whether to enable OTLP exporters.
        otlp_endpoint: Endpoint for OTLP exporter.
        sampling_ratio: Sampling ratio for traces (0.0 to 1.0).
        force_enable: Force enable telemetry even if disabled by environment variables.

    Returns:
        True if telemetry was initialized successfully, False otherwise.
    """
    global _tracer_provider, _meter_provider, _atlas_tracer, _atlas_meter

    # Use console exporter setting from environment if not explicitly provided
    if enable_console_exporter is None:
        enable_console_exporter = CONSOLE_EXPORT_ENABLED

    # Check if telemetry is disabled by environment variable and not forced
    if not TELEMETRY_ENABLED and not force_enable:
        logger.info("Telemetry is disabled by environment configuration.")
        return False

    # Check if OpenTelemetry is available
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning(
            "OpenTelemetry packages are not installed. Telemetry will be disabled."
        )
        return False

    # Check if telemetry is already initialized
    if _tracer_provider is not None:
        logger.info("Telemetry already initialized.")
        return True

    try:
        # Create resource information for the service
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
                "telemetry.sdk.name": "opentelemetry",
                "telemetry.sdk.language": "python",
            }
        )

        # Initialize tracer provider
        _tracer_provider = TracerProvider(resource=resource)

        # Add console exporter for development
        if enable_console_exporter:
            console_span_processor = BatchSpanProcessor(ConsoleSpanExporter())
            _tracer_provider.add_span_processor(console_span_processor)
            logger.debug("Console span exporter enabled")

        # Add OTLP exporter if enabled
        if enable_otlp_exporter and otlp_endpoint:
            # Import OTLP exporters only if needed
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )
                from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                    OTLPMetricExporter,
                )

                otlp_span_processor = BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=otlp_endpoint)
                )
                _tracer_provider.add_span_processor(otlp_span_processor)

                # Create metric reader - use in a future implementation
                # that configures metric export (currently not used)
                PeriodicExportingMetricReader(
                    OTLPMetricExporter(endpoint=otlp_endpoint)
                )
                logger.debug(f"OTLP exporter enabled with endpoint: {otlp_endpoint}")
            except ImportError:
                logger.warning(
                    "OTLP exporters not available. Install 'opentelemetry-exporter-otlp' package."
                )

        try:
            # Set the global tracer provider - may fail if one is already set
            trace.set_tracer_provider(_tracer_provider)
        except Exception as e:
            logger.debug(f"Could not set tracer provider: {e}. Continuing with existing provider.")

        # Get a tracer for Atlas
        _atlas_tracer = trace.get_tracer(service_name, service_version)

        # Initialize metrics
        readers = []
        if enable_console_exporter:
            console_metric_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter()
            )
            readers.append(console_metric_reader)

        # Create meter provider with configured readers
        if readers:
            _meter_provider = MeterProvider(resource=resource, metric_readers=readers)
        else:
            # When no readers are configured, create a basic meter provider without readers
            _meter_provider = MeterProvider(resource=resource)

        try:
            # Set the global meter provider - may fail if one is already set
            metrics.set_meter_provider(_meter_provider)
        except Exception as e:
            logger.debug(f"Could not set meter provider: {e}. Continuing with existing provider.")

        # Get a meter for Atlas
        _atlas_meter = metrics.get_meter(service_name, service_version)

        logger.info(
            f"Telemetry initialized for service {service_name} v{service_version}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to initialize telemetry: {str(e)}")
        _tracer_provider = None
        _meter_provider = None
        _atlas_tracer = None
        _atlas_meter = None
        return False


def shutdown_telemetry() -> None:
    """Gracefully shut down telemetry providers."""
    global _tracer_provider, _meter_provider, _atlas_tracer, _atlas_meter

    if _tracer_provider:
        logger.info("Shutting down tracer provider...")
        _tracer_provider.shutdown()
        _tracer_provider = None
        _atlas_tracer = None

    if _meter_provider:
        logger.info("Shutting down meter provider...")
        _meter_provider.shutdown()
        _meter_provider = None
        _atlas_meter = None


def enable_telemetry() -> bool:
    """Enable telemetry at runtime.

    Returns:
        True if telemetry was enabled successfully, False otherwise.
    """
    global TELEMETRY_ENABLED

    TELEMETRY_ENABLED = True

    # If telemetry is already initialized, we're good
    if _tracer_provider is not None:
        logger.info("Telemetry is already initialized and enabled.")
        return True

    # Initialize telemetry with force_enable to bypass environment settings
    return initialize_telemetry(force_enable=True)


def disable_telemetry() -> None:
    """Disable telemetry at runtime.

    This will stop any future span creation but won't affect existing spans.
    It will also shut down any active providers.
    """
    global TELEMETRY_ENABLED

    TELEMETRY_ENABLED = False
    logger.info("Telemetry has been disabled.")

    # Shut down any active providers
    shutdown_telemetry()


def is_telemetry_enabled() -> bool:
    """Check if telemetry is currently enabled.

    Returns:
        True if telemetry is enabled, False otherwise.
    """
    return TELEMETRY_ENABLED and (OPENTELEMETRY_AVAILABLE or False)


def get_tracer() -> Optional[Tracer]:
    """Get the Atlas tracer instance.

    Returns:
        The Atlas tracer or None if telemetry is not initialized or enabled.
    """
    global _atlas_tracer

    if not TELEMETRY_ENABLED or not OPENTELEMETRY_AVAILABLE:
        return None

    if _atlas_tracer is None:
        # Try to initialize with defaults if not already initialized
        if initialize_telemetry():
            return _atlas_tracer
        return None

    return _atlas_tracer


def get_meter() -> Optional[Meter]:
    """Get the Atlas meter instance.

    Returns:
        The Atlas meter or None if telemetry is not initialized or enabled.
    """
    global _atlas_meter

    if not TELEMETRY_ENABLED or not OPENTELEMETRY_AVAILABLE:
        return None

    if _atlas_meter is None:
        # Try to initialize with defaults if not already initialized
        if initialize_telemetry():
            return _atlas_meter
        return None

    return _atlas_meter


def get_current_span() -> Optional[Span]:
    """Get the current active span.

    Returns:
        The current span or None if no span is active or telemetry is disabled.
    """
    if not TELEMETRY_ENABLED or not OPENTELEMETRY_AVAILABLE or trace is None:
        return None

    return trace.get_current_span()


def create_counter(name: str, description: str, unit: str = "1") -> Optional[Counter]:
    """Create a counter metric.

    Args:
        name: Name of the counter.
        description: Description of the counter.
        unit: Unit of the counter.

    Returns:
        A counter metric or None if telemetry is not initialized.
    """
    meter = get_meter()
    if meter is None:
        return None

    return meter.create_counter(name=name, description=description, unit=unit)


def create_histogram(
    name: str, description: str, unit: str = "ms"
) -> Optional[Histogram]:
    """Create a histogram metric.

    Args:
        name: Name of the histogram.
        description: Description of the histogram.
        unit: Unit of the histogram.

    Returns:
        A histogram metric or None if telemetry is not initialized.
    """
    meter = get_meter()
    if meter is None:
        return None

    return meter.create_histogram(name=name, description=description, unit=unit)


def traced(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    log_args: bool = False,
    log_result: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to create a span around a function.

    Args:
        name: Name of the span. If None, the function name will be used.
        attributes: Initial attributes for the span.
        log_args: Whether to log function arguments to the span.
        log_result: Whether to log function result to the span.

    Returns:
        A decorator function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # If telemetry is disabled or not available, just call the function
            if not TELEMETRY_ENABLED or not OPENTELEMETRY_AVAILABLE:
                return func(*args, **kwargs)

            # Get the tracer
            tracer = get_tracer()
            if tracer is None:
                return func(*args, **kwargs)

            # Determine span name
            span_name = name if name is not None else func.__name__

            # Get the calling module and class
            module_name = func.__module__
            qualname = func.__qualname__

            # Prepare attributes
            span_attributes = {
                "code.function": qualname,
                "code.namespace": module_name,
            }

            # Add custom attributes if provided
            if attributes:
                span_attributes.update(attributes)

            # Log start with details if in debug mode
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Starting span: {span_name}")

            # Start a new span
            with tracer.start_as_current_span(
                span_name, attributes=span_attributes
            ) as span:
                try:
                    # Log arguments if requested
                    if log_args and logger.isEnabledFor(logging.DEBUG):
                        # Remove self for instance methods
                        arg_list = (
                            list(args[1:])
                            if args and qualname.split(".")[0] != func.__name__
                            else list(args)
                        )
                        arg_dict = {**kwargs}

                        # Truncate large values and convert to strings
                        def truncate_value(val: Any) -> str:
                            s = str(val)
                            return s[:100] + "..." if len(s) > 100 else s

                        args_str = ", ".join([truncate_value(a) for a in arg_list])
                        kwargs_str = ", ".join(
                            [f"{k}={truncate_value(v)}" for k, v in arg_dict.items()]
                        )

                        span.set_attribute("function.args", args_str)
                        span.set_attribute("function.kwargs", kwargs_str)
                        logger.debug(
                            f"Function {qualname} called with args: {args_str}, kwargs: {kwargs_str}"
                        )

                    # Call the original function
                    result = func(*args, **kwargs)

                    # Log result if requested
                    if log_result and logger.isEnabledFor(logging.DEBUG):
                        result_str = str(result)
                        if len(result_str) > 100:
                            result_str = result_str[:100] + "..."
                        span.set_attribute("function.result", result_str)
                        logger.debug(f"Function {qualname} returned: {result_str}")

                    return result
                except Exception as ex:
                    # Record the exception in the span
                    span.record_exception(ex)
                    span.set_status(StatusCode.ERROR, str(ex))
                    logger.error(f"Exception in {qualname}: {str(ex)}", exc_info=True)
                    raise
                finally:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Ending span: {span_name}")

        return wrapper

    return decorator


class TracedClass:
    """Mixin class to add tracing to a class.

    This mixin adds tracing to all public methods of a class.

    Example:
        ```python
        class MyAgent(TracedClass):
            def process_message(self, message: str) -> str:
                # This method will be automatically traced
                return "response"
        ```
    """

    def __init_subclass__(cls, disable_tracing: bool = False, **kwargs: Any) -> None:
        """Initialize subclass with tracing for all methods.

        Args:
            disable_tracing: Whether to disable tracing for this class.
        """
        super().__init_subclass__(**kwargs)

        # Skip if tracing is disabled for this class
        if disable_tracing:
            logger.debug(f"Tracing disabled for class {cls.__name__}")
            return

        # Skip if telemetry is not available or enabled
        if not TELEMETRY_ENABLED or not OPENTELEMETRY_AVAILABLE:
            return

        # Get all methods defined in the class
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            # Skip dunder methods and private methods
            if name.startswith("__") or name.startswith("_"):
                continue

            # Apply the traced decorator
            setattr(cls, name, traced()(method))


# Define metrics but initialize them lazily
_api_request_counter = None
_api_token_counter = None
_api_cost_counter = None
_document_retrieval_histogram = None
_agent_processing_histogram = None


def get_api_request_counter():
    """Get the API request counter metric, initializing it if needed."""
    global _api_request_counter
    if _api_request_counter is None:
        _api_request_counter = create_counter(
            name="atlas.api.requests", description="Count of API requests made", unit="1"
        )
    return _api_request_counter


def get_api_token_counter():
    """Get the API token counter metric, initializing it if needed."""
    global _api_token_counter
    if _api_token_counter is None:
        _api_token_counter = create_counter(
            name="atlas.api.tokens", description="Count of API tokens used", unit="1"
        )
    return _api_token_counter


def get_api_cost_counter():
    """Get the API cost counter metric, initializing it if needed."""
    global _api_cost_counter
    if _api_cost_counter is None:
        _api_cost_counter = create_counter(
            name="atlas.api.cost", description="Cost of API usage", unit="usd"
        )
    return _api_cost_counter


def get_document_retrieval_histogram():
    """Get the document retrieval histogram metric, initializing it if needed."""
    global _document_retrieval_histogram
    if _document_retrieval_histogram is None:
        _document_retrieval_histogram = create_histogram(
            name="atlas.retrieval.duration",
            description="Time taken for document retrieval",
            unit="ms",
        )
    return _document_retrieval_histogram


def get_agent_processing_histogram():
    """Get the agent processing histogram metric, initializing it if needed."""
    global _agent_processing_histogram
    if _agent_processing_histogram is None:
        _agent_processing_histogram = create_histogram(
            name="atlas.agent.processing_time",
            description="Time taken for agent to process a request",
            unit="ms",
        )
    return _agent_processing_histogram

# Example usage:
#
# @traced(name="process_document", attributes={"document_type": "markdown"})
# def process_document(doc_id: str) -> str:
#     # Function implementation
#     return "processed"
#
# class MyAgent(TracedClass):
#     def process_message(self, message: str) -> str:
#         # This method will be automatically traced
#         return "response"
