"""
Admin configuration for the transactions app.
Custom admin actions for deposit/withdrawal approval.
"""
from django.contrib import admin
from django.utils import timezone
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'txn_type', 'amount', 'fee', 'net_amount',
                    'status', 'wallet', 'created_at')
    list_filter = ('txn_type', 'status')
    search_fields = ('user__username', 'user__email', 'description')
    readonly_fields = ('amount', 'fee', 'net_amount', 'created_at',
                       'updated_at', 'approved_at')
    list_select_related = ('user', 'wallet', 'approved_by')
    actions = ['approve_transactions', 'reject_transactions']

    @admin.action(description='Approve selected pending transactions')
    def approve_transactions(self, request, queryset):
        from apps.wallets.services import WalletService
        count = 0
        for txn in queryset.filter(status=Transaction.TxnStatus.PENDING):
            try:
                if txn.txn_type == Transaction.TxnType.DEPOSIT:
                    WalletService.approve_deposit(txn, request.user)
                elif txn.txn_type == Transaction.TxnType.WITHDRAWAL:
                    WalletService.approve_withdrawal(txn, request.user)
                count += 1
            except Exception:
                continue
        self.message_user(request, f'{count} transaction(s) approved.')

    @admin.action(description='Reject selected pending transactions')
    def reject_transactions(self, request, queryset):
        from apps.wallets.services import WalletService
        count = 0
        for txn in queryset.filter(status=Transaction.TxnStatus.PENDING):
            try:
                if txn.txn_type == Transaction.TxnType.WITHDRAWAL:
                    WalletService.reject_withdrawal(txn, request.user)
                else:
                    txn.status = Transaction.TxnStatus.CANCELLED
                    txn.approved_by = request.user
                    txn.approved_at = timezone.now()
                    txn.save(update_fields=['status', 'approved_by', 'approved_at'])
                count += 1
            except Exception:
                continue
        self.message_user(request, f'{count} transaction(s) rejected.')
