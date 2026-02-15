from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model with MLM fields"""
    
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'wallet_balance', 'registration_bonus', 'total_invested',
        'total_earnings', 'direct_referrals_count', 'is_active_investor',
        'referral_code'
    ]
    
    list_filter = [
        'is_active_investor', 'is_staff', 'is_superuser',
        'is_active', 'joined_at'
    ]
    
    search_fields = [
        'username', 'email', 'first_name', 'last_name',
        'referral_code'
    ]
    
    readonly_fields = [
        'joined_at', 'last_login', 'date_joined',
        'referral_code', 'earnings_cap_percentage'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Wallet & Finances', {
            'fields': (
                'wallet_balance', 'registration_bonus',
                'total_invested', 'total_earnings',
                'earnings_cap_percentage', 'trc20_wallet_address'
            )
        }),
        ('MLM Structure', {
            'fields': (
                'referred_by', 'referral_code',
                'direct_referrals_count', 'is_active_investor'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'joined_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'referred_by'
            ),
        }),
    )
