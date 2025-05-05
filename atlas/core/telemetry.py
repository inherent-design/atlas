"""
Telemetry module for Atlas framework.

This module provides OpenTelemetry integration for tracing, metrics, and
logging throughout the Atlas framework.
"""

import os
import logging
import inspect
import functools
from typing import Optional, Dict, Any, Callable, TypeVar, cast

# Import OpenTelemetry modules
try:
    from opentelemetry import trace, metrics
    from opentelemetry.trace import Span, Tracer, StatusCode
    from opentelemetry.metrics import Meter, Counter, Histogram
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

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
T = TypeVar('T')

# Configure logger
logger = logging.getLogger(__name__)

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
    enable_console_exporter: bool = True,
    enable_otlp_exporter: bool = False,
    otlp_endpoint: Optional[str] = None,
    sampling_ratio: float = 1.0,
) -> bool:
    """Initialize OpenTelemetry for the Atlas service.
    
    Args:
        service_name: Name of the service for telemetry.
        service_version: Version of the service.
        enable_console_exporter: Whether to enable console exporters.
        enable_otlp_exporter: Whether to enable OTLP exporters.
        otlp_endpoint: Endpoint for OTLP exporter.
        sampling_ratio: Sampling ratio for traces (0.0 to 1.0).
        
    Returns:
        True if telemetry was initialized successfully, False otherwise.
    """
    global _tracer_provider, _meter_provider, _atlas_tracer, _atlas_meter
    
    # Check if OpenTelemetry is available
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry packages are not installed. Telemetry will be disabled.")
        return False
    
    # Check if telemetry is already initialized
    if _tracer_provider is not None:
        logger.info("Telemetry already initialized.")
        return True
    
    try:
        # Create resource information for the service
        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
        })
        
        # Initialize tracer provider
        _tracer_provider = TracerProvider(resource=resource)
        
        # Add console exporter for development
        if enable_console_exporter:
            console_span_processor = BatchSpanProcessor(ConsoleSpanExporter())
            _tracer_provider.add_span_processor(console_span_processor)
            
        # Add OTLP exporter if enabled
        if enable_otlp_exporter and otlp_endpoint:
            # Import OTLP exporters only if needed
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
                
                otlp_span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
                _tracer_provider.add_span_processor(otlp_span_processor)
                
                otlp_metric_reader = PeriodicExportingMetricReader(
                    OTLPMetricExporter(endpoint=otlp_endpoint)
                )
            except ImportError:
                logger.warning("OTLP exporters not available. Install 'opentelemetry-exporter-otlp' package.")
                
        # Set the global tracer provider
        trace.set_tracer_provider(_tracer_provider)
        
        # Get a tracer for Atlas
        _atlas_tracer = trace.get_tracer(service_name, service_version)
        
        # Initialize metrics
        _meter_provider = MeterProvider(resource=resource)
        
        # Add console exporter for metrics in development
        if enable_console_exporter:
            console_metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
            _meter_provider = MeterProvider(resource=resource, metric_readers=[console_metric_reader])
        
        # Set the global meter provider
        metrics.set_meter_provider(_meter_provider)
        
        # Get a meter for Atlas
        _atlas_meter = metrics.get_meter(service_name, service_version)
        
        logger.info(f"Telemetry initialized for service {service_name} v{service_version}")
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


def get_tracer() -> Optional[Tracer]:
    """Get the Atlas tracer instance.
    
    Returns:
        The Atlas tracer or None if telemetry is not initialized.
    """
    global _atlas_tracer
    
    if not OPENTELEMETRY_AVAILABLE:
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
        The Atlas meter or None if telemetry is not initialized.
    """
    global _atlas_meter
    
    if not OPENTELEMETRY_AVAILABLE:
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
        The current span or None if no span is active.
    """
    if not OPENTELEMETRY_AVAILABLE or trace is None:
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


def create_histogram(name: str, description: str, unit: str = "ms") -> Optional[Histogram]:
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
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to create a span around a function.
    
    Args:
        name: Name of the span. If None, the function name will be used.
        attributes: Initial attributes for the span.
        
    Returns:
        A decorator function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # If OpenTelemetry is not available, just call the function
            if not OPENTELEMETRY_AVAILABLE:
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
                
            # Start a new span
            with tracer.start_as_current_span(span_name, attributes=span_attributes) as span:
                try:
                    # Call the original function
                    result = func(*args, **kwargs)
                    return result
                except Exception as ex:
                    # Record the exception in the span
                    span.record_exception(ex)
                    span.set_status(StatusCode.ERROR, str(ex))
                    raise
                    
        return wrapper
        
    return decorator


class TracedClass:
    """Mixin class to add tracing to a class.
    
    This mixin adds tracing to all public methods of a class.
    """
    
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Initialize subclass with tracing for all methods."""
        super().__init_subclass__(**kwargs)
        
        # Skip if OpenTelemetry is not available
        if not OPENTELEMETRY_AVAILABLE:
            return
            
        # Get all methods defined in the class
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            # Skip dunder methods and private methods
            if name.startswith('__') or name.startswith('_'):
                continue
                
            # Apply the traced decorator
            setattr(cls, name, traced()(method))


# Create metrics for common operations
api_request_counter = create_counter(
    name="atlas.api.requests",
    description="Count of API requests made",
    unit="1"
)

api_token_counter = create_counter(
    name="atlas.api.tokens",
    description="Count of API tokens used",
    unit="1"
)

api_cost_counter = create_counter(
    name="atlas.api.cost",
    description="Cost of API usage",
    unit="usd"
)

document_retrieval_histogram = create_histogram(
    name="atlas.retrieval.duration",
    description="Time taken for document retrieval",
    unit="ms"
)

agent_processing_histogram = create_histogram(
    name="atlas.agent.processing_time",
    description="Time taken for agent to process a request",
    unit="ms"
)

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