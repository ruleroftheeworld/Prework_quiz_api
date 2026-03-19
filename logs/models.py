from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    """Immutable audit log for all user and admin actions."""

    ACTION_CHOICES = [
        # User actions
        ("user_registered", "User Registered"),
        ("user_login", "User Login"),
        ("quiz_created", "Quiz Created"),
        ("quiz_started", "Quiz Started"),
        ("answer_submitted", "Answer Submitted"),
        ("quiz_completed", "Quiz Completed"),
        ("attempt_invalidated", "Attempt Invalidated"),
        # Admin actions
        ("admin_created_user", "Admin Created User"),
        ("admin_deleted_user", "Admin Deleted User"),
        ("admin_deleted_quiz", "Admin Deleted Quiz"),
        #Teacher actions
        ("teacher_approved",    "Teacher Approved"), 
        ("test_created",        "Test Created"),
        ("test_assigned",       "Test Assigned"),
        ("test_started",        "Test Started"),
        ("test_submitted",      "Test Submitted"),
        ("answers_released",    "Answers Released"),
        ("test_deleted",        "Test Deleted"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "activity_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp}] {self.action} by {self.user_id}"
