from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from .models import Subscription
from earnings.tasks import process_subscription_purchase


@login_required
def subscription_list(request):
    """View to list all available tiers and user's subscriptions"""
    user = request.user
    subscriptions = user.subscriptions.all()

    context = {
        'user': user,
        'subscriptions': subscriptions,
        'tiers': [
            {'name': 'Tier 1', 'range': '$50 - $3,000', 'rate': '6%'},
            {'name': 'Tier 2', 'range': '$3,001 - $5,000', 'rate': '8%'},
            {'name': 'Tier 3', 'range': '$5,001+', 'rate': '10%'},
        ]
    }
    return render(request, 'investment/list.html', context)


@login_required
def buy_subscription(request):
    """View to handle subscription purchase"""
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except Exception:
            messages.error(request, "Invalid amount entered.")
            return redirect('investment:list')

        use_bonus = request.POST.get('use_bonus') == 'on'
        user = request.user
        bonus_to_use = Decimal('0.00')

        if amount < Decimal('50'):
            messages.error(request, "Minimum investment is $50.")
            return redirect('investment:list')

        if use_bonus and user.registration_bonus > 0:
            # Max 10% of amount or $1, whichever is smaller
            max_bonus = min(amount * Decimal('0.10'), Decimal('1.00'))
            bonus_to_use = min(max_bonus, user.registration_bonus)

        total_needed = amount - bonus_to_use
        if total_needed > user.wallet_balance:
            messages.error(request, f"Insufficient balance. You need ${total_needed:.2f} but have ${user.wallet_balance:.2f}.")
            return redirect('investment:list')

        # Call the task directly (synchronously) since Celery may not be running in dev
        # In production with Celery running, change to: process_subscription_purchase.delay(...)
        result = process_subscription_purchase(user.id, float(amount), float(bonus_to_use))

        if result.get('status') == 'success':
            messages.success(request, f"Investment of ${amount} activated successfully! Commissions are being distributed.")
        else:
            messages.error(request, result.get('message', 'An error occurred. Please try again.'))

    return redirect('investment:list')
