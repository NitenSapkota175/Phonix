from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from decimal import Decimal, InvalidOperation
from .models import Transaction, DepositAddress
from accounts.email_utils import send_deposit_confirmation, send_withdrawal_processed


@login_required
def wallet_history(request):
    """View to show transaction history with pagination"""
    transactions_qs = request.user.transactions.all()
    paginator = Paginator(transactions_qs, 20)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)
    return render(request, 'wallet/history.html', {'transactions': transactions})


@login_required
def deposit(request):
    """View to handle deposits - shows the master TRC20 deposit address"""
    user = request.user

    # Use the master wallet address for all deposits
    # Users send USDT TRC20 to this address and submit their txn hash for verification
    from django.conf import settings
    MASTER_DEPOSIT_ADDRESS = getattr(settings, 'MASTER_WALLET_ADDRESS', 'TSn6B3s6KoQh9e5T18Ph3Gg6xu62ZMQzh1')
    if not MASTER_DEPOSIT_ADDRESS:
        MASTER_DEPOSIT_ADDRESS = 'TSn6B3s6KoQh9e5T18Ph3Gg6xu62ZMQzh1'

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (InvalidOperation, ValueError):
            messages.error(request, "Invalid amount entered.")
            return render(request, 'wallet/deposit.html', {'deposit_address': MASTER_DEPOSIT_ADDRESS, 'user': user})

        txn_hash = request.POST.get('txn_hash', '').strip()

        if amount < Decimal('10'):
            messages.error(request, "Minimum deposit is $10 USDT.")
        elif not txn_hash:
            messages.error(request, "Transaction hash is required for verification.")
        elif Transaction.objects.filter(txn_hash=txn_hash).exists():
            messages.error(request, "This transaction hash has already been submitted.")
        else:
            # Create a pending transaction — admin will verify on blockchain and approve
            Transaction.objects.create(
                user=user,
                type=Transaction.DEPOSIT,
                amount=amount,
                net_amount=amount,
                txn_hash=txn_hash,
                wallet_address=MASTER_DEPOSIT_ADDRESS,
                status=Transaction.PENDING,
                description="USDT TRC20 Deposit - Pending Admin Verification"
            )
            messages.info(request, f"Deposit of ${amount} USDT submitted. Your wallet will be credited once the transaction is verified on the blockchain.")
            return redirect('wallet:history')

    return render(request, 'wallet/deposit.html', {
        'deposit_address': MASTER_DEPOSIT_ADDRESS,
        'user': user,
    })


@login_required
def withdraw(request):
    """View to handle withdrawals"""
    user = request.user

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (InvalidOperation, ValueError):
            messages.error(request, "Invalid amount entered.")
            return render(request, 'wallet/withdraw.html', {'user': user})

        address = request.POST.get('wallet_address', '').strip()

        # Validate address
        if not address:
            messages.error(request, "Withdrawal address is required.")
            return render(request, 'wallet/withdraw.html', {'user': user})

        if not (address.startswith('T') and len(address) >= 34):
            messages.error(request, "Invalid TRC20 address. Must start with 'T' and be at least 34 characters.")
            return render(request, 'wallet/withdraw.html', {'user': user})

        if amount < Decimal('20'):
            messages.error(request, "Minimum withdrawal is $20 USDT.")
            return render(request, 'wallet/withdraw.html', {'user': user})

        fee = Transaction.calculate_withdrawal_fee(amount)
        net_amount = amount - fee

        if amount > user.wallet_balance:
            messages.error(request, f"Insufficient balance. You have ${user.wallet_balance:.2f} available.")
            return render(request, 'wallet/withdraw.html', {'user': user})

        # Deduct balance and create transaction
        user.wallet_balance -= amount
        user.save()

        txn = Transaction.objects.create(
            user=user,
            type=Transaction.WITHDRAWAL,
            amount=amount,
            fee=fee,
            net_amount=net_amount,
            wallet_address=address,
            status=Transaction.PENDING,
            description=f"Withdrawal to {address[:10]}...{address[-6:]}"
        )

        messages.success(request, f"Withdrawal request for ${amount} (net: ${net_amount:.2f} after 5% fee) submitted. Processing within 24 hours.")
        return redirect('wallet:history')

    return render(request, 'wallet/withdraw.html', {'user': user})
