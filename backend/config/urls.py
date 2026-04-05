from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.emergencies.views import HospitalListView
from config.upload_views import PresignedUploadUnavailableView

urlpatterns = [
    path('', RedirectView.as_view(url='/api/docs/', permanent=False)),
    path('admin/', admin.site.urls),

    # API Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-view'),
    path('api/redoc/',  SpectacularRedocView.as_view(url_name='schema'),  name='redoc-view'),

    # App routes
    path('api/auth/', include('apps.users.urls')),
    path('api/groups/', include('apps.groups.urls')),
    path('api/contributions/', include('apps.contributions.urls')),
    path('api/emergencies/',  include('apps.emergencies.urls')),
    path('api/hospitals/', HospitalListView.as_view(), name='hospital-list'),
    path('api/upload/', PresignedUploadUnavailableView.as_view(), name='upload-presign'),
    path('api/mpesa/', include('apps.mpesa.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/audit/', include('apps.audit.urls')),
]

