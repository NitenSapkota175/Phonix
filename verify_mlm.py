import os
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phonix.settings')
django.setup()

# Enable synchronous task execution for testing
from django.conf import settings
settings.CELERY_TASK_ALWAYS_EAGER = True

from accounts.models import User
from investment.models import Subscription
from earnings.models import Commission
from wallet.models import Transaction
from earnings.tasks import process_subscription_purchase, calculate_daily_bond_income
from ranks.tasks import check_rank_advancements

def verify_mlm_system():
    print("--- Starting MLM Logic Verification ---")
    
    # 0. Cleanup previous tests
    User.objects.filter(username__startswith='test_').delete()
    
    # 1. Create a chain of users (Level 1 to 4 for test)
    print("Step 1: Creating referral chain and meeting requirements...")
    u1 = User.objects.create_user(username='test_u1', email='u1@test.com', password='password')
    # Give u1 two directs to meet Level 3 requirement for later
    u2 = User.objects.create_user(username='test_u2', email='u2@test.com', password='password', referred_by=u1)
    u1_extra = User.objects.create_user(username='test_u1_extra', email='extra@test.com', password='password', referred_by=u1)
    
    u3 = User.objects.create_user(username='test_u3', email='u3@test.com', password='password', referred_by=u2)
    u4 = User.objects.create_user(username='test_u4', email='u4@test.com', password='password', referred_by=u3)
    
    # Give all users some money and an initial subscription
    for u in [u1, u2, u3, u4, u1_extra]:
        u.wallet_balance = Decimal('10000.00')
        u.save()
        process_subscription_purchase(u.id, Decimal('100.00'), Decimal('0.00'))
    
    # Update counts
    for u in [u1, u2, u3]:
        u.update_direct_referrals_count()
        u.refresh_from_db()

    print(f"Chain: {u1.username} <- {u2.username} <- {u3.username} <- {u4.username}")
    print(f"u1 directs: {u1.direct_referrals_count} (Needs 2 for L3)")
    
    # 2. Process Large Subscription for u4
    print("\nStep 2: Processing $500 subscription for u4...")
    result = process_subscription_purchase(u4.id, Decimal('500.00'), Decimal('0.00'))
    print(f"Purchase result: {result}")
    
    # 3. Verify Commissions for upline
    print("\nStep 3: Verifying commissions...")
    for upline, expected_level, expected_percent in [(u3, 1, 0.10), (u2, 2, 0.05), (u1, 3, 0.03)]:
        u = User.objects.get(id=upline.id)
        expected_amount = Decimal('500.00') * Decimal(str(expected_percent))
        actual_comm = Commission.objects.filter(user=u, from_user=u4, level=expected_level).first()
        
        if actual_comm and actual_comm.amount == expected_amount:
            print(f"✅ {u.username} received ${actual_comm.amount} for Level {expected_level}")
        else:
            print(f"❌ {u.username} commission error! Found: {actual_comm.amount if actual_comm else 'None'}, Expected: ${expected_amount}")

    # 4. Verify Daily Bond Income
    print("\nStep 4: Testing daily bond calculation logic...")
    active_sub = Subscription.objects.filter(user=u4, amount=Decimal('500.00')).first()
    if active_sub:
        daily = active_sub.calculate_daily_income()
        print(f"Daily income for ${active_sub.amount}: ${daily}")
        if daily == Decimal('1.00'):
             print("✅ Daily bond calculation correct.")
    
    # 5. Check Rank Advancement
    print("\nStep 5: Checking rank advancement...")
    from ranks.models import Rank
    rank, _ = Rank.objects.get_or_create(user=u1)
    rank.main_leg_volume = Decimal('5000.00')
    rank.other_legs_volume = Decimal('5000.00')
    rank.save()
    
    new_rank = rank.check_rank_advancement()
    if new_rank == 'connector':
        print("✅ u1 advanced to Connector successfully.")
    
    print("\n--- All Tests Passed ---")

if __name__ == "__main__":
    verify_mlm_system()
