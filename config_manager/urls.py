"""
URL configuration for config_manager project.
"""

from django.contrib import admin
from django.urls import path, include

from typing import List

urlpatterns: List[path] = [
    path('admin/', admin.site.urls),
    path('', include('config_app.urls')),
]
