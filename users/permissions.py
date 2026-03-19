from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to admin users."""
    message = "Admin access required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsOwnerOrAdmin(BasePermission):
    """Object-level permission for owner or admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        # obj must have a user or owner field
        owner = getattr(obj, "user", getattr(obj, "owner", None))
        return owner == request.user


class IsTeacher(BasePermission):
    message = "Teacher access required."
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "teacher"
        )

class IsApprovedTeacher(BasePermission):
    message = "Your teacher account is pending admin approval."
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "teacher"
            and request.user.is_approved
        )

class IsStudent(BasePermission):
    message = "Student access required."
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "user"
        )