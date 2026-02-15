"""
Demo script to showcase the Phonix MLM platform features.
This script will add test data to demonstrate the platform functionality.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phonix.settings')
django.setup()

from accounts.models import User
from investment.models import Subscription
from wallet.models import Transaction
from earnings.models import Commission
from django.utils import timezone

print("=" * 60)
print("PHONIX MLM PLATFORM - DEMO DATA SETUP")
print("=" * 60)

# Add wallet balance to user1 for demo
user1 = User.objects.get(username='user1')
user1.wallet_balance = Decimal('500.00')
user1.save()
print(f"\n✓ Added $500 to user1's wallet")

# Create a subscription for user1
subscription1 = Subscription.objects.create(
    user=user1,
    amount=Decimal('1000.00'),
    bonus_used=Decimal('10.00')
)
user1.registration_bonus = Decimal('0.00')
user1.wallet_balance = Decimal('500.00') - Decimal('990.00')  # Used $990 from wallet
user1.total_invested = Decimal('1000.00')
user1.is_active_investor = True
user1.save()

print(f"✓ Created Tier 1 subscription for user1: ${subscription1.amount}")
print(f"  - Monthly Rate: {subscription1.monthly_rate}%")
print(f"  - Earnings Cap: ${subscription1.earnings_cap}")

# Simulate some earnings for user1
daily_income = subscription1.calculate_daily_income()
subscription1.add_earnings(daily_income * 5)  # 5 days of income
user1.wallet_balance += daily_income * 5
user1.total_earnings += daily_income * 5
user1.save()

print(f"✓ Added 5 days of earnings: ${daily_income * 5:.2f}")

# Create commission record
commission1 = Commission.objects.create(
    user=user1,
    from_user=user1,
    level=0,
    amount=daily_income * 5,
    commission_type=Commission.DAILY_BOND,
    source_subscription=subscription1,
    description="Daily bond income (demo)"
)
print(f"✓ Created commission record")

# Create transaction records
Transaction.objects.create(
    user=user1,
    type=Transaction.DEPOSIT,
    amount=Decimal('500.00'),
    fee=Decimal('0.00'),
    net_amount=Decimal('500.00'),
    status=Transaction.COMPLETED,
    description="Demo deposit"
)

Transaction.objects.create(
    user=user1,
    type=Transaction.PURCHASE,
    amount=Decimal('1000.00'),
    fee=Decimal('0.00'),
    net_amount=Decimal('1000.00'),
    status=Transaction.COMPLETED,
    subscription=subscription1,
    description=f"Subscription purchase - {subscription1.tier}"
)

Transaction.objects.create(
    user=user1,
    type=Transaction.DAILY_INCOME,
    amount=daily_income * 5,
    fee=Decimal('0.00'),
    net_amount=daily_income * 5,
    status=Transaction.COMPLETED,
    subscription=subscription1,
    description="Daily bond income (5 days)"
)

print(f"✓ Created 3 transaction records")

# Add some data to user2
user2 = User.objects.get(username='user2')
user2.wallet_balance = Decimal('250.00')
user2.save()

subscription2 = Subscription.objects.create(
    user=user2,
    amount=Decimal('500.00'),
    bonus_used=Decimal('10.00')
)
user2.registration_bonus = Decimal('0.00')
user2.wallet_balance = Decimal('250.00') - Decimal('490.00')
user2.total_invested = Decimal('500.00')
user2.is_active_investor = True
user2.save()

print(f"\n✓ Created Tier 1 subscription for user2: ${subscription2.amount}")

# Create commission for user1 from user2's purchase (Level 1 - 10%)
level1_commission = subscription2.amount * Decimal('0.10')
Commission.objects.create(
    user=user1,
    from_user=user2,
    level=1,
    amount=level1_commission,
    commission_type=Commission.GENERATION,
    source_subscription=subscription2,
    description=f"Level 1 commission from {user2.username}'s subscription"
)

user1.wallet_balance += level1_commission
user1.total_earnings += level1_commission
user1.save()

Transaction.objects.create(
    user=user1,
    type=Transaction.COMMISSION,
    amount=level1_commission,
    fee=Decimal('0.00'),
    net_amount=level1_commission,
    status=Transaction.COMPLETED,
    subscription=subscription2,
    description=f"Level 1 commission from {user2.username}"
)

print(f"✓ Created Level 1 commission for user1: ${level1_commission}")

print("\n" + "=" * 60)
print("DEMO DATA SUMMARY")
print("=" * 60)
print(f"\nUser 1 (Referrer):")
print(f"  - Wallet Balance: ${user1.wallet_balance}")
print(f"  - Total Invested: ${user1.total_invested}")
print(f"  - Total Earnings: ${user1.total_earnings}")
print(f"  - Active Subscription: ${subscription1.amount} @ {subscription1.monthly_rate}%")
print(f"  - Earnings Progress: {subscription1.earnings_percentage:.1f}%")
print(f"  - Direct Referrals: {user1.direct_referrals_count}")

print(f"\nUser 2 (Referred by User 1):")
print(f"  - Wallet Balance: ${user2.wallet_balance}")
print(f"  - Total Invested: ${user2.total_invested}")
print(f"  - Active Subscription: ${subscription2.amount} @ {subscription2.monthly_rate}%")

print("\n" + "=" * 60)
print("✓ Demo data setup complete!")
print("=" * 60)
print("\nYou can now:")
print("1. Login as 'user1' to see an active investor dashboard")
print("2. Login as 'user2' to see a referred user's dashboard")
print("3. Access admin panel at /admin (admin/admin123)")
print("=" * 60)
