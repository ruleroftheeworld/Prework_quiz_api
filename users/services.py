from django.contrib.auth import get_user_model
from django.db import transaction
from logs.services import LogService

User = get_user_model()


class UserService:
    @staticmethod
    @transaction.atomic
    def register_user(validated_data: dict) -> User:
        user = User.objects.create_user(**validated_data)
        LogService.log(
            action="user_registered",
            user=user,
            metadata={"email": user.email, "level": user.level, "stream": user.stream},
        )
        return user

    @staticmethod
    def get_all_users(filters: dict = None):
        qs = User.objects.all()
        if filters:
            if filters.get("role"):
                qs = qs.filter(role=filters["role"])
            if filters.get("is_active") is not None:
                qs = qs.filter(is_active=filters["is_active"])
        return qs.order_by("-date_joined")

    @staticmethod
    @transaction.atomic
    def admin_create_user(validated_data: dict, created_by) -> User:
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        LogService.log(
            action="admin_created_user",
            user=created_by,
            metadata={"target_user_id": user.id, "target_email": user.email},
        )
        return user

    @staticmethod
    @transaction.atomic
    def delete_user(user_id: int, deleted_by) -> None:
        user = User.objects.get(pk=user_id)
        email = user.email
        user.delete()
        LogService.log(
            action="admin_deleted_user",
            user=deleted_by,
            metadata={"deleted_user_id": user_id, "deleted_email": email},
        )

    @staticmethod
    def update_score(user: User, score: float) -> None:
        """Atomically update aggregate score."""
        User.objects.filter(pk=user.pk).update(
            total_score=user.total_score + score,
            quizzes_taken=user.quizzes_taken + 1,
        )
