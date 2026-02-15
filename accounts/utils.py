"""
Utility functions for managing the MLM referral tree structure.
"""


def get_upline_chain(user, levels=20):
    """
    Get the upline chain for a user up to specified levels.
    
    Args:
        user: User instance
        levels: Number of levels to traverse (default 20 for MLM)
    
    Returns:
        List of tuples: [(level, user_instance), ...]
        Example: [(1, User1), (2, User2), ..., (20, User20)]
    """
    upline_chain = []
    current_user = user.referred_by
    level = 1
    
    while current_user and level <= levels:
        upline_chain.append((level, current_user))
        current_user = current_user.referred_by
        level += 1
    
    return upline_chain


def get_direct_referrals(user):
    """
    Get all direct referrals (Level 1) for a user.
    
    Args:
        user: User instance
    
    Returns:
        QuerySet of User instances
    """
    return user.referrals.all()


def get_downline_count(user, max_levels=20):
    """
    Count total number of users in downline up to max_levels.
    Uses recursive approach to count all descendants.
    
    Args:
        user: User instance
        max_levels: Maximum depth to traverse
    
    Returns:
        Integer count of total downline members
    """
    def count_recursive(current_user, current_level):
        if current_level > max_levels:
            return 0
        
        direct_refs = current_user.referrals.all()
        count = direct_refs.count()
        
        for ref in direct_refs:
            count += count_recursive(ref, current_level + 1)
        
        return count
    
    return count_recursive(user, 1)


def count_leg_volumes(user):
    """
    Calculate main leg volume vs other legs volume for rank advancement.
    
    Main Leg = The leg with the highest total investment volume
    Other Legs = Sum of all other legs
    
    Args:
        user: User instance
    
    Returns:
        Dictionary: {
            'main_leg_volume': Decimal,
            'other_legs_volume': Decimal,
            'leg_breakdown': [
                {'user': User, 'volume': Decimal},
                ...
            ]
        }
    """
    from decimal import Decimal
    from investment.models import Subscription
    
    direct_referrals = get_direct_referrals(user)
    leg_volumes = []
    
    for referral in direct_referrals:
        # Calculate total volume for this leg (referral + their downline)
        leg_volume = calculate_leg_volume(referral)
        leg_volumes.append({
            'user': referral,
            'volume': leg_volume
        })
    
    # Sort legs by volume (descending)
    leg_volumes.sort(key=lambda x: x['volume'], reverse=True)
    
    if not leg_volumes:
        return {
            'main_leg_volume': Decimal('0.00'),
            'other_legs_volume': Decimal('0.00'),
            'leg_breakdown': []
        }
    
    main_leg_volume = leg_volumes[0]['volume']
    other_legs_volume = sum(leg['volume'] for leg in leg_volumes[1:])
    
    return {
        'main_leg_volume': main_leg_volume,
        'other_legs_volume': other_legs_volume,
        'leg_breakdown': leg_volumes
    }


def calculate_leg_volume(user):
    """
    Calculate total investment volume for a user and their entire downline.
    
    Args:
        user: User instance
    
    Returns:
        Decimal: Total investment volume
    """
    from decimal import Decimal
    from investment.models import Subscription
    
    def get_volume_recursive(current_user):
        # Get user's own subscriptions
        user_volume = Subscription.objects.filter(
            user=current_user
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Add downline volumes
        downline_volume = Decimal('0.00')
        for referral in current_user.referrals.all():
            downline_volume += get_volume_recursive(referral)
        
        return user_volume + downline_volume
    
    return get_volume_recursive(user)


def get_level_members(user, level):
    """
    Get all users at a specific level in the downline.
    
    Args:
        user: User instance
        level: Level number (1 = direct referrals, 2 = their referrals, etc.)
    
    Returns:
        List of User instances at that level
    """
    if level == 1:
        return list(user.referrals.all())
    
    members = []
    current_level_members = list(user.referrals.all())
    
    for i in range(2, level + 1):
        next_level_members = []
        for member in current_level_members:
            next_level_members.extend(member.referrals.all())
        current_level_members = next_level_members
    
    return current_level_members


def check_direct_requirement(user, required_directs):
    """
    Check if user meets the direct referral requirement.
    
    Args:
        user: User instance
        required_directs: Number of direct referrals required
    
    Returns:
        Boolean: True if requirement is met
    """
    return user.direct_referrals_count >= required_directs


def get_genealogy_tree(user, max_depth=5):
    """
    Get a structured genealogy tree for display purposes.
    Limited to max_depth to avoid performance issues.
    
    Args:
        user: User instance
        max_depth: Maximum depth to traverse
    
    Returns:
        Dictionary representing the tree structure
    """
    def build_tree(current_user, current_depth):
        if current_depth > max_depth:
            return None
        
        node = {
            'user': current_user,
            'username': current_user.username,
            'email': current_user.email,
            'total_invested': current_user.total_invested,
            'is_active': current_user.is_active_investor,
            'children': []
        }
        
        for referral in current_user.referrals.all()[:10]:  # Limit to 10 per level
            child_node = build_tree(referral, current_depth + 1)
            if child_node:
                node['children'].append(child_node)
        
        return node
    
    return build_tree(user, 1)
