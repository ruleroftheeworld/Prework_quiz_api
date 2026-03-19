from rest_framework import serializers
from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)

    class Meta:
        model = ActivityLog
        fields = ["id", "user_email", "action", "timestamp", "metadata", "ip_address"]
