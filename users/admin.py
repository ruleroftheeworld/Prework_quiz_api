from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "role", "level", "stream", "is_active", "date_joined"]
    list_filter = ["role", "level", "stream", "is_active"]
    search_fields = ["email", "username", "full_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("username", "full_name")}),
        ("Profile", {"fields": ("role", "level", "stream")}),
        ("Stats", {"fields": ("total_score", "quizzes_taken")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("date_joined", "last_seen")}),
    )
    readonly_fields = ["date_joined", "last_seen", "total_score", "quizzes_taken"]

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "role", "level", "stream"),
        }),
    )
