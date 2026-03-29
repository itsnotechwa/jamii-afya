from django.contrib import admin
from .models import EmergencyRequest, EmergencyDocument, EmergencyApproval

admin.site.register(EmergencyRequest)
admin.site.register(EmergencyDocument)
admin.site.register(EmergencyApproval)
