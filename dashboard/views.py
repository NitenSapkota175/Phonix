from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

from accounts.models import User
from accounts.utils import get_downline_count
from investment.models import Subscription
from wallet.models import Transaction
from earnings.models import Commission
from ranks.models import Rank


@login_required
def dashboard(request):
    """Main dashboard view"""
    user = request.user
    
    # Get active subscriptions
    active_subscriptions = user.subscriptions.filter(is_active=True)
    completed_subscriptions = user.subscriptions.filter(is_active=False)
    
    # Get recent transactions
    recent_transactions = user.transactions.all()[:10]
    
    # Get recent commissions
    recent_commissions = user.commissions_received.all()[:10]
    
    # Get rank info
    try:
        rank = user.rank
    except Rank.DoesNotExist:
        rank = None
    
    # Calculate statistics
    total_active_investment = active_subscriptions.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_earnings_this_month = user.commissions_received.filter(
        paid_at__month=timezone.now().month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'user': user,
        'active_subscriptions': active_subscriptions,
        'completed_subscriptions': completed_subscriptions,
        'recent_transactions': recent_transactions,
        'recent_commissions': recent_commissions,
        'rank': rank,
        'total_active_investment': total_active_investment,
        'total_earnings_this_month': total_earnings_this_month,
        'referral_link': user.get_referral_link(request),
    }
    
    return render(request, 'dashboard/index.html', context)

@login_required
def network(request):
    """View to show MLM downline network"""
    user = request.user
    
    # Calculate members per level (up to 20)
    level_stats = []
    from accounts.utils import get_level_members
    
    for lvl in range(1, 21):
        members = get_level_members(user, lvl)
        if not members and lvl > 3: # Stop after level 3 if no more members to avoid extra work
            break
        level_stats.append({
            'level': lvl,
            'count': len(members),
            'members': members[:50] # Limit display to first 50 per level
        })
    
    context = {
        'user': user,
        'level_stats': level_stats,
        'total_network': sum(s['count'] for s in level_stats)
    }
    return render(request, 'dashboard/network.html', context)


@login_required
def profile(request):
    """User profile view"""
    user = request.user
    
    # Get referral statistics
    direct_referrals = user.referrals.all()
    total_network = get_downline_count(user)
    
    context = {
        'user': user,
        'direct_referrals': direct_referrals,
        'total_network': total_network,
        'referral_link': user.get_referral_link(request),
    }
    
    return render(request, 'dashboard/profile.html', context)


def register(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        referral_code = request.POST.get('referral_code', '').strip()
        
        # Validation
        if password != password2:
            messages.error(request, "Passwords do not match")
            return render(request, 'dashboard/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'dashboard/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render(request, 'dashboard/register.html')
        
        # Get referrer if code provided
        referred_by = None
        if referral_code:
            try:
                referred_by = User.objects.get(referral_code=referral_code)
            except User.DoesNotExist:
                messages.error(request, "Invalid referral code")
                return render(request, 'dashboard/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            referred_by=referred_by
        )
        
        # Update referrer's direct count
        if referred_by:
            referred_by.update_direct_referrals_count()
        
        # Log user in
        login(request, user)
        messages.success(request, f"Welcome to Phonix! You have received a $10 registration bonus.")
        
        return redirect('dashboard:index')
    
    # GET request - check for referral code in URL
    referral_code = request.GET.get('ref', '')
    
    return render(request, 'dashboard/register.html', {'referral_code': referral_code})


def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard:index')
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, 'dashboard/login.html')
