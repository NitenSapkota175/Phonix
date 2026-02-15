"""
Private key encryption utilities for secure storage
Uses Fernet (symmetric encryption) from cryptography library
"""
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib


def get_encryption_key():
    """
    Get or generate encryption key from SECRET_KEY
    Derives a Fernet-compatible key from Django's SECRET_KEY
    
    Returns:
        bytes: Fernet encryption key
    """
    # Use Django's SECRET_KEY to derive encryption key
    # This ensures encryption key is consistent and tied to the app
    key_bytes = settings.SECRET_KEY.encode('utf-8')
    
    # Use SHA256 to get 32 bytes, then base64 encode for Fernet
    hash_digest = hashlib.sha256(key_bytes).digest()
    fernet_key = base64.urlsafe_b64encode(hash_digest)
    
    return fernet_key


def encrypt_private_key(private_key):
    """
    Encrypt a private key for secure storage
    
    Args:
        private_key (str): Hex private key
        
    Returns:
        str: Encrypted private key (base64 string)
    """
    try:
        key = get_encryption_key()
        f = Fernet(key)
        
        # Encrypt the private key
        encrypted = f.encrypt(private_key.encode('utf-8'))
        
        # Return as base64 string for storage
        return encrypted.decode('utf-8')
    except Exception as e:
        raise Exception(f"Encryption error: {e}")


def decrypt_private_key(encrypted_private_key):
    """
    Decrypt a stored private key
    
    Args:
        encrypted_private_key (str): Encrypted private key (base64 string)
        
    Returns:
        str: Decrypted hex private key
    """
    try:
        key = get_encryption_key()
        f = Fernet(key)
        
        # Decrypt the private key
        decrypted = f.decrypt(encrypted_private_key.encode('utf-8'))
        
        # Return as string
        return decrypted.decode('utf-8')
    except Exception as e:
        raise Exception(f"Decryption error: {e}")


def test_encryption():
    """Test encryption/decryption"""
    test_key = "0" * 64  # Dummy private key
    
    encrypted = encrypt_private_key(test_key)
    decrypted = decrypt_private_key(encrypted)
    
    assert test_key == decrypted, "Encryption test failed"
    print("✅ Encryption test passed")
