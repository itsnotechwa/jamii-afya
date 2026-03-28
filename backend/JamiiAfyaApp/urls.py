from django.contrib import admin
from django.urls import path,include

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import *

router = DefaultRouter()
router.register(r'', AuditLogViewSet, basename='audit')
router.register(r'', EmergencyRequestViewSet, basename='emergency')
router.register(r'', GroupViewSet, basename='groups')
router.register(r'', GroupMemberViewSet, basename='group-members')
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include(router.urls)), 

    path('register/', RegisterView.as_view(), name='register'),

    path('login/', LoginView.as_view(), name='login'),

    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path('profile/', ProfileView.as_view(), name='profile'),

    path('callback/', STKCallbackView.as_view(), name='mpesa-stk-callback'),

    path('b2c/result/', B2CResultView.as_view(), name='mpesa-b2c-result'),
    
    path('b2c/timeout/', B2CTimeoutView.as_view(), name='mpesa-b2c-timeout'),
]
