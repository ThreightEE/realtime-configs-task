from django.shortcuts import render

from django.conf import settings

from . import realtime_config
from django.http import HttpRequest, HttpResponse, JsonResponse
from typing import Any


def home(request: HttpRequest) -> HttpResponse:
    """
    Demo page to view current constance configs.
    """

    config_keys = settings.CONSTANCE_CONFIG.keys()

    configs: dict[str, Any] = {key: realtime_config.get_config(key) for key in config_keys}

    context: dict[str, Any] = {
        'site_name': configs.get('SITE_NAME'),
        'theme_color': configs.get('THEME_COLOR'),
        'welcome_message': configs.get('WELCOME_MESSAGE'),
        'maintenance_mode': configs.get('MAINTENANCE_MODE'),
        'items_per_page': configs.get('ITEMS_PER_PAGE') or 10,
        'show_logs': configs.get('SHOW_LOGS'),
        'polling_s': configs.get('UI_POLLING_INTERVAL') or 300,
        'configs': configs,
    }

    return render(request, 'config_app/home.html', context)


def get_all_configs_api(request: HttpRequest) -> HttpResponse:
    """
    API endpoint that returns current config values as JSON
    """
    keys = settings.CONSTANCE_CONFIG.keys()
    configs = {key: realtime_config.get_config(key) for key in keys}
    return JsonResponse(configs)
