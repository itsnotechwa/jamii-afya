from django.db import models
from django.conf import settings


class EmergencyRequest(models.Model):
    """A member raises an emergency; admins vote; M-Pesa B2C disburses."""

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending Review'
        APPROVED  = 'approved',  'Approved'
        REJECTED  = 'rejected',  'Rejected'
        PAID      = 'paid',      'Paid Out'
        FAILED    = 'failed',    'Payout Failed'

    class EmergencyType(models.TextChoices):
        HOSPITALIZATION = 'hospitalization', 'Hospitalization'
        SURGERY         = 'surgery',         'Surgery'
        MEDICATION      = 'medication',      'Medication'
        MATERNITY       = 'maternity',       'Maternity'
        OTHER           = 'other',           'Other Medical'

    group            = models.ForeignKey('groups.Group', on_delete=models.PROTECT,
                                         related_name='emergencies')
    claimant         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                         related_name='emergency_requests')
    emergency_type   = models.CharField(max_length=20, choices=EmergencyType.choices)
    description      = models.TextField()
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    amount_approved  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status           = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    payout_phone     = models.CharField(max_length=15, help_text='Phone to disburse to (Safaricom)')
    rejection_reason = models.TextField(blank=True)
    mpesa_ref        = models.CharField(max_length=50, blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    resolved_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'emergency_requests'
        indexes  = [
            models.Index(fields=['group', 'status']),
            models.Index(fields=['claimant', 'status']),
        ]

    def __str__(self):
        return f"{self.claimant} | {self.emergency_type} | KES {self.amount_requested} [{self.status}]"

    def approve_vote_count(self):
        """DB count of approve votes (use serializer/API approval_count when SQL-annotated)."""
        return self.approvals.filter(decision='approve').count()

    @property
    def is_auto_approvable(self):
        return self.approve_vote_count() >= self.group.approval_threshold


class EmergencyDocument(models.Model):
    """Supporting docs: hospital receipts, discharge letters, etc."""
    emergency = models.ForeignKey(EmergencyRequest, on_delete=models.CASCADE,
                                  related_name='documents')
    file      = models.FileField(upload_to='emergency_docs/%Y/%m/')
    label     = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emergency_documents'


class EmergencyApproval(models.Model):
    """Immutable vote log — each admin votes once."""

    class Decision(models.TextChoices):
        APPROVE = 'approve', 'Approve'
        REJECT  = 'reject',  'Reject'

    emergency = models.ForeignKey(EmergencyRequest, on_delete=models.PROTECT,
                                  related_name='approvals')
    admin     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decision  = models.CharField(max_length=10, choices=Decision.choices)
    note      = models.TextField(blank=True)
    voted_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'emergency_approvals'
        unique_together = ('emergency', 'admin')  # one vote per admin

class Hospital(models.Model):
    name     = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    paybill  = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'hospitals'

    def __str__(self):
        return self.name