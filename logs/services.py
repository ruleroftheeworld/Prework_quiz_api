import logging

logger = logging.getLogger(__name__)


class LogService:
    @staticmethod
    def log(action: str, user=None, metadata: dict = None, ip_address: str = None) -> None:
        """
        Write an ActivityLog entry.
        Runs synchronously — swap the body for .delay() if you add Celery.
        """
        from .models import ActivityLog

        try:
            ActivityLog.objects.create(
                user=user,
                action=action,
                metadata=metadata or {},
                ip_address=ip_address,
            )
        except Exception as exc:
            # Never let logging crash the main flow
            logger.error("Failed to write ActivityLog: %s", exc)
