from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.serializers import ModelSerializer
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .models import Notification


class NotificationSerializer(ModelSerializer):
    class Meta:
        model  = Notification
        fields = ['id', 'event_type', 'title', 'body', 'is_read', 'reference_id', 'created_at']


@extend_schema(tags=['Notifications'])
class NotificationViewSet(ReadOnlyModelViewSet):
    serializer_class   = NotificationSerializer
    permission_classes = [IsAuthenticated]
    queryset           = Notification.objects.none()  # required for schema introspection

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'detail': 'All notifications marked as read.'})

    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notif).data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread': count})


router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
urlpatterns = [path('', include(router.urls))]
