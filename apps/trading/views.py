"""
Trading views — list trades and activate new trade packages.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View

from apps.core.mixins import ServiceExceptionMixin
from apps.wallets.models import Wallet
from apps.wallets.services import WalletService
from .models import Trade
from .services import TradeService


class TradeListView(LoginRequiredMixin, View):
    template_name = 'trading/list.html'

    def get(self, request):
        active_trades = Trade.objects.filter(user=request.user, is_active=True)
        completed_trades = Trade.objects.filter(user=request.user, is_active=False)
        trade_wallet = WalletService.get_wallet(request.user, Wallet.WalletType.TRADE)
        ctx = {
            'active_trades': active_trades,
            'completed_trades': completed_trades,
            'trade_wallet': trade_wallet,
            'tier_config': Trade.TIER_CONFIG,
        }
        return render(request, self.template_name, ctx)


class TradeActivateView(ServiceExceptionMixin, LoginRequiredMixin, View):
    template_name = 'trading/activate.html'

    def get(self, request):
        trade_wallet = WalletService.get_wallet(request.user, Wallet.WalletType.TRADE)
        return render(request, self.template_name, {
            'trade_wallet': trade_wallet,
            'tier_config': Trade.TIER_CONFIG,
        })

    def post(self, request):
        amount = request.POST.get('amount', '0')
        txn_password = request.POST.get('transaction_password', '')
        trade = TradeService.activate(request.user, amount, txn_password)
        messages.success(request, f'Trade package activated: ${trade.amount} ({trade.get_tier_display()})')
        return redirect('trading:list')
