from rest_framework.permissions import BasePermission
from apps.groups.models import GroupMember


class IsGroupAdmin(BasePermission):
    """
    Allows access only to group admins.
    Expects the view to have a group object or group_id in kwargs/query_params.
    """
    message = 'Only group admins can perform this action.'

    def has_object_permission(self, request, view, obj):
        # obj can be a Group or any model with a .group FK
        group = getattr(obj, 'group', obj)
        return GroupMember.objects.filter(
            group=group,
            user=request.user,
            role='admin',
            status='active'
        ).exists()
