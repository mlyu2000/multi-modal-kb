#!/usr/bin/env python3
"""Retry logic for LLM API calls."""

import time
import random
from functools import wraps
from typing import Callable, Any, Optional
import logging


def retry(max_retries: int = 3, initial_delay: float = 1.0, max_delay: float = 30.0,
          backoff_multiplier: float = 2.0, retryable_exceptions: tuple = (Exception,),
          on_retry: Optional[Callable[[int, Exception], None]] = None):
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("trading_kb")
            
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt, e)
                        
                        logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                        
                        sleep_time = min(delay, max_delay)
                        jitter = sleep_time * 0.1 * random.random()
                        time.sleep(sleep_time + jitter)
                        
                        delay *= backoff_multiplier
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
                        
            raise last_exception
        return wrapper
    return decorator


def retry_gemma(func: Callable) -> Callable:
    """Retry decorator for Gemma API calls."""
    return retry(max_retries=3, initial_delay=2.0, max_delay=60.0, backoff_multiplier=2.0,
                 retryable_exceptions=(Exception,))(func)


def retry_qwen(func: Callable) -> Callable:
    """Retry decorator for Qwen API calls."""
    return retry(max_retries=3, initial_delay=2.0, max_delay=60.0, backoff_multiplier=2.0,
                 retryable_exceptions=(Exception,))(func)


def retry_embedding(func: Callable) -> Callable:
    """Retry decorator for embedding API calls."""
    return retry(max_retries=5, initial_delay=1.0, max_delay=30.0, backoff_multiplier=1.5,
                 retryable_exceptions=(Exception,))(func)
