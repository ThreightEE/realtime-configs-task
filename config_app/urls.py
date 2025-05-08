from django.urls import path
from . import views

app_name = 'config_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/configs/', views.get_all_configs_api, name='get_all_configs_api'),
    path('api/logs/', views.get_change_logs_api, name='get_change_logs_api'),
]
