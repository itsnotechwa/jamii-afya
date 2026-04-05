import logging

from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
import rest_framework.fields as f
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MpesaTransaction
from .webhook_security import (
    mark_replay_processed,
    parse_b2c_result_payload,
    parse_b2c_timeout_payload,
    parse_stk_callback_payload,
    should_skip_replay,
    verify_mpesa_webhook,
)

logger = logging.getLogger(__name__)


def _stk_items_to_map(items: list[dict]) -> dict:
    out = {}
    for i in items:
        name = i.get('Name')
        if name:
            out[name] = i.get('Value')
    return out


@extend_schema(
    tags=['M-Pesa'],
    request=inline_serializer('STKCallbackRequest', fields={}),
    responses={200: inline_serializer('MpesaCallbackResponse', fields={'ResultCode': f.IntegerField(), 'ResultDesc': f.CharField()})},
    description='Safaricom STK Push callback. Called by Safaricom after payment completes. Internal use only.',
)
class STKCallbackView(APIView):
    """
    Safaricom POSTs here after STK Push completes.
    Confirms the contribution on success.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        bad = verify_mpesa_webhook(request)
        if bad is not None:
            return bad

        try:
            parsed = parse_stk_callback_payload(dict(request.data))
        except ValueError as exc:
            logger.warning('STK callback invalid payload: %s', exc)
            return Response({'ResultCode': 1, 'ResultDesc': 'Bad Request'}, status=400)

        checkout_id = parsed['checkout_id']
        result_code = parsed['result_code']
        callback = parsed['callback']
        data = parsed['raw']

        if should_skip_replay('stk', checkout_id, result_code):
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        try:
            tx = MpesaTransaction.objects.get(checkout_request_id=checkout_id)
        except MpesaTransaction.DoesNotExist:
            logger.warning('STK callback for unknown CheckoutRequestID: %s', checkout_id)
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        if result_code != '0' and tx.status == 'success':
            logger.error(
                'STK callback conflict: failure after success for CheckoutRequestID=%s',
                checkout_id,
            )
            mark_replay_processed('stk', checkout_id, result_code)
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        if result_code == '0' and tx.status == 'success':
            mark_replay_processed('stk', checkout_id, result_code)
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        tx.result_code = result_code
        tx.result_desc = parsed['result_desc']
        tx.raw_callback = data

        if result_code == '0':
            items = _stk_items_to_map(parsed['metadata_items'])
            tx.mpesa_receipt = items.get('MpesaReceiptNumber', '') or ''
            tx.mpesa_transaction_id = (
                items.get('TransactionID', '') or items.get('MpesaReceiptNumber', '') or ''
            )
            tx.status = 'success'
            tx.save()

            from apps.contributions.models import Contribution

            contribution = Contribution.objects.filter(id=tx.reference_id).first()
            if contribution:
                if contribution.status != 'confirmed':
                    contribution.status = 'confirmed'
                    contribution.mpesa_ref = tx.mpesa_receipt
                    contribution.confirmed_at = timezone.now()
                    contribution.save(update_fields=['status', 'mpesa_ref', 'confirmed_at'])

                    from apps.notifications.tasks import notify_contribution_confirmed

                    notify_contribution_confirmed.delay(contribution.id)
        else:
            tx.status = 'failed'
            tx.save()

            from apps.contributions.models import Contribution

            contribution = Contribution.objects.filter(id=tx.reference_id).first()
            if contribution and contribution.status == 'pending':
                has_success = MpesaTransaction.objects.filter(
                    reference_id=tx.reference_id, status='success'
                ).exists()
                if not has_success:
                    contribution.status = 'failed'
                    contribution.save(update_fields=['status'])

        mark_replay_processed('stk', checkout_id, result_code)
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})


@extend_schema(
    tags=['M-Pesa'],
    request=inline_serializer('B2CResultRequest', fields={}),
    responses={200: inline_serializer('B2CResultResponse', fields={'ResultCode': f.IntegerField(), 'ResultDesc': f.CharField()})},
    description='Safaricom B2C result callback. Called when a payout completes or fails. Internal use only.',
)
class B2CResultView(APIView):
    """
    Safaricom POSTs B2C result here.
    Marks emergency as PAID or FAILED.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        bad = verify_mpesa_webhook(request)
        if bad is not None:
            return bad

        try:
            parsed = parse_b2c_result_payload(dict(request.data))
        except ValueError as exc:
            logger.warning('B2C result invalid payload: %s', exc)
            return Response({'ResultCode': 1, 'ResultDesc': 'Bad Request'}, status=400)

        conv_id = parsed['conversation_id']
        result_code = parsed['result_code']
        data = parsed['raw']

        if should_skip_replay('b2c', conv_id, result_code):
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        try:
            tx = MpesaTransaction.objects.get(checkout_request_id=conv_id)
        except MpesaTransaction.DoesNotExist:
            logger.warning('B2C result for unknown ConversationID: %s', conv_id)
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        if result_code != '0' and tx.status == 'success':
            logger.error(
                'B2C callback conflict: failure after success for ConversationID=%s',
                conv_id,
            )
            mark_replay_processed('b2c', conv_id, result_code)
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        if result_code == '0' and tx.status == 'success':
            mark_replay_processed('b2c', conv_id, result_code)
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        tx.raw_callback = data
        tx.result_code = result_code
        tx.result_desc = parsed['result_desc']

        from apps.emergencies.models import EmergencyRequest
        from apps.notifications.tasks import notify_payout_result

        if result_code == '0':
            params = {p['Key']: p.get('Value') for p in parsed['params_list'] if p.get('Key')}
            tx.mpesa_receipt = params.get('TransactionReceipt', '') or ''
            tx.status = 'success'
            tx.save()

            updated = EmergencyRequest.objects.filter(id=tx.reference_id).exclude(status='paid').update(
                status='paid',
                mpesa_ref=tx.mpesa_receipt,
                resolved_at=timezone.now(),
            )
            if updated:
                notify_payout_result.delay(tx.reference_id, success=True)
        else:
            tx.status = 'failed'
            tx.save()
            updated = EmergencyRequest.objects.filter(id=tx.reference_id).exclude(
                status__in=('paid', 'failed')
            ).update(status='failed')
            if updated:
                notify_payout_result.delay(tx.reference_id, success=False)

        mark_replay_processed('b2c', conv_id, result_code)
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})


@extend_schema(
    tags=['M-Pesa'],
    request=inline_serializer('B2CTimeoutRequest', fields={}),
    responses={200: inline_serializer('B2CTimeoutResponse', fields={'ResultCode': f.IntegerField(), 'ResultDesc': f.CharField()})},
    description='Safaricom B2C timeout callback. Called when a payout request times out. Internal use only.',
)
class B2CTimeoutView(APIView):
    """Safaricom calls this if the B2C request times out."""

    permission_classes = [AllowAny]

    def post(self, request):
        bad = verify_mpesa_webhook(request)
        if bad is not None:
            return bad

        try:
            conv_id = parse_b2c_timeout_payload(dict(request.data))
        except ValueError as exc:
            logger.warning('B2C timeout invalid payload: %s', exc)
            return Response({'ResultCode': 1, 'ResultDesc': 'Bad Request'}, status=400)

        if should_skip_replay('b2cto', conv_id, 'timeout'):
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        MpesaTransaction.objects.filter(checkout_request_id=conv_id).update(status='timeout')
        logger.error('B2C timeout for ConversationID: %s', conv_id)
        mark_replay_processed('b2cto', conv_id, 'timeout')
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})
