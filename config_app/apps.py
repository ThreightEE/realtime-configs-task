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
            'makemigrations', 'migrate', 'collectstatic', 'check', 'shell', 'help',
            'createsuperuser', 'loaddata', 'dumpdata'
        ]
        command = sys.argv[1] if len(sys.argv) > 1 else None
        is_management_command = command in management_commands

        is_runserver_main_process = os.environ.get('RUN_MAIN') == 'true'

        if is_management_command:
            logger.info(f"PID {pid}: Skipping Pub/Sub setup for management command '{command}'")
            return

        if is_runserver_main_process:
            logger.info(f"PID {pid}: Skipping Pub/Sub setup for runserver reloader process")
            return
        
        # Check if already initialized
        if not hasattr(ConfigAppConfig, '_initialized_pids'):
            ConfigAppConfig._initialized_pids = {}
        
        if pid in ConfigAppConfig._initialized_pids:
            logger.info(f"PID {pid}: Worker already initialized")
            return

        try:
            from . import realtime_config
            from . import signals
            from constance.signals import config_updated

            realtime_config.load_defaults()
            logger.info(f"PID {pid}: Loaded constance config defaults")

            config_updated.connect(signals.config_updated_handler)
            logger.info(f"PID {pid}: Successfully connected 'config_updated' signal to 'config_updated_handler'")

            logger.info(f"PID {pid}: Starting Redis Pub/Sub subscriber")
            realtime_config.start_subscriber_thread()

            ConfigAppConfig._initialized_pids[pid] = True
            logger.info(f"PID {pid}: Initialization complete")

        except Exception as e:
            logger.error(f"PID {pid}: Error in ConfigAppConfig.ready(): {e}", exc_info=True)
