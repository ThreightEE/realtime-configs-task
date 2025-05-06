from django.apps import AppConfig

import sys
import logging

logger = logging.getLogger(__name__)


class ConfigAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config_app'

    def ready(self):
        # Don't call on basic manage.py commands
        management_commands = [
            'makemigrations', 'migrate', 'collectstatic', 'check', 'shell', 'help'
        ]
        is_management_command = any(cmd in sys.argv for cmd in management_commands)
        is_not_server_process = is_management_command or 'manage.py' in sys.argv[0]
        logger.info(f"ConfigAppConfig.ready(): is_management_command={is_management_command}, is_not_server_process={is_not_server_process}")

        from . import realtime_config
        realtime_config.load_defaults()
        logger.info("Loaded constance config defaults")

        try:
            from constance.signals import config_updated
            from . import signals
            config_updated.connect(signals.config_updated_handler)
            logger.info("Successfully connected 'config_updated' signal to 'config_updated_handler'.")
        except Exception as e:
             logger.error(f"Failed to connect constance signal: {e}", exc_info=True)


        # ! ! ! TO DO: Pub/Sub
        if not is_not_server_process:
             logger.info("[Pub/Sub listener to be implemented]")
