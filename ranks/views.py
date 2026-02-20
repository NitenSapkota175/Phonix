from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from wallet.models import Transaction


@login_required
def rank_dashboard(request):
    """Rank advancement and weekly bonus dashboard"""
    user = request.user

    try:
        rank = user.rank
    except Exception:
        rank = None

    # Rank tier definitions for display
    rank_tiers = [
        {'key': 'connector', 'name': 'Connector', 'icon': 'plug', 'main_leg': '5,000', 'other_legs': '5,000', 'bonus': '50', 'weeks': 4},
        {'key': 'builder', 'name': 'Builder', 'icon': 'hammer', 'main_leg': '10,000', 'other_legs': '10,000', 'bonus': '200', 'weeks': 4},
        {'key': 'professional', 'name': 'Professional', 'icon': 'briefcase', 'main_leg': '20,000', 'other_legs': '20,000', 'bonus': '500', 'weeks': 4},
        {'key': 'executive', 'name': 'Executive', 'icon': 'star', 'main_leg': '50,000', 'other_legs': '50,000', 'bonus': '1,000', 'weeks': 4},
        {'key': 'director', 'name': 'Director', 'icon': 'chess-king', 'main_leg': '100,000', 'other_legs': '100,000', 'bonus': '2,000', 'weeks': 4},
        {'key': 'crown', 'name': 'Crown', 'icon': 'crown', 'main_leg': '200,000', 'other_legs': '200,000', 'bonus': '5,000', 'weeks': 4},
    ]

    # Get weekly bonus transaction history
    bonus_history = user.transactions.filter(type=Transaction.WEEKLY_BONUS).order_by('-created_at')[:20]

    context = {
        'user': user,
        'rank': rank,
        'rank_tiers': rank_tiers,
        'bonus_history': bonus_history,
    }
    return render(request, 'ranks/dashboard.html', context)
