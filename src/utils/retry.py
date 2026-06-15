"""
Retry utilities for handling flaky RPC calls.
"""

import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_async(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator to retry an async function with exponential backoff.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == retries - 1:
                        logger.error(
                            "Failed %s after %d attempts: %s", func.__name__, retries, e
                        )
                        raise

                    logger.warning(
                        "Attempt %d/%d for %s failed: %s. Retrying in %.2fs...",
                        attempt + 1,
                        retries,
                        func.__name__,
                        e,
                        current_delay,
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            return None

        return wrapper

    return decorator
