from django.shortcuts import render

from django.conf import settings
from constance import config

def home(request):
    """
    Demo page to view current constance configs.
    """

    config_keys = settings.CONSTANCE_CONFIG.keys()

    # dict {key: current value}
    configs = {}
    for key in config_keys:
        try:
            configs[key] = getattr(config, key)
        except Exception as e:
            print(f"Could not get config for key '{key}'. Error: {e}")
            configs[key] = None

    context = {
        'site_name': config.SITE_NAME,
        'theme_color': config.THEME_COLOR,
        'welcome_message': config.WELCOME_MESSAGE,
        'maintenance_mode': config.MAINTENANCE_MODE,
        'items_per_page': config.ITEMS_PER_PAGE,
        'show_logs': config.SHOW_LOGS,
        'configs': configs,
    }

    return render(request, 'config_app/home.html', context)
