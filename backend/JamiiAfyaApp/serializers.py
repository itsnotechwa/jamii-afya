from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate

from .models import EmergencyRequest, EmergencyDocument, EmergencyApproval, Group, GroupMember, User
import secrets



# The serializers defined in this module are responsible for converting model instances of EmergencyRequest, EmergencyDocument, and EmergencyApproval into JSON format for API responses, as well as validating and deserializing incoming data for creating or updating these models through the API. Each serializer includes fields that correspond to the model attributes, along with any additional read-only fields or nested serializers for related objects.
class EmergencyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EmergencyDocument
        fields = ['id', 'file', 'label', 'uploaded_at']



# The EmergencyApprovalSerializer includes a read-only field for the admin's full name, which is derived from the related admin user model, and ensures that the voted_at timestamp is read-only to maintain the integrity of approval records.
class EmergencyApprovalSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.get_full_name', read_only=True)

    # The Meta class defines the model and fields for the EmergencyApprovalSerializer 
    #It specifies which fields are read-only to prevent unauthorized modifications to approval records.
    class Meta:
        model  = EmergencyApproval
        fields = ['id', 'admin', 'admin_name', 'decision', 'note', 'voted_at']
        read_only_fields = ['voted_at']



# The EmergencyRequestSerializer includes nested serializers for related documents and approvals, as well as additional read-only fields for the claimant's full name and the count of approvals. 
#It also overrides the create method to automatically set the claimant to the currently authenticated user when a new emergency request is created.
class EmergencyRequestSerializer(serializers.ModelSerializer):
    documents    = EmergencyDocumentSerializer(many=True, read_only=True)
    approvals    = EmergencyApprovalSerializer(many=True, read_only=True)
    claimant_name = serializers.CharField(source='claimant.get_full_name', read_only=True)
    approval_count = serializers.IntegerField(read_only=True)

    # The Meta class defines the model and fields for the EmergencyRequestSerializer.
    #It specifies which fields are read-only to ensure that certain attributes of an emergency request cannot be modified through the API after creation.
    class Meta:
        model  = EmergencyRequest
        fields = ['id', 'group', 'claimant', 'claimant_name', 'emergency_type',
                  'description', 'amount_requested', 'amount_approved', 'status',
                  'payout_phone', 'rejection_reason', 'mpesa_ref',
                  'approval_count', 'documents', 'approvals', 'created_at', 'resolved_at']
        read_only_fields = ['claimant', 'status', 'amount_approved',
                            'rejection_reason', 'mpesa_ref', 'resolved_at']

    def create(self, validated_data):
        validated_data['claimant'] = self.context['request'].user
        return super().create(validated_data)



# The VoteSerializer is a simple serializer that validates the input for voting on an emergency request, ensuring that the decision is either 'approve' or 'reject', and allowing for an optional note to be included with the vote.
class VoteSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approve', 'reject'])
    note     = serializers.CharField(required=False, allow_blank=True)



# The GroupSerializer includes additional read-only fields for the member count and total pool of contributions, which are calculated based on related models. It also overrides the create method to automatically generate an invite code and set the creator of the group when a new group is created through the API.
class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    total_pool   = serializers.SerializerMethodField()

    class Meta:
        model  = Group
        fields = ['id', 'name', 'description', 'invite_code', 'is_active',
                  'min_contributions_to_qualify', 'max_payout_amount',
                  'approval_threshold', 'member_count', 'total_pool', 'created_at']
        read_only_fields = ['invite_code', 'created_at']

    def get_member_count(self, obj):
        return obj.memberships.filter(status='active').count()

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



# The GroupMemberSerializer includes read-only fields for the user's full name and phone number, which are derived from the related user model, and ensures that the joined_at timestamp is read-only to maintain the integrity of group membership records.
class GroupMemberSerializer(serializers.ModelSerializer):
    user_name  = serializers.CharField(source='user.get_full_name', read_only=True)
    phone      = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model  = GroupMember
        fields = ['id', 'user', 'user_name', 'phone', 'role', 'status', 'joined_at']
        read_only_fields = ['joined_at']



# The JoinGroupSerializer is a simple serializer that validates the input for joining a group using an invite code, ensuring that the provided invite code corresponds to an active group in the system.
class JoinGroupSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=12)

    def validate_invite_code(self, value):
        try:
            return Group.objects.get(invite_code=value.upper(), is_active=True)
        except Group.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired invite code.")



# The RegisterSerializer validates that the provided passwords match and creates a new user with the specified attributes, while the LoginSerializer authenticates the user and returns a JWT token along with the user's profile information upon successful login.
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'phone_number',
                  'national_id', 'email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.username = str(validated_data['phone_number'])
        user.set_password(password)
        user.save()
        return user



# The LoginSerializer authenticates the user using their phone number and password, and if successful, generates a JWT token for the user and returns it along with the user's profile information. If authentication fails, it raises a validation error indicating that the credentials are invalid.
class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password     = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['phone_number'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        tokens = RefreshToken.for_user(user)
        return {
            'user': UserProfileSerializer(user).data,
            'access':  str(tokens.access_token),
            'refresh': str(tokens),
        }



# The UserProfileSerializer is a simple serializer that provides a read-only representation of the user's profile information, including their full name, phone number, national ID, verification status, and profile picture.
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'first_name', 'last_name', 'phone_number',
                  'national_id', 'email', 'is_verified', 'profile_pic']
        read_only_fields = ['is_verified']
