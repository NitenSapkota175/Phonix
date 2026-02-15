from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for Subscription model"""
    
    list_display = [
        'user', 'amount', 'tier', 'monthly_rate',
        'total_earned', 'earnings_cap', 'earnings_percentage',
        'is_active', 'started_at'
    ]
    
    list_filter = ['tier', 'is_active', 'started_at']
    
    search_fields = ['user__username', 'user__email']
    
    readonly_fields = [
        'tier', 'monthly_rate', 'earnings_cap',
        'started_at', 'completed_at', 'earnings_percentage',
        'days_active'
    ]
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'amount', 'tier', 'monthly_rate')
        }),
        ('Earnings Tracking', {
            'fields': (
                'total_earned', 'earnings_cap', 'earnings_percentage',
                'bonus_used'
            )
        }),
        ('Status', {
            'fields': (
                'is_active', 'started_at', 'completed_at', 'days_active'
            )
        }),
    )
