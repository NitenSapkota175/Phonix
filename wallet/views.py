from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from .models import Transaction, DepositAddress

@login_required
def wallet_history(request):
    """View to show transaction history"""
    transactions = request.user.transactions.all()
    return render(request, 'wallet/history.html', {'transactions': transactions})

@login_required
def deposit(request):
    """View to handle deposits (mockup with manual address)"""
    user = request.user
    
    # Get or create a mock deposit address
    deposit_addr, created = DepositAddress.objects.get_or_create(
        user=user,
        defaults={'address': f'T{user.username.upper()}MOCKADDRESSPAYMENT'}
    )
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', '0'))
        txn_hash = request.POST.get('txn_hash', '').strip()
        
        if amount < 10:
            messages.error(request, "Minimum deposit is $10")
        elif not txn_hash:
            messages.error(request, "Transaction hash is required")
        else:
            # Create a pending transaction
            Transaction.objects.create(
                user=user,
                type=Transaction.DEPOSIT,
                amount=amount,
                net_amount=amount,
                txn_hash=txn_hash,
                wallet_address=deposit_addr.address,
                status=Transaction.PENDING,
                description="Manual USDT TRC20 Deposit"
            )
            messages.info(request, "Deposit submitted and is now pending verification.")
            return redirect('wallet:history')
            
    return render(request, 'wallet/deposit.html', {'deposit_address': deposit_addr.address})

@login_required
def withdraw(request):
    """View to handle withdrawals"""
    user = request.user
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', '0'))
        address = request.POST.get('wallet_address', '').strip()
        
        if not address:
            messages.error(request, "Withdrawal address is required")
            return redirect('wallet:withdraw')
            
        fee = Transaction.calculate_withdrawal_fee(amount)
        total_needed = amount
        
        if total_needed > user.wallet_balance:
            messages.error(request, "Insufficient wallet balance")
        elif amount < 20:
            messages.error(request, "Minimum withdrawal is $20")
        else:
            # Deduct balance immediately (or mark as processing)
            user.wallet_balance -= total_needed
            user.save()
            
            # Create transaction
            Transaction.objects.create(
                user=user,
                type=Transaction.WITHDRAWAL,
                amount=amount,
                fee=fee,
                net_amount=amount - fee,
                wallet_address=address,
                status=Transaction.PENDING,
                description=f"Withdrawal to {address}"
            )
            messages.success(request, f"Withdrawal request for ${amount} submitted successfully.")
            return redirect('wallet:history')
            
    return render(request, 'wallet/withdraw.html', {'user': user})
