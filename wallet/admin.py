"""
Admin approval actions and customizations for wallet transactions.
"""
from django.contrib import admin, messages
from django.utils.html import format_html
from .models import Transaction, DepositAddress


def approve_deposit(modeladmin, request, queryset):
    """Admin action to approve pending deposits"""
    updated = 0
    for transaction in queryset.filter(type=Transaction.DEPOSIT, status=Transaction.PENDING):
        # Credit user wallet
        user = transaction.user
        user.wallet_balance += transaction.net_amount
        user.save()
        
        # Mark transaction as completed
        transaction.mark_completed()
        updated += 1
    
    messages.success(request, f'{updated} deposit(s) approved successfully.')

approve_deposit.short_description = "Approve selected deposits"


def reject_transaction(modeladmin, request, queryset):
    """Admin action to reject pending transactions"""
    updated = 0
    for transaction in queryset.filter(status=Transaction.PENDING):
        # For withdrawals, refund the amount back to user
        if transaction.type == Transaction.WITHDRAWAL:
            user = transaction.user
            user.wallet_balance += transaction.amount  # Refund full amount
            user.save()
        
        # Mark as failed
        transaction.mark_failed("Rejected by admin")
        updated += 1
    
    messages.warning(request, f'{updated} transaction(s) rejected.')

reject_transaction.short_description = "Reject selected transactions"


def approve_withdrawal(modeladmin, request, queryset):
    """Admin action to approve pending withdrawals (mark for processing)"""
    updated = 0
    for transaction in queryset.filter(type=Transaction.WITHDRAWAL, status=Transaction.PENDING):
        # Change status to processing (admin will send crypto manually)
        transaction.status = Transaction.PROCESSING
        transaction.save()
        updated += 1
    
    messages.info(request, f'{updated} withdrawal(s) marked for processing.')

approve_withdrawal.short_description = "Approve selected withdrawals (mark for processing)"


def mark_withdrawal_complete(modeladmin, request, queryset):
    """Admin action to mark withdrawals as completed after sending crypto"""
    updated = 0
    for transaction in queryset.filter(type=Transaction.WITHDRAWAL, status=Transaction.PROCESSING):
        transaction.mark_completed()
        updated += 1
    
    messages.success(request, f'{updated} withdrawal(s) marked as completed.')

mark_withdrawal_complete.short_description = "Mark withdrawals as completed"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'type', 'amount_display', 'fee', 'net_amount', 
        'status_badge', 'created_at', 'txn_hash_short'
    ]
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['user__username', 'user__email', 'txn_hash', 'wallet_address', 'description']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'net_amount']
    actions = [approve_deposit, approve_withdrawal, mark_withdrawal_complete, reject_transaction]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'type', 'amount', 'fee', 'net_amount', 'status')
        }),
        ('Crypto Details', {
            'fields': ('txn_hash', 'wallet_address'),
            'classes': ('collapse',),
        }),
        ('Related Objects', {
            'fields': ('subscription',),
            'classes': ('collapse',),
        }),
        ('Additional Info', {
            'fields': ('description',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )
    
    def amount_display(self, obj):
        """Display amount with color coding"""
        if obj.type in [Transaction.DEPOSIT, Transaction.COMMISSION, Transaction.DAILY_INCOME, Transaction.WEEKLY_BONUS]:
            return format_html('<span style="color: green; font-weight: bold;">${}</span>', obj.amount)
        else:
            return format_html('<span style="color: red; font-weight: bold;">${}</span>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            Transaction.COMPLETED: 'green',
            Transaction.PENDING: 'orange',
            Transaction.PROCESSING: 'blue',
            Transaction.FAILED: 'red',
            Transaction.CANCELLED: 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def txn_hash_short(self, obj):
        """Display shortened transaction hash"""
        if obj.txn_hash:
            return obj.txn_hash[:16] + '...' if len(obj.txn_hash) > 16 else obj.txn_hash
        return '-'
    txn_hash_short.short_description = 'Txn Hash'


@admin.register(DepositAddress)
class DepositAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address', 'created_at']
    search_fields = ['user__username', 'address']
    readonly_fields = ['created_at']
