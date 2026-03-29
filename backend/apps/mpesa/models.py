from django.db import models
from django.conf import settings


class MpesaTransaction(models.Model):
    """Immutable log of every Daraja API transaction for full auditability."""

    class TxType(models.TextChoices):
        STK_PUSH  = 'stk_push',  'STK Push (C2B)'
        B2C       = 'b2c',       'B2C Payout'

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
    mpesa_transaction_id = models.CharField(
        max_length=50, blank=True, null=True,
        help_text='Safaricom TransactionID returned in callback metadata (distinct from receipt number)',
    )
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
