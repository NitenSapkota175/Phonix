"""
Dashboard view — aggregated stats with Redis caching.
Avoid N+1 queries using select_related/prefetch_related + aggregate.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Sum
from django.views import View
from django.shortcuts import render

from apps.wallets.models import Wallet
from apps.transactions.models import Transaction
from apps.incomes.models import Income


DASHBOARD_CACHE_TTL = 300  # 5 minutes


class DashboardView(LoginRequiredMixin, View):
    template_name = 'dashboard/index.html'

    def get(self, request):
        ctx = self._get_context(request.user)
        return render(request, self.template_name, ctx)

    @staticmethod
    def _get_context(user):
        cache_key = f'dashboard:{user.pk}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        # All wallets in one query
        wallets = {
            w.wallet_type: w
            for w in Wallet.objects.filter(user=user)
        }

        # Binary tree volumes
        try:
            node = user.binary_node
            left_vol = node.left_volume
            right_vol = node.right_volume
            power_leg = max(left_vol, right_vol)
            other_leg = min(left_vol, right_vol)
            total_team = left_vol + right_vol
        except Exception:
            left_vol = right_vol = power_leg = other_leg = total_team = 0

        # Income aggregations (single query)
        income_totals = Income.objects.filter(user=user).aggregate(
            total=Sum('amount'),
        )
        total_income = income_totals['total'] or 0

        # Trade stats
        from apps.trading.models import Trade
        trade_agg = Trade.objects.filter(user=user, is_active=True).aggregate(total=Sum('amount'))
        total_trade = trade_agg['total'] or 0

        # Withdrawal stats
        withdrawal_agg = Transaction.objects.filter(
            user=user,
            txn_type=Transaction.TxnType.WITHDRAWAL,
            status=Transaction.TxnStatus.COMPLETED,
        ).aggregate(total=Sum('net_amount'))
        total_withdrawals = withdrawal_agg['total'] or 0

        # Top 10 transactions — single query, no N+1
        top_transactions = (
            Transaction.objects
            .filter(user=user)
            .select_related('wallet')
            .only('txn_type', 'amount', 'status', 'created_at', 'wallet__wallet_type')
            .order_by('-created_at')[:10]
        )

        # Direct referral team size
        directs = user.direct_referrals.count()

        ctx = {
            'wallets': wallets,
            'main_wallet': wallets.get('main'),
            'trade_wallet': wallets.get('trade'),
            'affiliate_wallet': wallets.get('affiliate'),
            'total_trade': total_trade,
            'total_withdrawal': total_withdrawals,
            'total_team_volume': total_team,
            'direct_team_count': directs,
            'power_leg': power_leg,
            'other_leg': other_leg,
            'total_income': total_income,
            'top_transactions': list(top_transactions),
            'referral_link': user.get_referral_link(request=None),
        }

        cache.set(cache_key, ctx, DASHBOARD_CACHE_TTL)
        return ctx
