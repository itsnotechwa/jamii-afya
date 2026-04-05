from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['phone_number', 'first_name', 'last_name', 'national_id', 'is_verified', 'is_staff']
    search_fields = ['phone_number', 'first_name', 'last_name', 'national_id']
    list_filter   = ['is_verified', 'is_staff', 'is_active']
    fieldsets     = BaseUserAdmin.fieldsets + (
        ('Jamii Afya', {'fields': ('phone_number', 'national_id', 'is_verified', 'profile_pic')}),
    )
