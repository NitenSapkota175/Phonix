"""
Admin configuration for the accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerificationToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_email_verified', 'is_active_investor',
                    'direct_referrals_count', 'joined_at')
    list_filter = ('role', 'is_email_verified', 'is_active_investor', 'is_staff')
    search_fields = ('username', 'email', 'referral_code', 'phone')
    readonly_fields = ('referral_code', 'joined_at', 'direct_referrals_count')
    ordering = ('-joined_at',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Phonix', {
            'fields': ('role', 'phone', 'referral_code', 'referred_by',
                       'direct_referrals_count', 'is_active_investor',
                       'is_email_verified', 'transaction_password'),
        }),
    )


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires_at', 'is_used')
    list_filter = ('is_used',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token',)
