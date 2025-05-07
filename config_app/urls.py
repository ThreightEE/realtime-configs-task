from django.urls import path
from . import views

app_name = 'config_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/configs/', views.get_all_configs_api, name='get_all_configs_api')
]
