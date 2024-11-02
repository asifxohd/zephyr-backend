from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Custom permission to only allow users with 'admin' role.
    """

    def has_permission(self, request, view):
        return request.user  and request.user.role == 'admin'


class IsInvestor(BasePermission):
    """
    Custom permission to only allow users with 'investor' role.
    """

    def has_permission(self, request, view):
        return request.user and request.user.status and request.user.role == 'investor'


class IsBusiness(BasePermission):
    """
    Custom permission to only allow users with 'business' role.
    """

    def has_permission(self, request, view):
        return request.user and request.user.status and request.user.role == 'business'




