from django.db import models
from django.conf import settings


class Contribution(models.Model):
    """Monthly/periodic M-Pesa contributions to a group pool."""

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        FAILED    = 'failed',    'Failed'

    group      = models.ForeignKey('groups.Group', on_delete=models.PROTECT,
                                   related_name='contributions')
    member     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name='contributions')
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    mpesa_ref  = models.CharField(max_length=50, blank=True, null=True, unique=True)
    period     = models.CharField(
        max_length=10,
        help_text='YYYY-MM (monthly), YYYY-WNN (weekly e.g. 2024-W03), YYYY-MM-DD (daily)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table        = 'contributions'
        unique_together = ('group', 'member', 'period')  # one contribution per period
        indexes = [
            models.Index(fields=['group', 'status']),
            models.Index(fields=['member', 'period']),
            models.Index(fields=['mpesa_ref']),
        ]

    def __str__(self):
        return f"{self.member} → {self.group} KES {self.amount} [{self.period}]"
