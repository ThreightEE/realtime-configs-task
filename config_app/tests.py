from django.test import TestCase, override_settings
from django.conf import settings

from unittest.mock import patch
import redis
import time

from . import realtime_config
from constance.backends.redisd import RedisBackend


def reset_set_up():
    """
    Clear module on app start.
    """
    realtime_config._local_cache.clear()
    realtime_config._default_values.clear()
    realtime_config._redis_available = True
    realtime_config._last_redis_error_time = 0.0
        

@override_settings(
    REDIS_RETRY_INTERVAL=0.01
)
class RealTimeConfigTests(TestCase):

    def setUp(self):
        reset_set_up()
        realtime_config.load_defaults()


    @patch.object(RedisBackend, 'get')
    def test_cache(self, mock_constance_backend_get):
        """
        Get value from constance Redis, cache -> get it again from local cache.
        """
        mock_constance_backend_get.return_value = b'"Test Value"'
        expected_value = b'"Test Value"'

        self.assertEqual(realtime_config.get_config('SITE_NAME'), expected_value)
        mock_constance_backend_get.assert_called_once_with('SITE_NAME')

        self.assertIn('SITE_NAME', realtime_config._local_cache)
        self.assertEqual(realtime_config._local_cache['SITE_NAME'], expected_value)
        
        mock_constance_backend_get.reset_mock()

        self.assertEqual(realtime_config.get_config('SITE_NAME'), expected_value)
        mock_constance_backend_get.assert_not_called()


    @patch.object(RedisBackend, 'get',
                  side_effect=redis.exceptions.ConnectionError("Redis is down"))
    def test_fallback_to_settings_default(self, mock_constance_backend_get_error):
        """
        Redis unavailable, cache empty, no default -> fallback to settings default.
        Test fail fast mechanism.
        """
        expected_value = realtime_config._default_values.get('WELCOME_MESSAGE')
        self.assertIsNotNone(expected_value, 
                             f"Default for 'WELCOME_MESSAGE' not in _default_values")

        value = realtime_config.get_config('WELCOME_MESSAGE')
        self.assertEqual(value, expected_value)
        mock_constance_backend_get_error.assert_called_once_with('WELCOME_MESSAGE')
        self.assertFalse(realtime_config._redis_available,
                         "Redis should be marked as unavailable")

        mock_constance_backend_get_error.reset_mock()
        self.assertEqual(realtime_config.get_config('WELCOME_MESSAGE'),
                         expected_value)
        mock_constance_backend_get_error.assert_not_called()

        retry_interval = settings.REDIS_RETRY_INTERVAL
        time.sleep(retry_interval + 0.01)

        self.assertEqual(realtime_config.get_config('WELCOME_MESSAGE'),
                         expected_value)
        mock_constance_backend_get_error.assert_called_once_with('WELCOME_MESSAGE')
        
    
    @patch.object(RedisBackend, 'get',
                  side_effect=redis.exceptions.ConnectionError("Redis is down"))
    def test_fallback_to_argument_default(self, mock_constance_backend_get_error_arg):
        """
        Redis unavailable, cache empty -> fallback to arg default.
        """
        expected_value = "Argument Default"
        value = realtime_config.get_config('SITE_NAME', default=expected_value)
        self.assertEqual(value, expected_value)
        mock_constance_backend_get_error_arg.assert_called_once_with('SITE_NAME')
        self.assertFalse(realtime_config._redis_available)
