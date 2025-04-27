from rest_framework import permissions

class IsOrganization(permissions.BasePermission):
    """
    Allows access only to users with role = 'organization'.
    """

    message = 'Only organization users are allowed to perform this action.'

    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS) for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is authenticated and has role 'organization'
        return request.user.is_authenticated and request.user.role == 'organization'