from django.apps import AppConfig

import sys
import logging
import os

logger = logging.getLogger(__name__)


class ConfigAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config_app'

    def ready(self):
        pid = os.getpid()
        logger.info(f"ConfigAppConfig.ready() CALLED in PID: {pid}")

        # Don't call on basic manage.py commands
        management_commands = [
            'makemigrations', 'migrate', 'collectstatic', 'check', 'shell', 'help'
        ]
        is_management_command = any(cmd in sys.argv for cmd in management_commands)
        is_runserver_main_process = os.environ.get('RUN_MAIN') == 'true'

        if is_management_command or not is_runserver_main_process:
            logger.info(f"PID {pid}: Skipping Pub/Sub setup for main/management process")
            return

        logger.info(f"PID {pid}: Pub/Sub setup")
        try:
            from . import realtime_config
            from . import signals
            from constance.signals import config_updated

            realtime_config.load_defaults()
            logger.info("Loaded constance config defaults")

            config_updated.connect(signals.config_updated_handler)
            logger.info("Successfully connected 'config_updated' signal to 'config_updated_handler'")

            logger.info("Starting Redis Pub/Sub subscriber")
            realtime_config.start_subscriber_thread()

        except Exception as e:
            logger.error(f"Error during ConfigAppConfig.ready() initialization: {e}", exc_info=True)
