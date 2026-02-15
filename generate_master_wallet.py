"""
Quick setup script to generate a master wallet for TRC20 integration
Run this to get started with testing
"""

def generate_master_wallet():
    """Generate a new master wallet for the platform"""
    print("=" * 60)
    print("GENERATING MASTER WALLET FOR PHONIX PLATFORM")
    print("=" * 60)
    print()
    
    try:
        from wallet.tron_utils import generate_wallet
        
        wallet = generate_wallet()
        
        print("✅ Master Wallet Generated Successfully!")
        print()
        print("🔐 SAVE THESE CREDENTIALS SECURELY!")
        print("-" * 60)
        print(f"Address:     {wallet['address']}")
        print(f"Private Key: {wallet['private_key']}")
        print("-" * 60)
        print()
        print("📝 Next Steps:")
        print("1. Copy the Address and Private Key above")
        print("2. Open your .env file (or create from .env.example)")
        print("3. Add these lines:")
        print()
        print(f"   MASTER_WALLET_ADDRESS={wallet['address']}")
        print(f"   MASTER_WALLET_KEY={wallet['private_key']}")
        print()
        print("4. For testing, set: TRON_NETWORK=shasta")
        print("5. Get test TRX from: https://www.trongrid.io/shasta/")
        print()
        print("⚠️  IMPORTANT SECURITY NOTES:")
        print("   - NEVER commit .env file to version control")
        print("   - Store private key in secure location (password manager)")
        print("   - For production, use hardware wallet if possible")
        print("   - This key controls all platform funds!")
        print()
        print("=" * 60)
        
        return wallet
        
    except Exception as e:
        print(f"❌ Error generating wallet: {e}")
        print()
        print("Make sure you have:")
        print("1. Installed tronpy: pip install tronpy")
        print("2. Run migrations: python manage.py migrate")
        return None


if __name__ == "__main__":
    import os
    import sys
    import django
    
    # Setup Django environment
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phonix.settings')
    django.setup()
    
    generate_master_wallet()
