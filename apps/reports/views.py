"""
Report views — user income/stats reports and admin platform overview.
"""
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View

from apps.accounts.models import User
from apps.incomes.models import Income
from apps.trading.models import Trade
from apps.transactions.models import Transaction
from apps.wallets.models import Wallet
from apps.referral.models import BinaryNode


class UserReportView(LoginRequiredMixin, View):
    template_name = 'reports/user_report.html'

    def get(self, request):
        user = request.user

        # Income breakdown by type
        income_by_type = (
            Income.objects.filter(user=user)
            .values('income_type')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )

        # Trade stats
        trade_stats = Trade.objects.filter(user=user).aggregate(
            total_invested=Sum('amount'),
            total_earned=Sum('total_earned'),
            active_count=Count('id', filter=Q(is_active=True)),
            completed_count=Count('id', filter=Q(is_active=False)),
        )

        # Wallet balances
        wallets = {
            w.wallet_type: w
            for w in Wallet.objects.filter(user=user)
        }

        # Transaction summary
        txn_summary = Transaction.objects.filter(user=user).aggregate(
            total_deposits=Sum('amount', filter=Q(
                txn_type=Transaction.TxnType.DEPOSIT,
                status=Transaction.TxnStatus.COMPLETED)),
            total_withdrawals=Sum('net_amount', filter=Q(
                txn_type=Transaction.TxnType.WITHDRAWAL,
                status=Transaction.TxnStatus.COMPLETED)),
        )

        # Referral stats
        try:
            node = user.binary_node
            binary_stats = {
                'left_volume': node.left_volume,
                'right_volume': node.right_volume,
                'power_leg': node.power_leg_volume,
                'other_leg': node.other_leg_volume,
                'total_team': node.total_team_volume,
            }
        except BinaryNode.DoesNotExist:
            binary_stats = {}

        ctx = {
            'income_by_type': income_by_type,
            'trade_stats': trade_stats,
            'wallets': wallets,
            'txn_summary': txn_summary,
            'binary_stats': binary_stats,
            'direct_referrals': user.direct_referrals_count,
        }
        return render(request, self.template_name, ctx)


class AdminReportView(LoginRequiredMixin, View):
    template_name = 'reports/admin_report.html'

    def get(self, request):
        if not request.user.is_admin_role:
            messages.error(request, 'You do not have permission to view admin reports.')
            return redirect('dashboard:index')

        # Platform totals
        total_users = User.objects.count()
        active_investors = User.objects.filter(is_active_investor=True).count()
        verified_users = User.objects.filter(is_email_verified=True).count()

        # Trade totals
        trade_totals = Trade.objects.aggregate(
            total_invested=Sum('amount'),
            total_roi_paid=Sum('total_earned'),
            active_trades=Count('id', filter=Q(is_active=True)),
        )

        # Income totals
        total_income_paid = Income.objects.aggregate(total=Sum('amount'))['total'] or 0

        # Volume stats
        volume_stats = BinaryNode.objects.aggregate(
            total_left=Sum('left_volume'),
            total_right=Sum('right_volume'),
        )

        # Transaction totals
        txn_totals = Transaction.objects.aggregate(
            total_deposits=Sum('amount', filter=Q(
                txn_type=Transaction.TxnType.DEPOSIT,
                status=Transaction.TxnStatus.COMPLETED)),
            total_withdrawals=Sum('net_amount', filter=Q(
                txn_type=Transaction.TxnType.WITHDRAWAL,
                status=Transaction.TxnStatus.COMPLETED)),
            pending_deposits=Count('id', filter=Q(
                txn_type=Transaction.TxnType.DEPOSIT,
                status=Transaction.TxnStatus.PENDING)),
            pending_withdrawals=Count('id', filter=Q(
                txn_type=Transaction.TxnType.WITHDRAWAL,
                status=Transaction.TxnStatus.PENDING)),
        )

        ctx = {
            'total_users': total_users,
            'active_investors': active_investors,
            'verified_users': verified_users,
            'trade_totals': trade_totals,
            'total_income_paid': total_income_paid,
            'volume_stats': volume_stats,
            'txn_totals': txn_totals,
        }
        return render(request, self.template_name, ctx)
