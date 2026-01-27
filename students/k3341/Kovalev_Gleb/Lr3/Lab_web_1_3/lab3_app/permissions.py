from rest_framework.permissions import BasePermission


def _role(request, role: str) -> bool:
    return bool(
        request.user
        and request.user.is_authenticated
        and hasattr(request.user, "profile")
        and request.user.profile.role == role
    )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return _role(request, "admin")


class IsCleaner(BasePermission):
    def has_permission(self, request, view):
        return _role(request, "cleaner")


class IsClient(BasePermission):
    def has_permission(self, request, view):
        return _role(request, "client")