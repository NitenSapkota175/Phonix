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
        amount = Decimal(request.POST.get('amount', '0'))
        use_bonus = request.POST.get('use_bonus') == 'on'
        
        user = request.user
        bonus_to_use = Decimal('0.00')
        
        if use_bonus:
            # Max 10% of amount or available bonus
            max_bonus = amount * Decimal('0.10')
            bonus_to_use = min(max_bonus, user.registration_bonus)
        
        # Process the purchase
        # In a real app, this would be a Celery task, but for now we call it directly or via delay
        # For simplicity in this step, we'll try to call the task logic
        result = process_subscription_purchase(user.id, amount, bonus_to_use)
        
        if result['status'] == 'success':
            messages.success(request, result['message'])
            return redirect('investment:list')
        else:
            messages.error(request, result['message'])
            
    return redirect('investment:list')
