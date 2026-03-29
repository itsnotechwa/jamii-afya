from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.serializers import ModelSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .models import AuditLog


class AuditLogSerializer(ModelSerializer):
    class Meta:
        model  = AuditLog
        fields = ['id', 'user', 'action', 'endpoint', 'response_code',
                  'ip_address', 'timestamp']


@extend_schema(tags=['Audit'])
class AuditLogViewSet(ReadOnlyModelViewSet):
    """Superadmin-only: full audit trail for compliance."""
    serializer_class   = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields   = ['user', 'action', 'endpoint']
    ordering_fields    = ['timestamp']

    def get_queryset(self):
        return AuditLog.objects.select_related('user').order_by('-timestamp')


router = DefaultRouter()
router.register(r'', AuditLogViewSet, basename='audit')
urlpatterns = [path('', include(router.urls))]
