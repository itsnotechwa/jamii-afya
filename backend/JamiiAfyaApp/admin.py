from django.contrib import admin
from .models import *

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin



# Register the AuditLog model with the Django admin site, allowing administrators to view and search through audit logs while preventing any modifications to them.
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'action', 'endpoint', 'response_code', 'ip_address', 'timestamp']
    list_filter   = ['action', 'response_code']
    search_fields = ['user__phone_number', 'endpoint', 'ip_address']
    readonly_fields = ['user', 'action', 'endpoint', 'payload',
                        'response_code', 'ip_address', 'timestamp']

    def has_add_permission(self, request):
        return False   # Audit logs are system-generated only

    def has_delete_permission(self, request, obj=None):
        return False   # Never delete audit logs


# Register the Contribution model with the Django admin site, allowing administrators to manage contributions while ensuring that certain fields are read-only to maintain data integrity.
@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display  = ['member', 'group', 'amount', 'period', 'status', 'mpesa_ref', 'created_at']
    list_filter   = ['status', 'group', 'period']
    search_fields = ['member__phone_number', 'mpesa_ref']
    readonly_fields = ['mpesa_ref', 'confirmed_at', 'created_at']


class EmergencyDocumentInline(admin.TabularInline):
    model   = EmergencyDocument
    extra   = 0
    fields  = ['label', 'file', 'uploaded_at']
    readonly_fields = ['uploaded_at']


class EmergencyApprovalInline(admin.TabularInline):
    model   = EmergencyApproval
    extra   = 0
    fields  = ['admin', 'decision', 'note', 'voted_at']
    readonly_fields = ['voted_at']

# Register the EmergencyRequest model with the Django admin site, allowing administrators to manage emergency requests while providing inlines for related documents and approvals to facilitate comprehensive oversight of each request.
@admin.register(EmergencyRequest)
class EmergencyRequestAdmin(admin.ModelAdmin):
    list_display  = ['claimant', 'group', 'emergency_type', 'amount_requested',
                     'amount_approved', 'status', 'created_at']
    list_filter   = ['status', 'emergency_type', 'group']
    search_fields = ['claimant__phone_number', 'claimant__first_name', 'mpesa_ref']
    readonly_fields = ['mpesa_ref', 'created_at', 'resolved_at']
    inlines       = [EmergencyDocumentInline, EmergencyApprovalInline]

# Register the EmergencyApproval model with the Django admin site, allowing administrators to view and manage emergency approvals while ensuring that certain fields are read-only to maintain the integrity of approval records.
@admin.register(EmergencyApproval)
class EmergencyApprovalAdmin(admin.ModelAdmin):
    list_display  = ['emergency', 'admin', 'decision', 'voted_at']
    list_filter   = ['decision']
    readonly_fields = ['voted_at']

# The GroupMemberInline class defines an inline admin interface for managing group members within the GroupAdmin, allowing administrators to easily view and edit group memberships directly from the group detail page while ensuring that the joined_at timestamp is read-only.
class GroupMemberInline(admin.TabularInline):
    model  = GroupMember
    extra  = 0
    fields = ['user', 'role', 'status', 'joined_at']
    readonly_fields = ['joined_at']

# Register the Group model with the Django admin site, allowing administrators to manage groups while providing an inline interface for managing group members and ensuring that certain fields are read-only to maintain data integrity.
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ['name', 'created_by', 'is_active', 'min_contributions_to_qualify',
                     'max_payout_amount', 'approval_threshold', 'invite_code', 'created_at']
    search_fields = ['name', 'invite_code']
    list_filter   = ['is_active']
    inlines       = [GroupMemberInline]
    readonly_fields = ['invite_code']

# Register the GroupMember model with the Django admin site, allowing administrators to manage group memberships while ensuring that certain fields are read-only to maintain the integrity of group membership records.
@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display  = ['user', 'group', 'role', 'status', 'joined_at']
    list_filter   = ['role', 'status']
    search_fields = ['user__phone_number', 'group__name']

# Register the Notification model with the Django admin site, allowing administrators to manage notifications while ensuring that certain fields are read-only to maintain the integrity of notification records.
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['recipient', 'event_type', 'title', 'is_read', 'created_at']
    list_filter   = ['event_type', 'is_read', 'channel']
    search_fields = ['recipient__phone_number', 'title']
    readonly_fields = ['created_at']

# Register the SMSLog model with the Django admin site, allowing administrators to view and manage SMS logs while ensuring that certain fields are read-only to maintain the integrity of SMS log records and preventing any modifications or deletions to them.
@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display   = ['recipient_phone', 'status', 'at_message_id',
                      'at_cost', 'at_status_code', 'sent_at']
    list_filter    = ['status']
    search_fields  = ['recipient_phone', 'at_message_id']
    readonly_fields = ['notification', 'recipient_phone', 'message', 'status',
                       'at_message_id', 'at_cost', 'at_status_code',
                       'raw_response', 'sent_at']

    def has_add_permission(self, request):
        return False  # SMS logs are system-generated

    def has_delete_permission(self, request, obj=None):
        return False  # Never delete SMS logs


# Register the custom User model with the Django admin site, allowing administrators to manage user accounts while providing a customized interface that includes additional fields specific to the application's user model.
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['phone_number', 'first_name', 'last_name', 'national_id', 'is_verified', 'is_staff']
    search_fields = ['phone_number', 'first_name', 'last_name', 'national_id']
    list_filter   = ['is_verified', 'is_staff', 'is_active']
    fieldsets     = BaseUserAdmin.fieldsets + (
        ('JamiiFund', {'fields': ('phone_number', 'national_id', 'is_verified', 'profile_pic')}),
    )

# Register the MpesaTransaction model with the Django admin site, allowing administrators to manage M-Pesa transactions while ensuring that certain fields are read-only to maintain the integrity of transaction records.
@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display   = ['user', 'tx_type', 'phone', 'amount', 'status',
                      'mpesa_receipt', 'created_at']
    list_filter    = ['tx_type', 'status']
    search_fields  = ['phone', 'mpesa_receipt', 'checkout_request_id']
    readonly_fields = ['raw_callback', 'created_at', 'updated_at']
