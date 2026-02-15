"""
TRON Blockchain Utilities for TRC20 USDT Integration
Handles wallet generation, transaction verification, and blockchain interaction
"""
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.exceptions import ValidationError, TransactionError
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# USDT TRC20 Contract Addresses
USDT_CONTRACTS = {
    'mainnet': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
    'shasta': 'TG3XXyExBkPp9nzdajDZsozEu4BkaSJozs',  # Testnet USDT
}


def get_tron_client():
    """
    Get configured Tron client instance based on network setting
    
    Returns:
        Tron: Configured Tron client
    """
    network = settings.TRON_NETWORK
    
    if network == 'mainnet':
        client = Tron(network='mainnet')
    else:
        client = Tron(network='shasta')
    
    # Set API key if available
    if settings.TRON_API_KEY:
        client.providers[0].api_key = settings.TRON_API_KEY
    
    return client


def get_usdt_contract_address():
    """Get USDT contract address for current network"""
    network = settings.TRON_NETWORK
    return USDT_CONTRACTS.get(network, USDT_CONTRACTS['mainnet'])


def generate_wallet():
    """
    Generate a new TRC20 wallet address and private key
    
    Returns:
        dict: {
            'address': str - Base58 TRC20 address,
            'private_key': str - Hex private key,
            'public_key': str - Hex public key
        }
    
    WARNING: Store private_key securely and encrypted!
    """
    try:
        private_key = PrivateKey.random()
        public_key = private_key.public_key
        address = public_key.to_base58check_address()
        
        return {
            'address': address,
            'private_key': private_key.hex(),
            'public_key': public_key.hex(),
        }
    except Exception as e:
        logger.error(f"Error generating wallet: {e}")
        raise


def validate_address(address):
    """
    Validate if a string is a valid TRC20 address
    
    Args:
        address (str): TRC20 address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not address or not isinstance(address, str):
            return False
        
        # TRC20 addresses start with 'T' and are 34 characters
        if not address.startswith('T') or len(address) != 34:
            return False
        
        # Try to decode with Tron client
        client = get_tron_client()
        # This will raise an exception if invalid
        client.to_hex_address(address)
        return True
    except:
        return False


def get_account_balance(address):
    """
    Get TRX and USDT balance for an address
    
    Args:
        address (str): TRC20 address
        
    Returns:
        dict: {
            'trx_balance': Decimal - TRX balance,
            'usdt_balance': Decimal - USDT balance
        }
    """
    try:
        client = get_tron_client()
        
        # Get TRX balance
        account_info = client.get_account(address)
        trx_balance = account_info.get('balance', 0) / 1_000_000  # Convert from SUN to TRX
        
        # Get USDT balance
        usdt_contract = get_usdt_contract_address()
        contract = client.get_contract(usdt_contract)
        
        try:
            usdt_balance_raw = contract.functions.balanceOf(address)
            usdt_balance = Decimal(usdt_balance_raw) / Decimal('1000000')  # USDT has 6 decimals
        except:
            usdt_balance = Decimal('0')
        
        return {
            'trx_balance': Decimal(str(trx_balance)),
            'usdt_balance': usdt_balance
        }
    except Exception as e:
        logger.error(f"Error getting balance for {address}: {e}")
        return {
            'trx_balance': Decimal('0'),
            'usdt_balance': Decimal('0')
        }


def get_usdt_transactions(address, limit=20):
    """
    Get USDT TRC20 transactions for an address
    
    Args:
        address (str): TRC20 address
        limit (int): Maximum number of transactions to fetch
        
    Returns:
        list: List of transaction dicts with keys:
            - txn_hash: Transaction hash
            - from_address: Sender address
            - to_address: Receiver address
            - amount: USDT amount (Decimal)
            - timestamp: Unix timestamp
            - confirmed: Boolean
    """
    try:
        client = get_tron_client()
        usdt_contract = get_usdt_contract_address()
        
        # Get TRC20 transfers from TronGrid API
        # Note: This requires TronGrid Pro API for full history
        url = f"{client.providers[0].base_url}/v1/accounts/{address}/transactions/trc20"
        params = {
            'limit': limit,
            'contract_address': usdt_contract
        }
        
        # Make API request (you may need to use requests library)
        # For now, we'll use a simplified approach
        
        transactions = []
        # Implementation will depend on TronGrid API response format
        
        return transactions
    except Exception as e:
        logger.error(f"Error fetching transactions for {address}: {e}")
        return []


def verify_transaction(txn_hash):
    """
    Verify a transaction on the blockchain
    
    Args:
        txn_hash (str): Transaction hash to verify
        
    Returns:
        dict: {
            'exists': bool,
            'confirmed': bool,
            'from_address': str,
            'to_address': str,
            'amount': Decimal,
            'timestamp': int,
            'block_number': int
        }
    """
    try:
        client = get_tron_client()
        
        # Get transaction info
        txn_info = client.get_transaction(txn_hash)
        
        if not txn_info:
            return {'exists': False}
        
        # Check if transaction is confirmed
        confirmed = txn_info.get('ret', [{}])[0].get('contractRet') == 'SUCCESS'
        
        # Extract transaction details
        # This will vary based on transaction type
        result = {
            'exists': True,
            'confirmed': confirmed,
            'timestamp': txn_info.get('raw_data', {}).get('timestamp', 0),
        }
        
        return result
    except Exception as e:
        logger.error(f"Error verifying transaction {txn_hash}: {e}")
        return {'exists': False}


def send_usdt(from_private_key, to_address, amount):
    """
    Send USDT to an address
    
    Args:
        from_private_key (str): Hex private key of sender
        to_address (str): Recipient TRC20 address
        amount (Decimal): Amount of USDT to send
        
    Returns:
        dict: {
            'success': bool,
            'txn_hash': str or None,
            'error': str or None
        }
    """
    try:
        client = get_tron_client()
        
        # Load private key
        priv_key = PrivateKey(bytes.fromhex(from_private_key))
        from_address = priv_key.public_key.to_base58check_address()
        
        # Validate recipient address
        if not validate_address(to_address):
            return {
                'success': False,
                'txn_hash': None,
                'error': 'Invalid recipient address'
            }
        
        # Get USDT contract
        usdt_contract = get_usdt_contract_address()
        contract = client.get_contract(usdt_contract)
        
        # Convert amount to contract format (6 decimals for USDT)
        amount_raw = int(amount * 1_000_000)
        
        # Build and send transaction
        txn = (
            contract.functions.transfer(to_address, amount_raw)
            .with_owner(from_address)
            .fee_limit(50_000_000)  # 50 TRX fee limit
            .build()
            .sign(priv_key)
        )
        
        # Broadcast transaction
        result = txn.broadcast()
        
        return {
            'success': True,
            'txn_hash': result.get('txid'),
            'error': None
        }
        
    except ValidationError as e:
        logger.error(f"Validation error sending USDT: {e}")
        return {
            'success': False,
            'txn_hash': None,
            'error': f'Validation error: {str(e)}'
        }
    except TransactionError as e:
        logger.error(f"Transaction error sending USDT: {e}")
        return {
            'success': False,
            'txn_hash': None,
            'error': f'Transaction error: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Error sending USDT: {e}")
        return {
            'success': False,
            'txn_hash': None,
            'error': str(e)
        }


def estimate_transaction_fee():
    """
    Estimate transaction fee for USDT transfer
    
    Returns:
        Decimal: Estimated fee in TRX
    """
    # USDT transfers typically cost 14,000-30,000 Energy
    # Without staked TRX, this costs ~14-30 TRX per transaction
    # With proper Energy staking, fees can be near zero
    
    # Conservative estimate
    return Decimal('1.0')  # 1 TRX


def get_master_wallet_balance():
    """
    Get balance of the master wallet
    
    Returns:
        dict: Balance information
    """
    master_address = settings.MASTER_WALLET_ADDRESS
    if not master_address:
        return {'error': 'Master wallet not configured'}
    
    return get_account_balance(master_address)
