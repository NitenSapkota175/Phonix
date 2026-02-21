"""
Admin configuration for the wallets app.
"""
from django.contrib import admin
from .models import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet_type', 'balance', 'total_deposited',
                    'total_withdrawn', 'total_earned', 'earnings_cap')
    list_filter = ('wallet_type',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('balance', 'total_deposited', 'total_withdrawn',
                       'total_earned', 'created_at', 'updated_at')
    list_select_related = ('user',)
