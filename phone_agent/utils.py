"""Utilities module for Phone Agent."""

import functools
import logging
import subprocess
import time
from typing import Any, Callable, TypeVar

# Configure logger
logger = logging.getLogger("phone_agent")

T = TypeVar("T")


def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    format_string: str | None = None,
) -> None:
    """
    Configure logging for Phone Agent.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional file path to save logs.
        format_string: Custom format string for log messages.

    Example:
        >>> setup_logging(logging.DEBUG, log_file="agent.log")
    """
    if format_string is None:
        format_string = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
    )

    logger.setLevel(level)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator for retrying a function on failure.

    Args:
        max_attempts: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.
        exceptions: Tuple of exceptions to catch and retry on.

    Example:
        >>> @retry(max_attempts=3, delay=0.5)
        ... def flaky_function():
        ...     # May fail sometimes
        ...     pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )

            raise last_exception  # type: ignore

        return wrapper

    return decorator


def run_adb_command(
    args: list[str],
    device_id: str | None = None,
    timeout: int = 10,
    check: bool = False,
) -> subprocess.CompletedProcess:
    """
    Run an ADB command with proper error handling.

    Args:
        args: Command arguments (without 'adb' prefix).
        device_id: Optional device ID for multi-device setups.
        timeout: Command timeout in seconds.
        check: If True, raise exception on non-zero exit code.

    Returns:
        CompletedProcess with stdout, stderr, and returncode.

    Example:
        >>> result = run_adb_command(["shell", "input", "tap", "100", "200"])
        >>> print(result.stdout)
    """
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(args)

    logger.debug(f"Running ADB: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )

    return result


@retry(max_attempts=3, delay=0.5, exceptions=(subprocess.TimeoutExpired, OSError))
def run_adb_with_retry(
    args: list[str],
    device_id: str | None = None,
    timeout: int = 10,
) -> subprocess.CompletedProcess:
    """
    Run an ADB command with automatic retry on failure.

    Uses retry decorator to handle flaky ADB connections.

    Args:
        args: Command arguments (without 'adb' prefix).
        device_id: Optional device ID.
        timeout: Command timeout in seconds.

    Returns:
        CompletedProcess with command results.
    """
    return run_adb_command(args, device_id, timeout, check=False)
