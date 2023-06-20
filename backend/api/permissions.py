from rest_framework.permissions import SAFE_METHODS, BasePermission


class AdminOrAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user == obj.author or request.user.is_superuser)


class AdminAndUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user and request.user.is_superuser)
