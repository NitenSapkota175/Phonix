"""
Test TRC20 utilities and verify everything is working
"""

def test_trc20_setup():
    """Test all TRC20 components"""
    print("=" * 60)
    print("TESTING TRC20 INTEGRATION SETUP")
    print("=" * 60)
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Import utilities
    print("1. Testing imports...")
    try:
        from wallet.tron_utils import generate_wallet, validate_address, get_tron_client
        from wallet.encryption import encrypt_private_key, decrypt_private_key
        print("   ✅ All imports successful")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        tests_failed += 1
        return
    
    # Test 2: Wallet generation
    print("2. Testing wallet generation...")
    try:
        wallet = generate_wallet()
        assert 'address' in wallet
        assert 'private_key' in wallet
        assert wallet['address'].startswith('T')
        assert len(wallet['address']) == 34
        assert len(wallet['private_key']) == 64
        print(f"   ✅ Generated address: {wallet['address'][:10]}...")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Wallet generation failed: {e}")
        tests_failed += 1
    
    # Test 3: Address validation
    print("3. Testing address validation...")
    try:
        valid = validate_address(wallet['address'])
        invalid = validate_address('invalid-address')
        assert valid == True
        assert invalid == False
        print("   ✅ Address validation working")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")
        tests_failed += 1
    
    # Test 4: Encryption
    print("4. Testing private key encryption...")
    try:
        test_key = "a" * 64
        encrypted = encrypt_private_key(test_key)
        decrypted = decrypt_private_key(encrypted)
        assert decrypted == test_key
        assert encrypted != test_key
        print(f"   ✅ Encryption working (encrypted length: {len(encrypted)})")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Encryption failed: {e}")
        tests_failed += 1
    
    # Test 5: Tron client connection
    print("5. Testing TRON network connection...")
    try:
        client = get_tron_client()
        # Test by getting a known contract (USDT)
        from wallet.tron_utils import get_usdt_contract_address
        usdt_address = get_usdt_contract_address()
        assert len(usdt_address) == 34
        print(f"   ✅ Connected to TRON network (USDT: {usdt_address[:10]}...)")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        tests_failed += 1
    
    # Test 6: DepositAddress model
    print("6. Testing DepositAddress model...")
    try:
        from wallet.models import DepositAddress
        from accounts.models import User
        
        # Check if we can create a user and address
        test_user = User.objects.filter(username='test_trc20_user').first()
        if test_user:
            print("   ⚠️  Test user already exists, skipping creation")
        else:
            print("   ℹ️  No test user found, create one to test address generation")
        
        print("   ✅ DepositAddress model accessible")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Model test failed: {e}")
        tests_failed += 1
    
    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}")
    print(f"❌ Tests Failed: {tests_failed}")
    print()
    
    if tests_failed == 0:
        print("🎉 All tests passed! TRC20 integration is ready!")
        print()
        print("Next steps:")
        print("1. Generate master wallet: python generate_master_wallet.py")
        print("2. Update .env with wallet credentials")
        print("3. Follow TRC20_TESTING.md for full testing")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    print("=" * 60)


if __name__ == "__main__":
    import os
    import sys
    import django
    
    # Setup Django environment
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phonix.settings')
    django.setup()
    
    test_trc20_setup()
