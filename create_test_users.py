#!/usr/bin/env python
"""
Script to create a superuser and test users for Phonix platform.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phonix.settings')
django.setup()

from accounts.models import User

# Create superuser
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@phonix.com',
        password='admin123'
    )
    print(f"✓ Superuser created: admin / admin123")
else:
    print("✓ Superuser already exists")

# Create test user 1 (no referrer)
if not User.objects.filter(username='user1').exists():
    user1 = User.objects.create_user(
        username='user1',
        email='user1@test.com',
        password='password123',
        first_name='John',
        last_name='Doe'
    )
    print(f"✓ Test User 1 created: user1 / password123")
    print(f"  Referral Code: {user1.referral_code}")
    print(f"  Registration Bonus: ${user1.registration_bonus}")
else:
    user1 = User.objects.get(username='user1')
    print(f"✓ Test User 1 exists: {user1.referral_code}")

# Create test user 2 (referred by user1)
if not User.objects.filter(username='user2').exists():
    user2 = User.objects.create_user(
        username='user2',
        email='user2@test.com',
        password='password123',
        first_name='Jane',
        last_name='Smith',
        referred_by=user1
    )
    user1.update_direct_referrals_count()
    print(f"✓ Test User 2 created: user2 / password123")
    print(f"  Referred by: {user1.username}")
    print(f"  Referral Code: {user2.referral_code}")
else:
    print("✓ Test User 2 already exists")

# Create test user 3 (referred by user2)
if not User.objects.filter(username='user3').exists():
    user3 = User.objects.create_user(
        username='user3',
        email='user3@test.com',
        password='password123',
        first_name='Bob',
        last_name='Johnson',
        referred_by=user2
    )
    user2.update_direct_referrals_count()
    print(f"✓ Test User 3 created: user3 / password123")
    print(f"  Referred by: {user2.username}")
else:
    print("✓ Test User 3 already exists")

print("\n" + "="*50)
print("PHONIX PLATFORM - TEST ACCOUNTS")
print("="*50)
print("Admin: admin / admin123")
print("User 1: user1 / password123")
print("User 2: user2 / password123")
print("User 3: user3 / password123")
print("="*50)
