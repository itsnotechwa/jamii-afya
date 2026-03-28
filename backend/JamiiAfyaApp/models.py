from django.db import models
from django.conf import settings

from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField



#The AuditLog model is designed to create an immutable record of every write action (POST, PATCH, DELETE) performed by users in the application. 
#This is crucial for fraud prevention and dispute resolution, as it allows administrators to track user actions and identify any suspicious behavior. 
#The model includes fields for the user who performed the action, the type of action, the endpoint accessed, the payload of the request, the response code, the IP address of the user, and a timestamp of when the action occurred. 
#The records are never deleted to maintain a complete audit trail.
class AuditLog(models.Model):
    """
    Immutable record of every write action for fraud prevention & dispute resolution.
    Written by AuditLogMiddleware — never deleted.
    """
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, related_name='audit_logs')
    action      = models.CharField(max_length=10)   # POST / PATCH / DELETE
    endpoint    = models.CharField(max_length=255)
    payload     = models.JSONField(default=dict)
    response_code = models.PositiveSmallIntegerField()
    ip_address  = models.GenericIPAddressField(null=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        indexes  = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user} | {self.action} {self.endpoint} | {self.timestamp}"



# The Contribution model represents the periodic M-Pesa contributions made by members to a group pool.
# Each contribution is linked to a specific group and member, and includes details such as the amount.
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
    period     = models.CharField(max_length=7, help_text='YYYY-MM e.g. 2024-01')
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



# The EmergencyRequest model captures the details of emergency claims made by members, including the type of emergency, the amount requested, and the status of the claim.
# It also includes fields for the payout phone number, any rejection reasons, and references to M-Pesa transactions. 
# The model is designed to facilitate the management of emergency requests, approvals, and disbursements within the application.
class EmergencyRequest(models.Model):
    """A member raises an emergency; admins vote; M-Pesa B2C disburses."""

    # The Status and EmergencyType inner classes define the possible values for the status of an emergency request and the types of emergencies that can be claimed, respectively.
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
    
    # The Meta class defines the database table name and indexes for the EmergencyRequest model, optimizing queries based on group, status, and claimant.
    class Meta:
        db_table = 'emergency_requests'
        indexes  = [
            models.Index(fields=['group', 'status']),
            models.Index(fields=['claimant', 'status']),
        ]

    def __str__(self):
        return f"{self.claimant} | {self.emergency_type} | KES {self.amount_requested} [{self.status}]"

    @property
    def approval_count(self):
        return self.approvals.filter(decision='approve').count()

    @property
    def is_auto_approvable(self):
        return self.approval_count >= self.group.approval_threshold


# The EmergencyDocument model represents supporting documents for emergency requests, such as hospital receipts or discharge letters.
# Each document is linked to a specific emergency request and includes a file field for uploading the document, a label for the document, and a timestamp for when it was uploaded.
class EmergencyDocument(models.Model):
    """Supporting docs: hospital receipts, discharge letters, etc."""
    emergency = models.ForeignKey(EmergencyRequest, on_delete=models.CASCADE,
                                  related_name='documents')
    file      = models.FileField(upload_to='emergency_docs/%Y/%m/')
    label     = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # The Meta class defines the database table name for the EmergencyDocument model.
    class Meta:
        db_table = 'emergency_documents'


# The EmergencyApproval model captures the approval decisions made by administrators for emergency requests.
# Each approval record is linked to a specific emergency request and administrator, and includes the decision (
class EmergencyApproval(models.Model):
    """Immutable vote log — each admin votes once."""
   
    # The Decision inner class defines the possible values for the approval decision.
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



# The Group model represents a community group that members can join to contribute to a shared pool for emergencies.
# It includes fields for the group's name, description, creator, invite code, and rules for qualifying for payouts. 
# The model also tracks whether the group is active and when it was created.
class Group(models.Model):
    name        = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    on_delete=models.PROTECT,
                                    related_name='created_groups')
    invite_code = models.CharField(max_length=12, unique=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    # ── Payout rules ──────────────────────────────────────────────────────────
    min_contributions_to_qualify = models.PositiveIntegerField(default=3)
    max_payout_amount            = models.DecimalField(max_digits=10, decimal_places=2, default=50000)
    approval_threshold           = models.PositiveIntegerField(default=3,
        help_text="Number of admin approvals required to release funds")

    class Meta:
        db_table = 'groups'
        indexes  = [models.Index(fields=['invite_code'])]

    def __str__(self):
        return self.name



# The GroupMember model represents the membership of users in groups, including their role (admin or member) and status (active, suspended, left).
# Each membership record is linked to a specific group and user, and includes a timestamp for when the user joined the group. 
# The model ensures that a user can only have one membership per group and includes indexes for efficient querying based on group and status.
class GroupMember(models.Model):
    
    # The Role and Status inner classes define the possible values for a member's role within the group and their membership status, respectively.
    class Role(models.TextChoices):
        ADMIN  = 'admin',  'Admin'
        MEMBER = 'member', 'Member'

    # The Status inner class defines the possible values for a member's status within the group, such as active, suspended, or left. 
    # This allows for managing group memberships and enforcing rules based on the member's current status.
    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        SUSPENDED = 'suspended', 'Suspended'
        LEFT      = 'left',      'Left'

    group      = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='group_memberships')
    role       = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    joined_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'group_members'
        unique_together = ('group', 'user')
        indexes    = [models.Index(fields=['group', 'status'])]

    def __str__(self):
        return f"{self.user} in {self.group} ({self.role})"



# The Notification model represents notifications sent to users within the application, such as alerts for new emergency requests, votes cast, or payout statuses.
# Each notification includes the recipient, event type, channel (in-app or SMS), title, body, and a reference ID for linking to related records. 
# The model also tracks whether the notification has been read and when it was created, allowing for efficient management of user notifications and ensuring that important events are communicated effectively.
class Notification(models.Model):

    # Defines the possible channels through which notifications can be sent, such as in-app notifications or SMS messages.
    class Channel(models.TextChoices):
        IN_APP = 'in_app', 'In App'
        SMS    = 'sms',    'SMS'
        BOTH   = 'both',   'In App + SMS'
    
    # Defines the possible event types for notifications, such as when an emergency is raised, a vote is cast, a payout is successful or failed, or when contributions are due or confirmed.
    class EventType(models.TextChoices):
        EMERGENCY_RAISED   = 'emergency_raised',   'Emergency Raised'
        EMERGENCY_APPROVED      = 'emergency_approved',      'Emergency Approved'
        EMERGENCY_REJECTED      = 'emergency_rejected',      'Emergency Rejected'
        VOTE_CAST          = 'vote_cast',           'Vote Cast'
        PAYOUT_SUCCESS     = 'payout_success',      'Payout Successful'
        PAYOUT_FAILED      = 'payout_failed',       'Payout Failed'
        CONTRIBUTION_DUE   = 'contribution_due',    'Contribution Due'
        CONTRIBUTION_CONFIRMED = 'contribution_confirmed', 'Contribution Confirmed'

    recipient   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='notifications')
    event_type  = models.CharField(max_length=30, choices=EventType.choices)
    channel     = models.CharField(max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    title       = models.CharField(max_length=200)
    body        = models.TextField()
    is_read     = models.BooleanField(default=False)
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        indexes  = [models.Index(fields=['recipient', 'is_read'])]

    def __str__(self):
        return f"{self.recipient} | {self.event_type}"


# The SMSLog model is designed to create an immutable record of every outbound SMS sent via Africa's Talking, which is used for audit purposes, retry logic, and cost tracking.
# Each SMS log entry includes details such as the recipient's phone number, the message content, the status of the SMS (sent, failed, pending), the Africa's Talking message ID, cost, status code, the raw response from the API, and a timestamp for when the SMS was sent.
class SMSLog(models.Model):
    """
    Immutable record of every outbound SMS via Africa's Talking.
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
    at_message_id   = models.CharField(max_length=100, blank=True)
    at_cost         = models.CharField(max_length=20, blank=True)
    at_status_code  = models.CharField(max_length=10, blank=True)
    raw_response    = models.JSONField(default=dict)
    sent_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sms_logs'
        indexes  = [
            models.Index(fields=['recipient_phone', 'sent_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"SMS to {self.recipient_phone} [{self.status}] {self.sent_at:%Y-%m-%d %H:%M}"


# The User model extends Django's AbstractUser to use phone number as the primary login identifier, which is essential for integrating with M-Pesa for contributions and payouts.
# It includes additional fields such as national ID, verification status, profile picture, and timestamps for when the user was created and last updated.
class User(AbstractUser):
    
    #Extended user: phone is the primary login identifier for M-Pesa linkage.
    phone_number = PhoneNumberField(unique=True, region='KE')
    national_id  = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_verified  = models.BooleanField(default=False)
    profile_pic  = models.ImageField(upload_to='profiles/', null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = 'phone_number'
    REQUIRED_FIELDS = ['username', 'email']

    class Meta:
        db_table  = 'users'
        indexes   = [models.Index(fields=['phone_number']),
                     models.Index(fields=['national_id'])]

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"



# The MpesaTransaction model is designed to create an immutable log of every transaction made through the M-Pesa Daraja API, including both STK Push (C2B) and B2C payouts.
# Each transaction record includes details such as the user involved, transaction type, status, phone number, amount, M-Pesa receipt number, and references to related emergency requests or contributions.
# This model is crucial for maintaining a complete audit trail of all M-Pesa transactions, which is essential for financial reconciliation, fraud prevention, and dispute resolution. 
# The records are never deleted.
class MpesaTransaction(models.Model):
    #Immutable log of every Daraja API transaction for full auditability.

    # Defines the possible transaction types for M-Pesa transactions, including STK Push (C2B) and B2C payouts.
    class TxType(models.TextChoices):
        STK_PUSH  = 'stk_push',  'STK Push (C2B)'
        B2C       = 'b2c',       'B2C Payout'

    # Defines the possible statuses for M-Pesa transactions, such as initiated, success, failed, or timeout to allow for tracking the state of each transaction and handling them accordingly in the application.
    class TxStatus(models.TextChoices):
        INITIATED = 'initiated', 'Initiated'
        SUCCESS   = 'success',   'Success'
        FAILED    = 'failed',    'Failed'
        TIMEOUT   = 'timeout',   'Timeout'

    user              = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                          null=True, related_name='mpesa_transactions')
    tx_type           = models.CharField(max_length=10, choices=TxType.choices)
    status            = models.CharField(max_length=10, choices=TxStatus.choices,
                                         default=TxStatus.INITIATED)
    phone             = models.CharField(max_length=15)
    amount            = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_receipt     = models.CharField(max_length=50, blank=True, null=True, unique=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    result_code       = models.CharField(max_length=10, blank=True)
    result_desc       = models.TextField(blank=True)
    raw_callback      = models.JSONField(default=dict)  # full Safaricom payload
    reference_id      = models.PositiveIntegerField(null=True, blank=True,
        help_text='emergency_id or contribution_id depending on tx_type')
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mpesa_transactions'
        indexes  = [
            models.Index(fields=['mpesa_receipt']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['user', 'tx_type', 'status']),
        ]

    def __str__(self):
        return f"{self.tx_type} | {self.phone} | KES {self.amount} | {self.status}"
