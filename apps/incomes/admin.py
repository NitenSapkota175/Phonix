"""
Admin configuration for the incomes app.
"""
from django.contrib import admin
from .models import Income


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('user', 'income_type', 'amount', 'wallet_type',
                    'source_user', 'level', 'created_at')
    list_filter = ('income_type', 'wallet_type')
    search_fields = ('user__username', 'user__email', 'source_user__username')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'source_user')
