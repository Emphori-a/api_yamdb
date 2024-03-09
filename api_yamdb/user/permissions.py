from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsOwnerOrIsAdmin(permissions.IsAdminUser):

    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and (request.user.is_admin()
                     or request.user.is_superuser)
                )

    def has_object_permission(self, request, view, obj):
        return ((request.user.is_authenticated
                 and (request.user.is_admin()
                      or request.user.is_superuser))
                or obj.author == request.user)

