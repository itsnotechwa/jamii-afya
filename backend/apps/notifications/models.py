from django.db import models
from django.conf import settings


class Notification(models.Model):
    class Channel(models.TextChoices):
        IN_APP = 'in_app', 'In App'
        SMS    = 'sms',    'SMS'
        BOTH   = 'both',   'In App + SMS'

    class EventType(models.TextChoices):
        EMERGENCY_RAISED        = 'emergency_raised',        'Emergency Raised'
        EMERGENCY_APPROVED      = 'emergency_approved',      'Emergency Approved'
        EMERGENCY_REJECTED      = 'emergency_rejected',      'Emergency Rejected'
        VOTE_CAST               = 'vote_cast',               'Vote Cast'
        PAYOUT_SUCCESS          = 'payout_success',          'Payout Successful'
        PAYOUT_FAILED           = 'payout_failed',           'Payout Failed'
        CONTRIBUTION_DUE        = 'contribution_due',        'Contribution Due'
        CONTRIBUTION_CONFIRMED  = 'contribution_confirmed',  'Contribution Confirmed'

    recipient    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='notifications')
    event_type   = models.CharField(max_length=30, choices=EventType.choices)
    channel      = models.CharField(max_length=10, choices=Channel.choices, default=Channel.BOTH)
    title        = models.CharField(max_length=200)
    body         = models.TextField()
    is_read      = models.BooleanField(default=False)
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        indexes  = [models.Index(fields=['recipient', 'is_read'])]

    def __str__(self):
        return f"{self.recipient} | {self.event_type}"


class SMSLog(models.Model):
    """
    Immutable record of every outbound SMS via CommsGrid.
    Used for audit, retry logic, and cost tracking.
    """
    class Status(models.TextChoices):
        SENT    = 'sent',    'Sent'
        FAILED  = 'failed',  'Failed'
        PENDING = 'pending', 'Pending'

    notification    = models.OneToOneField(
        Notification, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sms_log'
    )
    recipient_phone = models.CharField(max_length=20)
    message         = models.TextField()
    status          = models.CharField(max_length=10, choices=Status.choices,
                                       default=Status.PENDING)
    provider_message_id = models.CharField(max_length=100, blank=True)
    provider_status     = models.CharField(max_length=50, blank=True)
    raw_response        = models.JSONField(default=dict)
    sent_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sms_logs'
        indexes  = [
            models.Index(fields=['recipient_phone', 'sent_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"SMS to {self.recipient_phone} [{self.status}] {self.sent_at:%Y-%m-%d %H:%M}"
