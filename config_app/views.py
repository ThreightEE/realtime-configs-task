from django.shortcuts import render

from django.conf import settings

from . import realtime_config
from django.http import HttpRequest, HttpResponse, JsonResponse
from typing import Any

from .models import ConfigChangeLog


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
    API endpoint that returns current config values as JSON.
    """
    keys = settings.CONSTANCE_CONFIG.keys()
    configs = {key: realtime_config.get_config(key) for key in keys}
    return JsonResponse(configs)

def get_change_logs_api(request: HttpRequest) -> HttpResponse:
    """
    API endpoint that returns recent LOGS_COUNT config change logs.
    """
    max_logs_str = realtime_config.get_config('LOGS_COUNT', default='10')
    max_logs = int(max_logs_str)
    if max_logs <= 0:
        max_logs = 10

    logs = ConfigChangeLog.objects.all()[:max_logs]

    data = [{
        'id': log.id,
        'key': log.key,
        'old_value': log.old_value,
        'new_value': log.new_value,
        'changed_at': log.changed_at.strftime('%Y-%m-%d %H:%M:%S')
    } for log in logs]

    return JsonResponse({'logs': data})
