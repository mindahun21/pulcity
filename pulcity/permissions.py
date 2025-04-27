from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admin users to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user == obj.user:
            return True
        if request.user.is_staff:  
            return True
        return False
