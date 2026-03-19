from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class LastSeenMiddleware(MiddlewareMixin):
    """Update User.last_seen on every authenticated request (throttled per minute)."""

    def process_request(self, request):
        if not hasattr(request, "user"):
            return
        # Defer to after auth middleware resolves the user
        return None

    def process_response(self, request, response):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            now = timezone.now()
            last = user.last_seen
            # Only write to DB at most once per 60 seconds per user
            if last is None or (now - last).total_seconds() > 60:
                from django.contrib.auth import get_user_model
                get_user_model().objects.filter(pk=user.pk).update(last_seen=now)
        return response


class ActivityLogMiddleware(MiddlewareMixin):
    """
    Lightweight middleware – only logs HTTP 4xx/5xx errors to console.
    Detailed action logging is handled by service layer methods.
    """

    import logging
    _logger = logging.getLogger("django.request")

    def process_response(self, request, response):
        if response.status_code >= 400:
            user_id = getattr(getattr(request, "user", None), "id", None)
            self._logger.warning(
                "HTTP %s %s %s | user=%s",
                response.status_code,
                request.method,
                request.path,
                user_id,
            )
        return response
