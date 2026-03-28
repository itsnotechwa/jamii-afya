from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerUIView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerUIView.as_view(url_name='schema'), name='swagger-ui'),

    # App routes
    path('api/auth/',          include('apps.users.urls')),
    path('api/groups/',        include('apps.groups.urls')),
    path('api/contributions/', include('apps.contributions.urls')),
    path('api/emergencies/',   include('apps.emergencies.urls')),
    path('api/mpesa/',         include('apps.mpesa.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/audit/',         include('apps.audit.urls')),
]

