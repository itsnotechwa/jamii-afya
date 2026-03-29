from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Group, GroupMember
from .serializers import GroupSerializer, GroupMemberSerializer, JoinGroupSerializer
from utils.permissions import IsGroupAdmin


@extend_schema(tags=['Groups'])
class GroupViewSet(viewsets.ModelViewSet):
    serializer_class   = GroupSerializer
    permission_classes = [IsAuthenticated]
    queryset           = Group.objects.none()  # required for schema introspection

    def get_queryset(self):
        # Only groups the user belongs to
        return Group.objects.filter(
            memberships__user=self.request.user,
            memberships__status='active'
        ).select_related('created_by').distinct()

    @action(detail=False, methods=['post'])
    def join(self, request):
        """Join a group via invite code."""
        serializer = JoinGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data['invite_code']

        if GroupMember.objects.filter(group=group, user=request.user).exists():
            return Response({'detail': 'Already a member.'}, status=400)

        GroupMember.objects.create(group=group, user=request.user)
        return Response({'detail': f'Joined {group.name} successfully.'}, status=201)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List all members in a group."""
        group   = self.get_object()
        members = GroupMember.objects.filter(group=group).select_related('user')
        return Response(GroupMemberSerializer(members, many=True).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsGroupAdmin])
    def update_member(self, request, pk=None):
        """Update member role or status (admin only)."""
        group     = self.get_object()
        member_id = request.data.get('member_id')
        member    = get_object_or_404(GroupMember, id=member_id, group=group)
        serializer = GroupMemberSerializer(member, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
