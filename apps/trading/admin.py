"""
Admin configuration for the trading app.
"""
from django.contrib import admin
from .models import Trade


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'amount', 'monthly_rate', 'total_earned',
                    'earnings_cap', 'is_active', 'activated_at')
    list_filter = ('tier', 'is_active')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('total_earned', 'activated_at', 'completed_at',
                       'created_at', 'updated_at')
    list_select_related = ('user',)
