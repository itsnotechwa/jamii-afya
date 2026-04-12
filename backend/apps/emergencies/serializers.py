from rest_framework import serializers
from .models import EmergencyRequest, EmergencyDocument, EmergencyApproval, Hospital


class EmergencyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EmergencyDocument
        fields = ['id', 'file', 'label', 'uploaded_at']


class EmergencyApprovalSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.get_full_name', read_only=True)

    class Meta:
        model  = EmergencyApproval
        fields = ['id', 'admin', 'admin_name', 'decision', 'note', 'voted_at']
        read_only_fields = ['voted_at']


class EmergencyRequestSerializer(serializers.ModelSerializer):
    documents    = EmergencyDocumentSerializer(many=True, read_only=True)
    approvals    = EmergencyApprovalSerializer(many=True, read_only=True)
    claimant_name = serializers.CharField(source='claimant.get_full_name', read_only=True)
    approval_count = serializers.SerializerMethodField()
    paybill = serializers.CharField(source='group.paybill_number', read_only=True)

    class Meta:
        model  = EmergencyRequest
        fields = ['id', 'group', 'claimant', 'claimant_name', 'emergency_type',
                  'description', 'amount_requested', 'amount_approved', 'status',
                  'payout_phone', 'rejection_reason', 'mpesa_ref', 'paybill',
                  'approval_count', 'documents', 'approvals', 'created_at', 'resolved_at']
        read_only_fields = ['claimant', 'status', 'amount_approved',
                            'rejection_reason', 'mpesa_ref', 'resolved_at']

    def get_approval_count(self, obj):
        # Prefer SQL annotation from EmergencyRequestViewSet.get_queryset when present.
        _missing = object()
        annotated = getattr(obj, 'approval_count', _missing)
        if annotated is not _missing:
            return annotated
        # Always count from DB so prefetched `approvals` can never serve stale data.
        return EmergencyApproval.objects.filter(emergency=obj, decision='approve').count()


class VoteSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approve', 'reject'])
    note     = serializers.CharField(required=False, allow_blank=True)


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Hospital
        fields = ['id', 'name', 'location']
