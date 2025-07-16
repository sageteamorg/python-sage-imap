import inspect
import logging
import time
from collections import defaultdict
from functools import lru_cache, wraps
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from sage_imap.exceptions import (
    IMAPAuthenticationError,
    IMAPClientError,
    IMAPConfigurationError,
    IMAPConnectionError,
    IMAPMailboxSelectionError,
)

logger = logging.getLogger(__name__)

# Type variable for generic decorators
F = TypeVar("F", bound=Callable[..., Any])

# Global performance metrics storage
_performance_metrics: Dict[str, List[float]] = defaultdict(list)
_metrics_lock = Lock()

# Cache for validation results
_validation_cache: Dict[str, Any] = {}
_cache_lock = Lock()


def mailbox_selection_required(func: F) -> F:
    """
    Decorator to ensure a mailbox is selected before executing the function.

    Parameters
    ----------
    func : Callable
        Function to decorate.

    Returns
    -------
    Callable
        Decorated function.

    Raises
    ------
    IMAPMailboxSelectionError
        If no mailbox is selected.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, "current_selection") or not self.current_selection:
            raise IMAPMailboxSelectionError("No mailbox selected.")
        return func(self, *args, **kwargs)

    return wrapper


def connection_required(func: F) -> F:
    """
    Decorator to ensure an IMAP connection is established before executing the function.

    Parameters
    ----------
    func : Callable
        Function to decorate.

    Returns
    -------
    Callable
        Decorated function.

    Raises
    ------
    IMAPConnectionError
        If no connection is established.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, "connection") or not self.connection:
            raise IMAPConnectionError("No IMAP connection established.")
        return func(self, *args, **kwargs)

    return wrapper


def authenticated_required(func: F) -> F:
    """
    Decorator to ensure the user is authenticated before executing the function.

    Parameters
    ----------
    func : Callable
        Function to decorate.

    Returns
    -------
    Callable
        Decorated function.

    Raises
    ------
    IMAPAuthenticationError
        If user is not authenticated.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, "authenticated") or not self.authenticated:
            raise IMAPAuthenticationError("User is not authenticated.")
        return func(self, *args, **kwargs)

    return wrapper


def performance_monitor(
    track_time: bool = True,
    track_memory: bool = False,
    log_performance: bool = True,
    store_metrics: bool = True,
):
    """
    Decorator to monitor function performance including execution time and memory usage.

    Parameters
    ----------
    track_time : bool, optional
        Whether to track execution time, by default True.
    track_memory : bool, optional
        Whether to track memory usage, by default False.
    log_performance : bool, optional
        Whether to log performance metrics, by default True.
    store_metrics : bool, optional
        Whether to store metrics for later analysis, by default True.

    Returns
    -------
    Callable
        Decorator function.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"
            start_time = time.time() if track_time else None
            start_memory = None

            if track_memory:
                try:
                    import psutil

                    process = psutil.Process()
                    start_memory = process.memory_info().rss
                except ImportError:
                    logger.warning("psutil not available for memory tracking")

            try:
                result = func(*args, **kwargs)

                # Calculate metrics
                if track_time:
                    execution_time = time.time() - start_time

                    if store_metrics:
                        with _metrics_lock:
                            _performance_metrics[func_name].append(execution_time)

                    if log_performance:
                        logger.info(
                            f"Function '{func_name}' executed in {execution_time:.3f}s"
                        )

                if track_memory and start_memory:
                    try:
                        end_memory = process.memory_info().rss
                        memory_diff = end_memory - start_memory
                        if log_performance:
                            logger.info(
                                f"Function '{func_name}' memory usage: {memory_diff / 1024 / 1024:.2f} MB"
                            )
                    except:
                        pass

                return result

            except Exception as e:
                if track_time and log_performance:
                    execution_time = time.time() - start_time
                    logger.error(
                        f"Function '{func_name}' failed after {execution_time:.3f}s: {e}"
                    )
                raise

        return wrapper

    return decorator


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = True,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """
    Decorator to retry function execution on failure with configurable backoff.

    Parameters
    ----------
    max_retries : int, optional
        Maximum number of retry attempts, by default 3.
    delay : float, optional
        Initial delay between retries in seconds, by default 1.0.
    exponential_backoff : bool, optional
        Whether to use exponential backoff, by default True.
    exceptions : tuple, optional
        Tuple of exceptions to catch and retry on, by default (Exception,).
    on_retry : Optional[Callable], optional
        Callback function to call on each retry, by default None.

    Returns
    -------
    Callable
        Decorator function.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt + 1, e)

                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)

                        if exponential_backoff:
                            current_delay = min(
                                current_delay * 2, 30.0
                            )  # Cap at 30 seconds
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper

    return decorator


def validate_parameters(**validators):
    """
    Decorator to validate function parameters using custom validator functions.

    Parameters
    ----------
    **validators : dict
        Dictionary mapping parameter names to validator functions.

    Returns
    -------
    Callable
        Decorator function.

    Raises
    ------
    IMAPConfigurationError
        If parameter validation fails.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate parameters
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        if not validator(value):
                            raise IMAPConfigurationError(
                                f"Invalid value for parameter '{param_name}': {value}"
                            )
                    except Exception as e:
                        raise IMAPConfigurationError(
                            f"Validation failed for parameter '{param_name}': {e}"
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_function_calls(
    log_level: int = logging.INFO,
    log_args: bool = False,
    log_result: bool = False,
    log_exceptions: bool = True,
):
    """
    Decorator to log function calls with configurable detail level.

    Parameters
    ----------
    log_level : int, optional
        Logging level to use, by default logging.INFO.
    log_args : bool, optional
        Whether to log function arguments, by default False.
    log_result : bool, optional
        Whether to log function result, by default False.
    log_exceptions : bool, optional
        Whether to log exceptions, by default True.

    Returns
    -------
    Callable
        Decorator function.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"

            # Log function entry
            if log_args:
                logger.log(
                    log_level, f"Calling {func_name} with args={args}, kwargs={kwargs}"
                )
            else:
                logger.log(log_level, f"Calling {func_name}")

            try:
                result = func(*args, **kwargs)

                # Log function result
                if log_result:
                    logger.log(log_level, f"{func_name} returned: {result}")
                else:
                    logger.log(log_level, f"{func_name} completed successfully")

                return result

            except Exception as e:
                if log_exceptions:
                    logger.error(f"{func_name} raised exception: {e}")
                raise

        return wrapper

    return decorator


def cache_result(
    ttl: Optional[int] = None,
    maxsize: int = 128,
    typed: bool = False,
    key_func: Optional[Callable] = None,
):
    """
    Decorator to cache function results with optional TTL (Time To Live).

    Parameters
    ----------
    ttl : Optional[int], optional
        Time to live for cached results in seconds, by default None (no expiration).
    maxsize : int, optional
        Maximum cache size, by default 128.
    typed : bool, optional
        Whether to cache different types separately, by default False.
    key_func : Optional[Callable], optional
        Custom function to generate cache keys, by default None.

    Returns
    -------
    Callable
        Decorator function.
    """

    def decorator(func: F) -> F:
        if ttl is None:
            # Use standard lru_cache for no expiration
            return lru_cache(maxsize=maxsize, typed=typed)(func)

        # Custom cache with TTL
        cache = {}
        cache_times = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = str(args) + str(sorted(kwargs.items()))

            current_time = time.time()

            # Check if result is cached and not expired
            if cache_key in cache:
                if current_time - cache_times[cache_key] < ttl:
                    return cache[cache_key]
                else:
                    # Remove expired entry
                    del cache[cache_key]
                    del cache_times[cache_key]

            # Compute result and cache it
            result = func(*args, **kwargs)

            # Maintain cache size
            if len(cache) >= maxsize:
                # Remove oldest entry
                oldest_key = min(cache_times.keys(), key=lambda k: cache_times[k])
                del cache[oldest_key]
                del cache_times[oldest_key]

            cache[cache_key] = result
            cache_times[cache_key] = current_time

            return result

        # Add cache management methods
        wrapper.cache_clear = lambda: cache.clear() or cache_times.clear()
        wrapper.cache_info = lambda: {
            "size": len(cache),
            "maxsize": maxsize,
            "ttl": ttl,
        }

        return wrapper

    return decorator


def rate_limit(calls: int, period: float):
    """
    Decorator to rate limit function calls.

    Parameters
    ----------
    calls : int
        Number of allowed calls per period.
    period : float
        Time period in seconds.

    Returns
    -------
    Callable
        Decorator function.

    Raises
    ------
    IMAPClientError
        If rate limit is exceeded.
    """

    def decorator(func: F) -> F:
        call_times = []
        lock = Lock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                current_time = time.time()

                # Remove old calls outside the period
                call_times[:] = [t for t in call_times if current_time - t < period]

                # Check rate limit
                if len(call_times) >= calls:
                    raise IMAPClientError(
                        f"Rate limit exceeded: {calls} calls per {period} seconds"
                    )

                # Record this call
                call_times.append(current_time)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_types(**type_validators):
    """
    Decorator to validate parameter types.

    Parameters
    ----------
    **type_validators : dict
        Dictionary mapping parameter names to expected types.

    Returns
    -------
    Callable
        Decorator function.

    Raises
    ------
    IMAPConfigurationError
        If type validation fails.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate types
            for param_name, expected_type in type_validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is not None and not isinstance(value, expected_type):
                        raise IMAPConfigurationError(
                            f"Parameter '{param_name}' must be of type {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def timeout(seconds: float):
    """
    Decorator to add timeout to function execution.

    Parameters
    ----------
    seconds : float
        Timeout in seconds.

    Returns
    -------
    Callable
        Decorator function.

    Raises
    ------
    IMAPClientError
        If function execution times out.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                raise IMAPClientError(
                    f"Function {func.__name__} timed out after {seconds} seconds"
                )

            # Set up timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Restore old handler and cancel alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper

    return decorator


def exception_handler(
    exceptions: Union[Type[Exception], tuple] = Exception,
    default_return: Any = None,
    log_exceptions: bool = True,
    reraise: bool = False,
):
    """
    Decorator to handle exceptions gracefully.

    Parameters
    ----------
    exceptions : Union[Type[Exception], tuple], optional
        Exception types to catch, by default Exception.
    default_return : Any, optional
        Default value to return on exception, by default None.
    log_exceptions : bool, optional
        Whether to log caught exceptions, by default True.
    reraise : bool, optional
        Whether to reraise exceptions after handling, by default False.

    Returns
    -------
    Callable
        Decorator function.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_exceptions:
                    logger.error(f"Exception in {func.__name__}: {e}")

                if reraise:
                    raise

                return default_return

        return wrapper

    return decorator


def deprecated(message: str = "", version: str = ""):
    """
    Decorator to mark functions as deprecated.

    Parameters
    ----------
    message : str, optional
        Deprecation message, by default "".
    version : str, optional
        Version when function was deprecated, by default "".

    Returns
    -------
    Callable
        Decorator function.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import warnings

            deprecation_msg = f"Function {func.__name__} is deprecated"
            if version:
                deprecation_msg += f" since version {version}"
            if message:
                deprecation_msg += f": {message}"

            warnings.warn(deprecation_msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_performance_metrics(func_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get performance metrics for monitored functions.

    Parameters
    ----------
    func_name : Optional[str], optional
        Specific function name to get metrics for, by default None (all functions).

    Returns
    -------
    Dict[str, Any]
        Performance metrics dictionary.
    """
    with _metrics_lock:
        if func_name:
            times = _performance_metrics.get(func_name, [])
            if not times:
                return {}

            return {
                "function": func_name,
                "call_count": len(times),
                "total_time": sum(times),
                "average_time": sum(times) / len(times),
                "min_time": min(times),
                "max_time": max(times),
                "last_call_time": times[-1] if times else None,
            }
        else:
            metrics = {}
            for func_name, times in _performance_metrics.items():
                if times:
                    metrics[func_name] = {
                        "call_count": len(times),
                        "total_time": sum(times),
                        "average_time": sum(times) / len(times),
                        "min_time": min(times),
                        "max_time": max(times),
                        "last_call_time": times[-1],
                    }
            return metrics


def clear_performance_metrics(func_name: Optional[str] = None):
    """
    Clear performance metrics.

    Parameters
    ----------
    func_name : Optional[str], optional
        Specific function name to clear metrics for, by default None (all functions).
    """
    with _metrics_lock:
        if func_name:
            _performance_metrics.pop(func_name, None)
        else:
            _performance_metrics.clear()


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception,
):
    """
    Decorator implementing circuit breaker pattern.

    Parameters
    ----------
    failure_threshold : int, optional
        Number of failures before opening circuit, by default 5.
    recovery_timeout : float, optional
        Time to wait before attempting recovery, by default 60.0.
    expected_exception : Type[Exception], optional
        Exception type that triggers circuit breaker, by default Exception.

    Returns
    -------
    Callable
        Decorator function.
    """

    def decorator(func: F) -> F:
        state = {"failures": 0, "last_failure_time": None, "state": "closed"}

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            # Check if circuit should be reset
            if (
                state["state"] == "open"
                and state["last_failure_time"]
                and current_time - state["last_failure_time"] > recovery_timeout
            ):
                state["state"] = "half-open"
                state["failures"] = 0

            # Reject calls if circuit is open
            if state["state"] == "open":
                raise IMAPClientError(
                    f"Circuit breaker is open for {func.__name__}. "
                    f"Try again after {recovery_timeout} seconds."
                )

            try:
                result = func(*args, **kwargs)

                # Reset on success
                if state["state"] == "half-open":
                    state["state"] = "closed"
                state["failures"] = 0

                return result

            except expected_exception:
                state["failures"] += 1
                state["last_failure_time"] = current_time

                if state["failures"] >= failure_threshold:
                    state["state"] = "open"
                    logger.warning(f"Circuit breaker opened for {func.__name__}")

                raise

        return wrapper

    return decorator
