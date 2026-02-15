from django.contrib import admin
from .models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    """Admin interface for Commission model"""
    
    list_display = [
        'user', 'from_user', 'level', 'amount',
        'commission_type', 'paid_at'
    ]
    
    list_filter = ['commission_type', 'level', 'paid_at']
    
    search_fields = ['user__username', 'from_user__username']
    
    readonly_fields = ['paid_at']
    
    fieldsets = (
        ('Commission Details', {
            'fields': (
                'user', 'from_user', 'level', 'amount', 'commission_type'
            )
        }),
        ('Source', {
            'fields': ('source_subscription', 'description')
        }),
        ('Timestamp', {
            'fields': ('paid_at',)
        }),
    )
