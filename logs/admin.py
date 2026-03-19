from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ["action", "user", "timestamp", "ip_address"]
    list_filter = ["action"]
    search_fields = ["user__email", "action"]
    readonly_fields = ["user", "action", "timestamp", "metadata", "ip_address"]

    def has_add_permission(self, request):
        return False  # Logs are immutable

    def has_change_permission(self, request, obj=None):
        return False
