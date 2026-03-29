from django.contrib import admin
from .models import Notification, SMSLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display   = ['recipient', 'event_type', 'channel', 'title', 'is_read', 'created_at']
    list_filter    = ['event_type', 'is_read', 'channel']
    search_fields  = ['recipient__phone_number', 'title']
    readonly_fields = ['created_at']


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display   = ['recipient_phone', 'status', 'provider_message_id',
                      'provider_status', 'sent_at']
    list_filter    = ['status']
    search_fields  = ['recipient_phone', 'provider_message_id']
    readonly_fields = ['notification', 'recipient_phone', 'message', 'status',
                       'provider_message_id', 'provider_status',
                       'raw_response', 'sent_at']

    def has_add_permission(self, request):
        return False  # SMS logs are system-generated

    def has_delete_permission(self, request, obj=None):
        return False  # Never delete SMS logs
