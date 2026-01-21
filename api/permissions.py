from rest_framework import permissions


class IsOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            role = request.user.userprofile.role
            return role in ['operator', 'finance_admin']
        except:
            return False


class IsFinanceAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            return request.user.userprofile.role == 'finance_admin'
        except:
            return False
