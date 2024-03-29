from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import User


class IsAuthorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            return request.method in SAFE_METHODS or request.user == obj
        return request.method in SAFE_METHODS or request.user == obj.author


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or request.user.is_superuser
