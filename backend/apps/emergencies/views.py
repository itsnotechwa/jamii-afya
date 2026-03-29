from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from .models import EmergencyRequest, EmergencyApproval, EmergencyDocument
from .serializers import EmergencyRequestSerializer, VoteSerializer, EmergencyDocumentSerializer
from utils.permissions import IsGroupAdmin
from utils.eligibility import check_eligibility


@extend_schema(tags=['Emergencies'])
class EmergencyRequestViewSet(viewsets.ModelViewSet):
    serializer_class   = EmergencyRequestSerializer
    permission_classes = [IsAuthenticated]
    queryset           = EmergencyRequest.objects.none()  # required for schema introspection

    def get_queryset(self):
        return EmergencyRequest.objects.filter(
            group__memberships__user=self.request.user,
            group__memberships__status='active'
        ).annotate(
            approval_count=Count('approvals', filter=Q(approvals__decision='approve'))
        ).select_related('claimant', 'group').prefetch_related('documents', 'approvals').distinct()

    def perform_create(self, serializer):
        user  = self.request.user
        group = serializer.validated_data['group']

        # ── Eligibility gate ──────────────────────────────────────────────
        eligible, reason = check_eligibility(user, group)
        if not eligible:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(reason)

        serializer.save(claimant=user)

        # Notify group admins
        from apps.notifications.tasks import notify_admins_new_emergency
        notify_admins_new_emergency.delay(serializer.instance.id)

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """Admin casts approve/reject vote. Auto-disburses when threshold met."""
        emergency = self.get_object()

        if emergency.status != 'pending':
            return Response({'detail': 'This request is no longer pending.'}, status=400)

        # Only group admins may vote
        from apps.groups.models import GroupMember
        is_admin = GroupMember.objects.filter(
            group=emergency.group, user=request.user, role='admin', status='active'
        ).exists()
        if not is_admin:
            return Response({'detail': 'Only group admins can vote.'}, status=403)

        if EmergencyApproval.objects.filter(emergency=emergency, admin=request.user).exists():
            return Response({'detail': 'You have already voted.'}, status=400)

        serializer = VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            decision = serializer.validated_data['decision']
            note     = serializer.validated_data.get('note', '')

            EmergencyApproval.objects.create(
                emergency=emergency,
                admin=request.user,
                decision=decision,
                note=note,
            )

            approval_count = emergency.approvals.filter(decision='approve').count()
            reject_count   = emergency.approvals.filter(decision='reject').count()

            if decision == 'reject' and reject_count >= emergency.group.approval_threshold:
                emergency.status           = 'rejected'
                emergency.rejection_reason = note or 'Rejected by admins.'
                emergency.resolved_at      = timezone.now()
                emergency.save(update_fields=['status', 'rejection_reason', 'resolved_at'])

                # SMS: tell claimant request was rejected
                from apps.notifications.tasks import notify_emergency_rejected
                notify_emergency_rejected.delay(emergency.id)

            elif approval_count >= emergency.group.approval_threshold:
                emergency.status          = 'approved'
                emergency.amount_approved = min(
                    emergency.amount_requested, emergency.group.max_payout_amount
                )
                emergency.resolved_at = timezone.now()
                emergency.save(update_fields=['status', 'amount_approved', 'resolved_at'])

                # SMS: tell claimant they've been approved
                from apps.notifications.tasks import notify_emergency_approved
                notify_emergency_approved.delay(emergency.id)

                # Trigger B2C payout async
                from apps.mpesa.tasks import disburse_emergency_payout
                disburse_emergency_payout.delay(emergency.id)

            # SMS: confirm the vote back to the admin who just voted
            from apps.notifications.tasks import notify_vote_cast
            notify_vote_cast.delay(emergency.id, request.user.id, decision)

        return Response(EmergencyRequestSerializer(emergency).data)

    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Attach supporting documents to an emergency request."""
        emergency  = self.get_object()
        serializer = EmergencyDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(emergency=emergency)
        return Response(serializer.data, status=201)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Shortcut: all pending requests in my groups (for admin dashboard)."""
        qs = self.get_queryset().filter(status='pending')
        return Response(EmergencyRequestSerializer(qs, many=True).data)
