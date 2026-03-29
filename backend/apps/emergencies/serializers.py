from rest_framework import serializers
from .models import EmergencyRequest, EmergencyDocument, EmergencyApproval


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
    approval_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = EmergencyRequest
        fields = ['id', 'group', 'claimant', 'claimant_name', 'emergency_type',
                  'description', 'amount_requested', 'amount_approved', 'status',
                  'payout_phone', 'rejection_reason', 'mpesa_ref',
                  'approval_count', 'documents', 'approvals', 'created_at', 'resolved_at']
        read_only_fields = ['claimant', 'status', 'amount_approved',
                            'rejection_reason', 'mpesa_ref', 'resolved_at']


class VoteSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approve', 'reject'])
    note     = serializers.CharField(required=False, allow_blank=True)
