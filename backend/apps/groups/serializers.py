from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Group, GroupMember
import secrets


class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    total_pool   = serializers.SerializerMethodField()

    class Meta:
        model  = Group
        fields = [
            'id', 'name', 'description', 'invite_code', 'is_active',
            'contribution_frequency', 'contribution_deadline_day',
            'contribution_amount', 'paybill_number',
            'min_contributions_to_qualify', 'max_payout_amount',
            'approval_threshold', 'member_count', 'total_pool', 'created_at',
        ]
        read_only_fields = ['invite_code', 'created_at']

    @extend_schema_field(serializers.IntegerField())
    def get_member_count(self, obj):
        return obj.memberships.filter(status='active').count()

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_total_pool(self, obj):
        from apps.contributions.models import Contribution
        from django.db.models import Sum
        result = Contribution.objects.filter(
            group=obj, status='confirmed'
        ).aggregate(total=Sum('amount'))
        return result['total'] or 0

    def create(self, validated_data):
        validated_data['invite_code'] = secrets.token_urlsafe(8)[:12].upper()
        validated_data['created_by']  = self.context['request'].user
        group = super().create(validated_data)
        # Creator automatically becomes admin member
        GroupMember.objects.create(group=group, user=group.created_by, role='admin')
        return group


class GroupMemberSerializer(serializers.ModelSerializer):
    user_name  = serializers.CharField(source='user.get_full_name', read_only=True)
    phone      = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model  = GroupMember
        fields = ['id', 'user', 'user_name', 'phone', 'role', 'status', 'joined_at']
        read_only_fields = ['joined_at']


class JoinGroupSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=12)

    def validate_invite_code(self, value):
        try:
            return Group.objects.get(invite_code=value.upper(), is_active=True)
        except Group.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired invite code.")
