"""
Wallet views — overview, deposit, withdrawal, swap, internal transfer.
Business logic delegated to WalletService.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View

from apps.core.mixins import ServiceExceptionMixin
from .models import Wallet
from .services import WalletService


class WalletOverviewView(LoginRequiredMixin, View):
    template_name = 'wallets/overview.html'

    def get(self, request):
        wallets = {
            w.wallet_type: w
            for w in Wallet.objects.filter(user=request.user)
        }
        ctx = {
            'main_wallet': wallets.get('main'),
            'trade_wallet': wallets.get('trade'),
            'affiliate_wallet': wallets.get('affiliate'),
        }
        return render(request, self.template_name, ctx)


class DepositView(ServiceExceptionMixin, LoginRequiredMixin, View):
    template_name = 'wallets/deposit.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        amount = request.POST.get('amount', '0')
        reference = request.POST.get('reference', '').strip()
        txn = WalletService.request_deposit(request.user, amount, reference)
        messages.success(request, f'Deposit request of ${txn.amount} submitted. Awaiting admin approval.')
        return redirect('wallets:overview')


class WithdrawView(ServiceExceptionMixin, LoginRequiredMixin, View):
    template_name = 'wallets/withdraw.html'

    def get(self, request):
        wallet = WalletService.get_wallet(request.user, Wallet.WalletType.MAIN)
        return render(request, self.template_name, {'wallet': wallet})

    def post(self, request):
        amount = request.POST.get('amount', '0')
        txn_password = request.POST.get('transaction_password', '')
        txn = WalletService.request_withdrawal(request.user, amount, txn_password)
        messages.success(
            request,
            f'Withdrawal of ${txn.amount} submitted (fee: ${txn.fee}). Awaiting admin approval.'
        )
        return redirect('wallets:overview')


class SwapView(ServiceExceptionMixin, LoginRequiredMixin, View):
    template_name = 'wallets/swap.html'

    def get(self, request):
        main = WalletService.get_wallet(request.user, Wallet.WalletType.MAIN)
        trade = WalletService.get_wallet(request.user, Wallet.WalletType.TRADE)
        return render(request, self.template_name, {
            'main_wallet': main,
            'trade_wallet': trade,
        })

    def post(self, request):
        amount = request.POST.get('amount', '0')
        txn_password = request.POST.get('transaction_password', '')
        WalletService.swap(request.user, amount, txn_password)
        messages.success(request, f'Swapped ${amount} from Main Wallet to Trade Wallet.')
        return redirect('wallets:overview')


class TransferView(ServiceExceptionMixin, LoginRequiredMixin, View):
    template_name = 'wallets/transfer.html'

    def get(self, request):
        wallets = {
            w.wallet_type: w
            for w in Wallet.objects.filter(user=request.user)
        }
        return render(request, self.template_name, {'wallets': wallets})

    def post(self, request):
        from_type = request.POST.get('from_wallet', '')
        to_type = request.POST.get('to_wallet', '')
        amount = request.POST.get('amount', '0')
        txn_password = request.POST.get('transaction_password', '')
        WalletService.internal_transfer(request.user, from_type, to_type, amount, txn_password)
        messages.success(request, f'Transferred ${amount} successfully.')
        return redirect('wallets:overview')
