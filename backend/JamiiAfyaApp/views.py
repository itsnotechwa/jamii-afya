from django.shortcuts import render, get_object_or_404
from django.urls import path, include

from django.db.models import Sum, Count
from django.db import transaction

from django.utils import timezone
from utils.permissions import IsGroupAdmin
from utils.eligibility import check_eligibility

from rest_framework import serializers, viewsets, status, generics

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.serializers import ModelSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView

from .serializers import EmergencyRequestSerializer, VoteSerializer, EmergencyDocumentSerializer, GroupSerializer, GroupMemberSerializer, JoinGroupSerializer, RegisterSerializer, LoginSerializer, UserProfileSerializer

from .models import *
import logging

logging.basicConfig(level=logging.INFO)



# The serializers defined in this module are responsible for converting model instances of EmergencyRequest, EmergencyDocument, and EmergencyApproval into JSON format for API responses, as well as validating and deserializing incoming data for creating or updating these models through the API. Each serializer includes fields that correspond to the model attributes, along with any additional read-only fields or nested serializers for related objects.
class AuditLogSerializer(ModelSerializer):
    class Meta:
        model  = AuditLog
        fields = ['id', 'user', 'action', 'endpoint', 'response_code',
                  'ip_address', 'timestamp']



# The AuditLogViewSet provides a read-only API endpoint for superadmins to access the full audit trail of write actions for compliance purposes. It includes filtering and ordering capabilities, and ensures that only authenticated superusers can access the audit logs.
class AuditLogViewSet(ReadOnlyModelViewSet):
    """Superadmin-only: full audit trail for compliance."""
    serializer_class   = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields   = ['user', 'action', 'endpoint']
    ordering_fields    = ['timestamp']

    def get_queryset(self):
        return AuditLog.objects.select_related('user').order_by('-timestamp')


router = DefaultRouter()
router.register(r'', AuditLogViewSet, basename='audit')
urlpatterns = [path('', include(router.urls))]



# The ContributionSerializer is responsible for converting Contribution model instances into JSON format for API responses, as well as validating and deserializing incoming data for creating or updating contributions through the API. It includes additional read-only fields for the member's full name and the group's name to provide more context in API responses.
class ContributionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    group_name  = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model  = Contribution
        fields = ['id', 'group', 'group_name', 'member', 'member_name',
                  'amount', 'status', 'mpesa_ref', 'period', 'created_at', 'confirmed_at']
        read_only_fields = ['status', 'mpesa_ref', 'confirmed_at']



# The ContributionViewSet provides API endpoints for members to view their contributions and initiate new contributions through M-Pesa. It includes a custom action for initiating contributions, which triggers an STK Push to the member's phone, and another action for retrieving a summary of contributions for a specific group. 
class InitiateContributionSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    amount   = serializers.DecimalField(max_digits=10, decimal_places=2)
    period   = serializers.CharField(max_length=7)  # YYYY-MM



# The ContributionViewSet provides API endpoints for members to view their contributions and initiate new contributions through M-Pesa. It includes a custom action for initiating contributions, which triggers an STK Push to the member's phone, and another action for retrieving a summary of contributions for a specific group.
class ContributionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = ContributionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contribution.objects.filter(
            group__memberships__user=self.request.user,
            group__memberships__status='active'
        ).select_related('member', 'group').distinct()


    @action(detail=False, methods=['post'])
    def initiate(self, request):
        
        #Kick off STK Push for a contribution.
        from apps.mpesa.services import MpesaService
        serializer = InitiateContributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = MpesaService.stk_push(
            phone=str(request.user.phone_number),
            amount=serializer.validated_data['amount'],
            account_ref=f"GRP{serializer.validated_data['group_id']}",
            description="JamiiFund Contribution",
        )
        if result.get('ResponseCode') == '0':
            # Create pending record; confirmed on M-Pesa callback
            Contribution.objects.get_or_create(
                group_id = serializer.validated_data['group_id'],
                member   = request.user,
                period   = serializer.validated_data['period'],
                defaults = {'amount': serializer.validated_data['amount'], 'status': 'pending'}
            )
        return Response(result)
    


    #Group-level pool summary for dashboard.
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Group-level pool summary for dashboard."""
        group_id = request.query_params.get('group_id')
        qs = Contribution.objects.filter(group_id=group_id, status='confirmed')
        data = qs.aggregate(total=Sum('amount'), count=Count('id'))
        return Response(data)

# The EmergencyRequestViewSet provides API endpoints for members to create emergency requests, view their requests, and for group admins to approve or reject requests. It includes custom actions for voting on requests, uploading supporting documents, and listing pending requests for admin review. The viewset ensures that only authenticated users can access these endpoints and that certain actions are restricted to group admins.
class EmergencyRequestViewSet(viewsets.ModelViewSet):
    serializer_class   = EmergencyRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmergencyRequest.objects.filter(
            group__memberships__user=self.request.user,
            group__memberships__status='active'
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

    # Admin voting endpoint for approving/rejecting emergency requests. Enforces that only group admins can vote, and that each admin can only vote once per request. Automatically updates the emergency request status to "approved" or "rejected" when the approval threshold is met, and triggers SMS notifications to the claimant and admins accordingly.
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

    # Admins can upload supporting documents (e.g. photos, hospital bills) to an emergency request through this endpoint. The uploaded documents are associated with the emergency request and can be viewed by group members when reviewing the request details.
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Attach supporting documents to an emergency request."""
        emergency  = self.get_object()
        serializer = EmergencyDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(emergency=emergency)
        return Response(serializer.data, status=201)

    # Admin dashboard shortcut to list all pending requests in my groups.
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Shortcut: all pending requests in my groups (for admin dashboard)."""
        qs = self.get_queryset().filter(status='pending')
        return Response(EmergencyRequestSerializer(qs, many=True).data)



# The GroupViewSet provides API endpoints for managing groups, including creating new groups, joining existing groups via invite code, and managing group members. 
# It includes custom actions for joining a group, listing group members, and updating member roles or statuses (admin only). 
# The viewset ensures that only authenticated users can access these endpoints and that certain actions are restricted to group admins.
class GroupViewSet(viewsets.ModelViewSet):
    serializer_class   = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only groups the user belongs to
        return Group.objects.filter(
            memberships__user=self.request.user,
            memberships__status='active'
        ).select_related('created_by').distinct()


    #Create a new group and automatically assign the creator as an admin member of the group. 
    #The invite code is generated using the secrets library.
    @action(detail=False, methods=['post'])
    def join(self, request):
        """Join a group via invite code."""
        serializer = JoinGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data['invite_code']

        if GroupMember.objects.filter(group=group, user=request.user).exists():
            return Response({'detail': 'Already a member.'}, status=400)

        GroupMember.objects.create(group=group, user=request.user)
        return Response({'detail': f'Joined {group.name} successfully.'}, status=201)


    #Listing all members in a group.
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List all members in a group."""
        group   = self.get_object()
        members = GroupMember.objects.filter(group=group).select_related('user')
        return Response(GroupMemberSerializer(members, many=True).data)


    #Update member role or status (admin only)
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsGroupAdmin])
    def update_member(self, request, pk=None):
        """Update member role or status (admin only)."""
        group     = self.get_object()
        member_id = request.data.get('member_id')
        member    = get_object_or_404(GroupMember, id=member_id, group=group)
        serializer = GroupMemberSerializer(member, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# The NotificationSerializer is responsible for converting Notification model instances into JSON format for API responses, as well as validating and deserializing incoming data for creating or updating notifications through the API. It includes fields that correspond to the model attributes, allowing for efficient management of notification statuses and content in the frontend application.
class NotificationSerializer(ModelSerializer):
    class Meta:
        model  = Notification
        fields = ['id', 'event_type', 'title', 'body', 'is_read', 'reference_id', 'created_at']

# The NotificationViewSet provides API endpoints for users to retrieve their notifications, mark notifications as read, and get the count of unread notifications. It ensures that only authenticated users can access their notifications and allows for efficient management of notification statuses to enhance the user experience in the frontend application.
class NotificationViewSet(ReadOnlyModelViewSet):
    serializer_class   = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

    # Endpoint to mark all notifications as read, allowing the frontend to clear the unread count or badge when the user views their notifications.
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'detail': 'All notifications marked as read.'})

    # Endpoint to mark a single notification as read when the user views it, allowing the frontend to update the notification's status and remove it from the unread count or badge.
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notif).data)

    # Endpoint to retrieve the count of unread notifications for the authenticated user, allowing the frontend to display notification badges or alerts accordingly.
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread': count})


router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
urlpatterns = [path('', include(router.urls))]




# The RegisterView allows new users to create an account by providing necessary information. 
# It validates the incoming data using the RegisterSerializer.
# Upon successful registration, returns a message prompting the user to verify their phone number to continue using the application.
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'message': 'Account created. Verify your phone to continue.'},
            status=status.HTTP_201_CREATED
        )



# The LoginView handles user authentication by validating credentials and returning a token upon successful login.
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)



# The ProfileView allows authenticated users to retrieve and update their profile information.
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user



class STKCallbackView(APIView):
    """
    Safaricom POSTs here after STK Push completes.
    Confirms the contribution on success.
    """
    permission_classes = [AllowAny]  # Safaricom has no auth header; validate via receipt lookup

    def post(self, request):
        data     = request.data
        callback = data.get('Body', {}).get('stkCallback', {})
        checkout_id = callback.get('CheckoutRequestID', '')
        result_code = str(callback.get('ResultCode', ''))

        try:
            tx = MpesaTransaction.objects.get(checkout_request_id=checkout_id)
        except MpesaTransaction.DoesNotExist:
            logger.warning(f"STK callback for unknown CheckoutRequestID: {checkout_id}")
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        tx.result_code   = result_code
        tx.result_desc   = callback.get('ResultDesc', '')
        tx.raw_callback  = data

        if result_code == '0':
            items = {
                i['Name']: i.get('Value')
                for i in callback.get('CallbackMetadata', {}).get('Item', [])
            }
            tx.mpesa_receipt = items.get('MpesaReceiptNumber', '')
            tx.status        = 'success'
            tx.save()

            # Confirm the pending contribution
            from apps.contributions.models import Contribution
            contribution_qs = Contribution.objects.filter(
                mpesa_ref__isnull=True,
                member=tx.user,
                status='pending',
            ).order_by('-created_at')
            contribution = contribution_qs.first()
            contribution_qs.update(
                status='confirmed',
                mpesa_ref=tx.mpesa_receipt,
                confirmed_at=timezone.now()
            )
            # SMS confirmation to contributor
            if contribution:
                from apps.notifications.tasks import notify_contribution_confirmed
                notify_contribution_confirmed.delay(contribution.id)
        else:
            tx.status = 'failed'
            tx.save()

        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})


class B2CResultView(APIView):
    """
    Safaricom POSTs B2C result here.
    Marks emergency as PAID or FAILED.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data   = request.data
        result = data.get('Result', {})
        conv_id     = result.get('ConversationID', '')
        result_code = str(result.get('ResultCode', ''))

        try:
            tx = MpesaTransaction.objects.get(checkout_request_id=conv_id)
        except MpesaTransaction.DoesNotExist:
            logger.warning(f"B2C result for unknown ConversationID: {conv_id}")
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

        tx.raw_callback = data
        tx.result_code  = result_code
        tx.result_desc  = result.get('ResultDesc', '')

        from apps.emergencies.models import EmergencyRequest
        from apps.notifications.tasks import notify_payout_result

        if result_code == '0':
            params = {
                p['Key']: p.get('Value')
                for p in result.get('ResultParameters', {}).get('ResultParameter', [])
            }
            tx.mpesa_receipt = params.get('TransactionReceipt', '')
            tx.status        = 'success'
            tx.save()

            EmergencyRequest.objects.filter(id=tx.reference_id).update(
                status='paid',
                mpesa_ref=tx.mpesa_receipt,
                resolved_at=timezone.now()
            )
            notify_payout_result.delay(tx.reference_id, success=True)
        else:
            tx.status = 'failed'
            tx.save()
            EmergencyRequest.objects.filter(id=tx.reference_id).update(status='failed')
            notify_payout_result.delay(tx.reference_id, success=False)

        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})


class B2CTimeoutView(APIView):
    """Safaricom calls this if the B2C request times out."""
    permission_classes = [AllowAny]

    def post(self, request):
        conv_id = request.data.get('Result', {}).get('ConversationID', '')
        MpesaTransaction.objects.filter(checkout_request_id=conv_id).update(status='timeout')
        logger.error(f"B2C timeout for ConversationID: {conv_id}")
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

