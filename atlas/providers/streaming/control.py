"""
Stream control interface for Atlas providers.

This module provides interfaces and implementations for controlling streaming
responses, including pause, resume, and cancel operations.
"""

import abc
import enum
import logging
import threading
from typing import Callable, Dict, Any, Optional

from atlas.providers.errors import ProviderStreamError
from atlas.core.errors import ErrorSeverity

# Import ModelResponse when moving implementation to its own file
# for now, we'll use a forward reference
# from atlas.providers.messages import ModelResponse

logger = logging.getLogger(__name__)


class StreamState(str, enum.Enum):
    """Possible states of a stream."""

    INITIALIZING = "initializing"  # Stream is being set up but not started
    ACTIVE = "active"              # Stream is actively producing content
    PAUSED = "paused"              # Stream is temporarily paused
    CANCELLED = "cancelled"        # Stream was explicitly cancelled
    COMPLETED = "completed"        # Stream has naturally completed
    ERROR = "error"                # Stream encountered an error


class StreamControl(abc.ABC):
    """Interface for controlling a streaming response.
    
    This interface provides methods for controlling streaming response flow,
    including pause, resume, and cancel operations. It also provides information
    about the stream's current state and capabilities.
    """
    
    @property
    @abc.abstractmethod
    def state(self) -> StreamState:
        """Get the current state of the stream."""
        pass
    
    @property
    @abc.abstractmethod
    def can_pause(self) -> bool:
        """Whether this stream supports pausing."""
        pass
    
    @property
    @abc.abstractmethod
    def can_resume(self) -> bool:
        """Whether this stream can be resumed from a paused state."""
        pass
    
    @property
    @abc.abstractmethod
    def can_cancel(self) -> bool:
        """Whether this stream supports cancellation."""
        pass
    
    @abc.abstractmethod
    def pause(self) -> bool:
        """
        Pause the stream if supported.
        
        Returns:
            bool: True if the stream was paused, False otherwise.
        
        Raises:
            ProviderStreamError: If the pause operation fails.
        """
        pass
    
    @abc.abstractmethod
    def resume(self) -> bool:
        """
        Resume the stream if paused.
        
        Returns:
            bool: True if the stream was resumed, False otherwise.
        
        Raises:
            ProviderStreamError: If the resume operation fails.
        """
        pass
    
    @abc.abstractmethod
    def cancel(self) -> bool:
        """
        Cancel the stream if supported.
        
        Returns:
            bool: True if the stream was cancelled, False otherwise.
        
        Raises:
            ProviderStreamError: If the cancel operation fails.
        """
        pass
    
    @abc.abstractmethod
    def register_state_change_callback(self, callback: Callable[[StreamState], None]) -> None:
        """
        Register a callback to be called when the stream state changes.
        
        Args:
            callback: Function to call with the new state.
        """
        pass
    
    @abc.abstractmethod
    def register_content_callback(self, callback: Callable[[str, "ModelResponse"], None]) -> None:
        """
        Register a callback to be called when new content is available.
        
        Args:
            callback: Function to call with new content and updated response.
        """
        pass

    @abc.abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get stream performance metrics.
        
        Returns:
            Dict containing stream metrics such as tokens processed, 
            throughput, latency, etc.
        """
        pass


class StreamControlBase(StreamControl):
    """Base implementation of StreamControl interface.
    
    This class provides a foundation for implementing stream control
    capabilities with state management and callback registration.
    """
    
    def __init__(self):
        """Initialize the stream control base."""
        self._state_lock = threading.RLock()
        self._state = StreamState.INITIALIZING
        self._state_callbacks = []
        self._content_callbacks = []
        self._metrics = {
            "start_time": None,
            "end_time": None,
            "tokens_processed": 0,
            "chars_processed": 0,
            "chunks_processed": 0,
            "avg_token_per_sec": 0,
            "total_tokens": 0,
        }
        self._metrics_lock = threading.Lock()
    
    @property
    def state(self) -> StreamState:
        """Get the current state of the stream."""
        with self._state_lock:
            return self._state
    
    @property
    def can_pause(self) -> bool:
        """Whether this stream supports pausing."""
        # Default implementation supports pausing if active
        with self._state_lock:
            return self._state == StreamState.ACTIVE
    
    @property
    def can_resume(self) -> bool:
        """Whether this stream can be resumed from a paused state."""
        # Default implementation supports resuming if paused
        with self._state_lock:
            return self._state == StreamState.PAUSED
    
    @property
    def can_cancel(self) -> bool:
        """Whether this stream supports cancellation."""
        # Default implementation supports cancellation if active or paused
        with self._state_lock:
            return self._state in (StreamState.ACTIVE, StreamState.PAUSED)
    
    def _set_state(self, new_state: StreamState) -> None:
        """
        Set the stream state and notify callbacks.
        
        Args:
            new_state: The new state.
        """
        with self._state_lock:
            if self._state == new_state:
                return
            
            old_state = self._state
            self._state = new_state
        
        # Notify callbacks outside the lock to prevent deadlocks
        for callback in self._state_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}", exc_info=True)
        
        logger.debug(f"Stream state changed: {old_state} -> {new_state}")
    
    def register_state_change_callback(self, callback: Callable[[StreamState], None]) -> None:
        """
        Register a callback to be called when the stream state changes.
        
        Args:
            callback: Function to call with the new state.
        """
        with self._state_lock:
            self._state_callbacks.append(callback)
            # Immediately call with current state to initialize
            current_state = self._state
        
        try:
            callback(current_state)
        except Exception as e:
            logger.error(f"Error in initial state callback: {e}", exc_info=True)
    
    def register_content_callback(self, callback: Callable[[str, "ModelResponse"], None]) -> None:
        """
        Register a callback to be called when new content is available.
        
        Args:
            callback: Function to call with new content and updated response.
        """
        self._content_callbacks.append(callback)
    
    def pause(self) -> bool:
        """
        Pause the stream if supported.
        
        Returns:
            bool: True if the stream was paused, False otherwise.
        
        Raises:
            ProviderStreamError: If the pause operation fails.
        """
        with self._state_lock:
            if not self.can_pause:
                return False
            
            try:
                # Provider-specific pause implementation
                if self._pause_provider_stream():
                    self._set_state(StreamState.PAUSED)
                    return True
                return False
            except Exception as e:
                error = ProviderStreamError(
                    message=f"Failed to pause stream: {e}",
                    cause=e,
                    severity=ErrorSeverity.WARNING,
                    can_resume=True
                )
                logger.error(str(error), exc_info=True)
                raise error
    
    def resume(self) -> bool:
        """
        Resume the stream if paused.
        
        Returns:
            bool: True if the stream was resumed, False otherwise.
        
        Raises:
            ProviderStreamError: If the resume operation fails.
        """
        with self._state_lock:
            if not self.can_resume:
                return False
            
            try:
                # Provider-specific resume implementation
                if self._resume_provider_stream():
                    self._set_state(StreamState.ACTIVE)
                    return True
                return False
            except Exception as e:
                error = ProviderStreamError(
                    message=f"Failed to resume stream: {e}",
                    cause=e,
                    severity=ErrorSeverity.WARNING,
                    can_resume=False
                )
                logger.error(str(error), exc_info=True)
                raise error
    
    def cancel(self) -> bool:
        """
        Cancel the stream if supported.
        
        Returns:
            bool: True if the stream was cancelled, False otherwise.
        
        Raises:
            ProviderStreamError: If the cancel operation fails.
        """
        with self._state_lock:
            if not self.can_cancel:
                return False
            
            try:
                # Provider-specific cancel implementation
                if self._cancel_provider_stream():
                    self._set_state(StreamState.CANCELLED)
                    return True
                return False
            except Exception as e:
                error = ProviderStreamError(
                    message=f"Failed to cancel stream: {e}",
                    cause=e,
                    severity=ErrorSeverity.WARNING,
                    can_resume=False
                )
                logger.error(str(error), exc_info=True)
                raise error
    
    def _pause_provider_stream(self) -> bool:
        """
        Provider-specific implementation to pause the stream.
        
        Returns:
            bool: True if the stream was paused, False otherwise.
        """
        # Default implementation always succeeds
        return True
    
    def _resume_provider_stream(self) -> bool:
        """
        Provider-specific implementation to resume the stream.
        
        Returns:
            bool: True if the stream was resumed, False otherwise.
        """
        # Default implementation always succeeds
        return True
    
    def _cancel_provider_stream(self) -> bool:
        """
        Provider-specific implementation to cancel the stream.
        
        Returns:
            bool: True if the stream was cancelled, False otherwise.
        """
        # Default implementation always succeeds
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get stream performance metrics.
        
        Returns:
            Dict containing stream metrics such as tokens processed, 
            throughput, latency, etc.
        """
        with self._metrics_lock:
            # Make a copy to avoid thread safety issues
            return dict(self._metrics)
    
    def _update_metrics(self, delta: str) -> None:
        """
        Update the metrics with new content.
        
        Args:
            delta: The new content.
        """
        import time
        
        with self._metrics_lock:
            # Initialize start time if not set
            if self._metrics["start_time"] is None:
                self._metrics["start_time"] = time.time()
            
            # Update metrics
            self._metrics["chunks_processed"] += 1
            self._metrics["chars_processed"] += len(delta)
            
            # Estimate tokens (can be improved with actual tokenization)
            estimated_tokens = len(delta) / 4  # Rough estimate
            self._metrics["tokens_processed"] += estimated_tokens
            
            # Calculate rate
            elapsed = time.time() - self._metrics["start_time"]
            if elapsed > 0:
                self._metrics["avg_token_per_sec"] = self._metrics["tokens_processed"] / elapsed