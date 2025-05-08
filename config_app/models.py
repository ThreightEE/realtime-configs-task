from django.db import models

class ConfigChangeLog(models.Model):
    key = models.CharField(
        max_length=100
    )
    
    old_value = models.TextField(
        null=True,
        blank=True
    )
    new_value = models.TextField()

    changed_at = models.DateTimeField(
        auto_now_add=True
    )
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Config Change Log'
        verbose_name_plural = 'Config Change Logs'

    def __str__(self):
        return f"Change '{self.key}' at {self.changed_at.strftime('%Y-%m-%d %H:%M')}"
