from rest_framework import permissions

class IsOrganization(permissions.BasePermission):
    """
    Allows access only to users with role = 'organization'.
    """

    message = 'Only approved organization users are allowed to perform this action.'

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            self.message = 'Authentication credentials were not provided.'
            return False

        if user.role != 'organization':
            self.message = 'Only organization users are allowed to perform this action.'
            return False

        try:
            org_profile = user._organization_profile 
            if org_profile.verification_status != 'approved':
                self.message = 'Your organization profile is not approved yet.'
                return False
        except Exception:
            self.message = 'Organization profile not found.'
            return False

        return True