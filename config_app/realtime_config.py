import threading
import logging
from typing import Any
from django.conf import settings
from constance import config
import redis
import time


logger = logging.getLogger(__name__)

_local_cache: dict[str, Any] = {}
_cache_lock = threading.Lock()

# Fill in AppConfig.ready() with load_defaults()
_default_values: dict[str, Any] = {}


def load_defaults() -> None:
    global _default_values
    defaults = {}
    try:
        constance_defs = getattr(settings, 'CONSTANCE_CONFIG', {})
        defaults = {key: definition[0] for key, definition in constance_defs.items()}
        logger.info("Successfully loaded default config values")
    except Exception as e:
        logger.error("Failed to load default config values from settings")
    _default_values = defaults

def get_config(key: str, default: Any = None) -> Any:
    """
    Get config value by key with caching.

    - Return local cache if there is any
    - Try to get config from Redis:
     - Save and return on success
     - Return default if given, or default from constance_config
    """

    with _cache_lock:
        if key in _local_cache:
            logger.debug(f"Config {key} retrieved from local cache - {_local_cache[key]}")
            return _local_cache[key]

    logger.debug(f"Cache miss for config '{key}'")

    try:
        value = getattr(config, key)
        with _cache_lock:
            _local_cache[key] = value
        logger.debug(f"Fetched config '{key}' from Redis and cached - {value}")
        return value

    except (redis.exceptions.RedisError, AttributeError) as e:
        if isinstance(e, redis.exceptions.RedisError):
            logger.warning(f"Redis operation failed for config '{key}'. Error: {e}")
        else:
            logger.error(f"Config '{key}' not found in Constance")

    except Exception as e:
        logger.error(f"Unexpected error getting config '{key}'")
        
    logger.warning(f"Fallback for config '{key}'")
    if default is not None:
        logger.warning(f"Returning passed default {default}")
        return default
    
    preloaded_default = _default_values.get(key)
    logger.warning(f"Returning preloaded default {preloaded_default}")
    return preloaded_default
