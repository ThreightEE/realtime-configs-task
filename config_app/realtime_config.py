import threading
import logging
from typing import Any
from django.conf import settings
from constance import config
import redis
import time

from .redis_client import get_redis_connection

import os


logger = logging.getLogger(__name__)

_local_cache: dict[str, Any] = {}
_cache_lock = threading.Lock()
# Fill in AppConfig.ready() with load_defaults()
_default_values: dict[str, Any] = {}

_subscriber_thread = None
_subscriber_lock = threading.Lock()


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
            # Check all cache contents for current process for debug
            # logger.debug(f"PID: {os.getpid()}, cache: {_local_cache}")
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


def run_subscriber():
    logger.info("Redis Pub/Sub subscriber starting")
    channel_name = getattr(settings, 'REDIS_PUB_SUB_CHANNEL', None)
    if not channel_name:
        logger.error("REDIS_PUB_SUB_CHANNEL is not defined")
        return

    logger.info(f"Subscriber listens to Redis channel '{channel_name}'")

    while True:
        redis_client = None
        pubsub = None
        try:
            redis_client = get_redis_connection()
            if not redis_client:
                logger.warning("Subscriber failed to get Redis connection. Retrying in 5 seconds...")
                time.sleep(5)
                continue

            pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(channel_name)
            logger.info(f"Subscribed to Redis channel: {channel_name}. Waiting for messages...")

            for message in pubsub.listen():
                logger.debug(f"Subscriber received message: {message}")
                if message and message['type'] == 'message' and 'data' in message:
                    key = message['data']
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    logger.info(f"Received update notification for key: {key}")

                    with _cache_lock:
                        # Check all cache contents for current process for debug
                        # logger.debug(f"PID: {os.getpid()}, cache before invalidation: {_local_cache}")
                        removed_value = _local_cache.pop(key, None)

                    if removed_value is not None:
                        logger.info(f"Invalidated cache for key: {key}")
                    else:
                        logger.debug(f"Key {key} not found in cache, nothing to invalidate")
                else:
                     logger.warning(f"Received unexpected message format from Pub/Sub: {message}")

        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error in subscriber: {e}")
            time.sleep(5)

        except Exception as e:
            logger.error(f"Unexpected error in Redis subscriber: {e}", exc_info=True)
            time.sleep(10)

        finally:
            # Faster free redis resources
            if pubsub:
                try:
                    pubsub.unsubscribe()
                    pubsub.close()
                    logger.debug("PubSub unsubscribed and connection closed.")
                except Exception as close_e:
                    logger.warning(f"Error during pubsub cleanup: {close_e}")

def start_subscriber_thread():
    """
    Background thread for run_subscriber().
    """
    global _subscriber_thread
    global _subscriber_lock

    with _subscriber_lock:
        if _subscriber_thread is None or not _subscriber_thread.is_alive():
            _subscriber_thread = threading.Thread(
                target=run_subscriber,
                # Don't wait for the thread to finish
                daemon=True,
                name="RedisConfigSubscriber"
            )
            _subscriber_thread.start()
            logger.info(f"Started Redis Pub/Sub subscriber thread: {_subscriber_thread.name}")
        else:
            logger.info(f"Redis Pub/Sub subscriber thread '{_subscriber_thread.name}' is already running.")
