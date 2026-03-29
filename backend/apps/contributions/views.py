from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer
import rest_framework.fields as f
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404
from .models import Contribution
from apps.groups.models import Group


class ContributionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    group_name  = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model  = Contribution
        fields = ['id', 'group', 'group_name', 'member', 'member_name',
                  'amount', 'status', 'mpesa_ref', 'period', 'created_at', 'confirmed_at']
        read_only_fields = ['status', 'mpesa_ref', 'confirmed_at']


class InitiateContributionSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    amount   = serializers.DecimalField(max_digits=10, decimal_places=2)
    period   = serializers.CharField(max_length=10)  # YYYY-MM / YYYY-WNN / YYYY-MM-DD


@extend_schema(tags=['Contributions'])
class ContributionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = ContributionSerializer
    permission_classes = [IsAuthenticated]
    queryset           = Contribution.objects.none()  # required for schema introspection

    def get_queryset(self):
        return Contribution.objects.filter(
            group__memberships__user=self.request.user,
            group__memberships__status='active'
        ).select_related('member', 'group').distinct()

    @extend_schema(
        tags=['Contributions'],
        request=inline_serializer('InitiateContributionRequest', fields={
            'group_id': f.IntegerField(),
            'amount':   f.DecimalField(max_digits=10, decimal_places=2),
            'period':   f.CharField(),
        }),
        responses={
            200: inline_serializer('STKPushAccepted', fields={
                'MerchantRequestID':    f.CharField(),
                'CheckoutRequestID':    f.CharField(),
                'ResponseCode':         f.CharField(),
                'ResponseDescription':  f.CharField(),
                'CustomerMessage':      f.CharField(),
            }),
            400: inline_serializer('ContribAlreadyConfirmed', fields={'detail': f.CharField()}),
            409: inline_serializer('STKAlreadyInFlight', fields={'detail': f.CharField()}),
        },
        description=(
            'Initiate an M-Pesa STK push for a group contribution. '
            'Returns 400 if the period is already confirmed. '
            'Returns 409 if a push is already in-flight (initiated/processing). '
            'Use POST /resend/ to retry after a cancellation or failure.'
        ),
    )
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """
        Initiate STK push. Blocked if already confirmed or in-flight.
        Use /resend/ to retry a failed or cancelled push.
        """
        from apps.mpesa.services import MpesaService
        from apps.mpesa.models import MpesaTransaction
        serializer = InitiateContributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group  = get_object_or_404(Group, id=serializer.validated_data['group_id'])
        period = serializer.validated_data['period']
        amount = serializer.validated_data['amount']

        # ── Dedup guard ───────────────────────────────────────────────────────
        existing = Contribution.objects.filter(
            group=group, member=request.user, period=period
        ).first()
        if existing:
            if existing.status == 'confirmed':
                return Response(
                    {'detail': 'Contribution for this period is already confirmed.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Block if ANY in-flight TX (initiated) exists — regardless of age.
            # Use /resend/ to send a new push after failure/cancellation.
            in_flight = MpesaTransaction.objects.filter(
                user=request.user,
                reference_id=existing.id,
                status='initiated',
            ).exists()
            if in_flight:
                return Response(
                    {'detail': 'STK push is already in-flight. Check your phone and enter M-Pesa PIN. Use /resend/ to retry after failure.'},
                    status=status.HTTP_409_CONFLICT,
                )

        # ── Determine payment type from group setting ─────────────────────────
        if group.paybill_number:
            tx_type   = group.payment_type or 'buy_goods'
            shortcode = group.paybill_number
        else:
            tx_type   = 'buy_goods'
            shortcode = None  # MpesaService falls back to MPESA_BUY_GOODS_TILL

        result = MpesaService.stk_push(
            phone=str(request.user.phone_number),
            amount=amount,
            account_ref=f"GRP{group.id}",
            description="JamiiFund Contribution",
            tx_type=tx_type,
            shortcode_override=shortcode,
        )
        if result.get('ResponseCode') == '0':
            contribution, _ = Contribution.objects.get_or_create(
                group_id = group.id,
                member   = request.user,
                period   = period,
                defaults = {'amount': amount, 'status': 'pending'},
            )
            MpesaTransaction.objects.create(
                user                = request.user,
                tx_type             = 'stk_push',
                status              = 'initiated',
                phone               = str(request.user.phone_number),
                amount              = amount,
                checkout_request_id = result.get('CheckoutRequestID', ''),
                merchant_request_id = result.get('MerchantRequestID', ''),
                reference_id        = contribution.id,
            )
        return Response(result)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Group-level pool summary for dashboard."""
        group_id = request.query_params.get('group_id')
        qs = Contribution.objects.filter(group_id=group_id, status='confirmed')
        data = qs.aggregate(total=Sum('amount'), count=Count('id'))
        return Response(data)

    @action(detail=False, methods=['post'])
    def send_reminder(self, request):
        """
        Admin manually triggers a contribution reminder SMS to unpaid members.
        Maps to the 'Re-prompt button' described in the PDF spec.
        Requires group_id and period in the request body.
        """
        from apps.notifications.tasks import send_contribution_reminders
        group_id = request.data.get('group_id')
        period   = request.data.get('period')

        if not group_id or not period:
            return Response(
                {'detail': 'group_id and period are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = get_object_or_404(Group, id=group_id)

        # Only group admins may trigger reminders
        from apps.groups.models import GroupMember
        is_admin = GroupMember.objects.filter(
            group=group, user=request.user, role='admin', status='active'
        ).exists()
        if not is_admin:
            return Response(
                {'detail': 'Only group admins can send contribution reminders.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        amount = float(group.contribution_amount or 0)
        send_contribution_reminders.delay(group_id=group.id, period=period, amount=amount)
        return Response({'detail': 'Contribution reminders queued successfully.'})

    # ── Re-send STK push (after failure / user cancellation) ──────────────────

    @extend_schema(
        tags=['Contributions'],
        request=inline_serializer('ResendContributionRequest', fields={
            'group_id': f.IntegerField(),
            'period':   f.CharField(),
        }),
        responses={
            200: inline_serializer('ResendSTKAccepted', fields={
                'MerchantRequestID':   f.CharField(),
                'CheckoutRequestID':   f.CharField(),
                'ResponseCode':        f.CharField(),
                'ResponseDescription': f.CharField(),
                'CustomerMessage':     f.CharField(),
            }),
            400: inline_serializer('ResendBadRequest', fields={'detail': f.CharField()}),
            409: inline_serializer('ResendConflict',   fields={'detail': f.CharField()}),
        },
        description=(
            'Re-send an STK push prompt for a pending contribution. '
            'Only allowed when the last transaction is failed or cancelled (result_code 1032). '
            'Blocked if contribution is already confirmed or a push is still in-flight.'
        ),
    )
    @action(detail=False, methods=['post'])
    def resend(self, request):
        """Retry an STK push for a failed or cancelled contribution."""
        from apps.mpesa.services import MpesaService
        from apps.mpesa.models import MpesaTransaction

        group_id = request.data.get('group_id')
        period   = request.data.get('period')
        if not group_id or not period:
            return Response(
                {'detail': 'group_id and period are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = get_object_or_404(Group, id=group_id)

        contribution = Contribution.objects.filter(
            group=group, member=request.user, period=period
        ).first()

        if not contribution:
            return Response(
                {'detail': 'No contribution found for this period. Use /initiate/ to start a new one.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if contribution.status == 'confirmed':
            return Response(
                {'detail': 'Contribution for this period is already confirmed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Block if still in-flight
        if MpesaTransaction.objects.filter(
            user=request.user, reference_id=contribution.id, status='initiated'
        ).exists():
            return Response(
                {'detail': 'Previous push is still in-flight. Check your phone for the PIN prompt.'},
                status=status.HTTP_409_CONFLICT,
            )

        # Only allow resend if last TX is failed/cancelled — not if never attempted
        last_tx = MpesaTransaction.objects.filter(
            user=request.user, reference_id=contribution.id
        ).order_by('-id').first()

        if not last_tx:
            return Response(
                {'detail': 'No prior transaction found. Use /initiate/ instead.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if last_tx.status not in ('failed',):
            return Response(
                {'detail': f'Cannot resend — last transaction status is "{last_tx.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Determine payment type
        if group.paybill_number:
            tx_type   = group.payment_type or 'buy_goods'
            shortcode = group.paybill_number
        else:
            tx_type   = 'buy_goods'
            shortcode = None

        result = MpesaService.stk_push(
            phone=str(request.user.phone_number),
            amount=contribution.amount,
            account_ref=f"GRP{group.id}",
            description="JamiiFund Contribution (retry)",
            tx_type=tx_type,
            shortcode_override=shortcode,
        )
        if result.get('ResponseCode') == '0':
            MpesaTransaction.objects.create(
                user                = request.user,
                tx_type             = 'stk_push',
                status              = 'initiated',
                phone               = str(request.user.phone_number),
                amount              = contribution.amount,
                checkout_request_id = result.get('CheckoutRequestID', ''),
                merchant_request_id = result.get('MerchantRequestID', ''),
                reference_id        = contribution.id,
            )
        return Response(result)

    # ── User's own M-Pesa transaction history ─────────────────────────────────

    @extend_schema(
        tags=['Contributions'],
        responses={
            200: inline_serializer('TransactionList', fields={
                'id':                    f.IntegerField(),
                'tx_type':               f.CharField(),
                'status':                f.CharField(),
                'phone':                 f.CharField(),
                'amount':                f.DecimalField(max_digits=10, decimal_places=2),
                'mpesa_receipt':         f.CharField(),
                'mpesa_transaction_id':  f.CharField(),
                'checkout_request_id':   f.CharField(),
                'result_code':           f.CharField(),
                'result_desc':           f.CharField(),
                'reference_id':          f.IntegerField(),
                'created_at':            f.DateTimeField(),
            }, many=True),
        },
        description=(
            'Retrieve all M-Pesa transactions for the authenticated user — '
            'includes success, failed, cancelled, and in-flight. '
            'Filter by status with ?status=success|failed|initiated.'
        ),
    )
    @action(detail=False, methods=['get'], url_path='transactions')
    def transactions(self, request):
        """All M-Pesa transactions for the current user."""
        from apps.mpesa.models import MpesaTransaction
        qs = MpesaTransaction.objects.filter(user=request.user).order_by('-id')
        tx_status = request.query_params.get('status')
        if tx_status:
            qs = qs.filter(status=tx_status)
        data = list(qs.values(
            'id', 'tx_type', 'status', 'phone', 'amount',
            'mpesa_receipt', 'mpesa_transaction_id', 'checkout_request_id',
            'result_code', 'result_desc', 'reference_id', 'created_at',
        ))
        return Response(data)

    # ── Recheck: query Safaricom for live STK push status ─────────────────────

    @extend_schema(
        tags=['Contributions'],
        request=inline_serializer('RecheckRequest', fields={
            'checkout_request_id': f.CharField(),
        }),
        responses={
            200: inline_serializer('RecheckResponse', fields={
                'tx_id':                 f.IntegerField(),
                'status':                f.CharField(),
                'result_code':           f.CharField(),
                'result_desc':           f.CharField(),
                'mpesa_receipt':         f.CharField(),
                'mpesa_transaction_id':  f.CharField(),
                'contribution_status':   f.CharField(),
                'daraja_raw':            f.DictField(),
            }),
            400: inline_serializer('RecheckBadRequest', fields={'detail': f.CharField()}),
            404: inline_serializer('RecheckNotFound',   fields={'detail': f.CharField()}),
        },
        description=(
            'Re-query Safaricom for the live status of an STK push — '
            'use this when the callback was delayed beyond the 2-minute window. '
            'Pass the CheckoutRequestID returned by /initiate/ or /resend/. '
            'Updates the transaction and linked contribution in the DB.'
        ),
    )
    @action(detail=False, methods=['post'], url_path='recheck')
    def recheck(self, request):
        """Query Safaricom STK Push Query API and sync status to DB."""
        from apps.mpesa.services import MpesaService
        from apps.mpesa.models import MpesaTransaction
        from django.utils import timezone

        checkout_id = request.data.get('checkout_request_id', '').strip()
        if not checkout_id:
            return Response(
                {'detail': 'checkout_request_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tx = MpesaTransaction.objects.get(
                checkout_request_id=checkout_id,
                user=request.user,
            )
        except MpesaTransaction.DoesNotExist:
            return Response(
                {'detail': 'Transaction not found or does not belong to you.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # If already resolved, just return current state — no need to query Safaricom
        if tx.status in ('success', 'failed'):
            contribution = Contribution.objects.filter(id=tx.reference_id).first()
            return Response({
                'tx_id':                tx.id,
                'status':               tx.status,
                'result_code':          tx.result_code,
                'result_desc':          tx.result_desc,
                'mpesa_receipt':        tx.mpesa_receipt or '',
                'mpesa_transaction_id': tx.mpesa_transaction_id or '',
                'contribution_status':  contribution.status if contribution else '',
                'daraja_raw':           {},
            })

        # Query Safaricom
        try:
            daraja = MpesaService.stk_query(checkout_id)
        except Exception as exc:
            return Response(
                {'detail': f'Safaricom query failed: {exc}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        result_code = str(daraja.get('ResultCode', daraja.get('errorCode', '')))
        result_desc = daraja.get('ResultDesc', daraja.get('errorMessage', ''))

        # ResponseCode 0 = query accepted. ResultCode 0 = payment successful.
        if daraja.get('ResponseCode') == '0' or result_code == '0':
            # Payment confirmed
            items = {
                i['Name']: i.get('Value')
                for i in daraja.get('CallbackMetadata', {}).get('Item', [])
            }
            receipt    = items.get('MpesaReceiptNumber', '')
            tx_id_safe = items.get('TransactionID', '') or receipt

            tx.status               = 'success'
            tx.result_code          = result_code
            tx.result_desc          = result_desc
            tx.mpesa_receipt        = receipt or tx.mpesa_receipt
            tx.mpesa_transaction_id = tx_id_safe or tx.mpesa_transaction_id
            tx.raw_callback         = daraja
            tx.save()

            contribution = Contribution.objects.filter(id=tx.reference_id).first()
            if contribution and contribution.status != 'confirmed':
                contribution.status       = 'confirmed'
                contribution.mpesa_ref    = tx.mpesa_receipt
                contribution.confirmed_at = timezone.now()
                contribution.save(update_fields=['status', 'mpesa_ref', 'confirmed_at'])
                from apps.notifications.tasks import notify_contribution_confirmed
                notify_contribution_confirmed.delay(contribution.id)

        elif result_code and result_code not in ('', '500'):
            # Definitive failure/cancellation
            tx.status      = 'failed'
            tx.result_code = result_code
            tx.result_desc = result_desc
            tx.raw_callback = daraja
            tx.save()

            contribution = Contribution.objects.filter(id=tx.reference_id).first()
            if contribution and contribution.status == 'pending':
                has_success = MpesaTransaction.objects.filter(
                    reference_id=tx.reference_id, status='success'
                ).exists()
                if not has_success:
                    contribution.status = 'failed'
                    contribution.save(update_fields=['status'])
            # else: still processing (e.g. errorCode 500.001.1001)
        else:
            contribution = Contribution.objects.filter(id=tx.reference_id).first()

        contribution = Contribution.objects.filter(id=tx.reference_id).first()
        return Response({
            'tx_id':                tx.id,
            'status':               tx.status,
            'result_code':          tx.result_code,
            'result_desc':          tx.result_desc,
            'mpesa_receipt':        tx.mpesa_receipt or '',
            'mpesa_transaction_id': tx.mpesa_transaction_id or '',
            'contribution_status':  contribution.status if contribution else '',
            'daraja_raw':           daraja,
        })
