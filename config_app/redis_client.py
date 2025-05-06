import redis
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_connection_pool = None


def get_redis_connection():
    """
    Get connection to Redis from connection pool. Works with both config dictionary and URL.
    """
    global _connection_pool
    
    if _connection_pool is None:
        try:
            redis_config = getattr(settings, 'CONSTANCE_REDIS_CONNECTION', None)
            
            if not redis_config:
                logger.error("CONSTANCE_REDIS_CONNECTION not defined")
                return None
            
            if isinstance(redis_config, dict):
                _connection_pool = redis.ConnectionPool(**redis_config)
            else:
                _connection_pool = redis.ConnectionPool.from_url(redis_config)
                
            logger.info("Created Redis connection pool")
        
        except Exception as e:
            logger.error(f"Failed to create Redis connection pool: {e}")
            return None
    
    try:
        return redis.Redis(connection_pool=_connection_pool)
    except Exception as e:
        logger.error(f"Failed to get Redis connection from pool: {e}")
        return None
