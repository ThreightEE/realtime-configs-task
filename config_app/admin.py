from django.contrib import admin

from .models import ConfigChangeLog

@admin.register(ConfigChangeLog)
class ConfigChangeLogAdmin(admin.ModelAdmin):
    list_display = ('key', 'old_value', 'new_value', 'changed_at')
    list_filter = ('key', 'changed_at')
    search_fields = ('key', 'new_value')
    readonly_fields = ('key', 'old_value', 'new_value', 'changed_at')
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
