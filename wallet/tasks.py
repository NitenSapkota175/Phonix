"""
Celery tasks for wallet operations including deposit monitoring and withdrawal processing
"""
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

from wallet.models import Transaction, DepositAddress
from wallet.tron_utils import (
    get_tron_client,
    get_usdt_contract_address,
    verify_transaction,
    send_usdt,
    get_account_balance
)
from accounts.email_utils import send_deposit_confirmation, send_withdrawal_processed

logger = logging.getLogger(__name__)


@shared_task
def monitor_deposits():
    """
    Monitor blockchain for new deposits to user addresses
    Run every 60 seconds via Celery Beat
    
    This task checks all deposit addresses for new USDT transactions
    and automatically credits user wallets when deposits are detected.
    """
    logger.info("Starting deposit monitoring task...")
    
    try:
        client = get_tron_client()
        usdt_contract_address = get_usdt_contract_address()
        
        # Get all deposit addresses that haven't been checked recently
        # or have never been checked
        one_minute_ago = timezone.now() - timezone.timedelta(minutes=1)
        addresses_to_check = DepositAddress.objects.filter(
            models.Q(last_checked__isnull=True) | models.Q(last_checked__lt=one_minute_ago)
        )[:100]  # Limit to 100 at a time to avoid API rate limits
        
        deposits_found = 0
        
        for deposit_addr in addresses_to_check:
            try:
                # Check for new USDT transactions
                balance_info = get_account_balance(deposit_addr.address)
                usdt_balance = balance_info['usdt_balance']
                
                # If there's a balance, check for unprocessed transactions
                if usdt_balance > 0:
                    # Get transaction history via TronGrid API
                    # For now, we'll check the balance and create a deposit
                    # In production, you'd query transaction history
                    
                    # Check if we already processed this amount
                    existing_deposit = Transaction.objects.filter(
                        wallet_address=deposit_addr.address,
                        type=Transaction.DEPOSIT,
                        status__in=[Transaction.PENDING, Transaction.COMPLETED]
                    ).exists()
                    
                    if not existing_deposit and usdt_balance > 0:
                        # Create pending deposit transaction
                        txn = Transaction.objects.create(
                            user=deposit_addr.user,
                            type=Transaction.DEPOSIT,
                            amount=usdt_balance,
                            net_amount=usdt_balance,
                            wallet_address=deposit_addr.address,
                            status=Transaction.PENDING,
                            description=f"USDT TRC20 deposit detected"
                        )
                        
                        deposits_found += 1
                        logger.info(f"New deposit detected: ${usdt_balance} for {deposit_addr.user.username}")
                
                # Update last checked time
                deposit_addr.last_checked = timezone.now()
                deposit_addr.save(update_fields=['last_checked'])
                
            except Exception as e:
                logger.error(f"Error checking address {deposit_addr.address}: {e}")
                continue
        
        logger.info(f"Deposit monitoring complete. Found {deposits_found} new deposits.")
        
        return {
            "status": "completed",
            "addresses_checked": addresses_to_check.count(),
            "deposits_found": deposits_found
        }
        
    except Exception as e:
        logger.error(f"Error in deposit monitoring task: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@shared_task
def verify_and_credit_deposit(transaction_id, txn_hash):
    """
    Verify a deposit transaction on blockchain and credit user wallet
    
    Args:
        transaction_id: Transaction model ID
        txn_hash: Blockchain transaction hash to verify
    """
    try:
        txn = Transaction.objects.get(id=transaction_id)
        
        # Verify transaction on blockchain
        verification = verify_transaction(txn_hash)
        
        if not verification.get('exists'):
            txn.mark_failed("Transaction not found on blockchain")
            return {"status": "error", "message": "Transaction not found"}
        
        if not verification.get('confirmed'):
            # Transaction exists but not confirmed yet
            return {"status": "pending", "message": "Transaction not yet confirmed"}
        
        # Transaction confirmed, credit user
        with transaction.atomic():
            user = txn.user
            user.wallet_balance += txn.net_amount
            user.save()
            
            # Update transaction
            txn.txn_hash = txn_hash
            txn.mark_completed()
            
            # Send confirmation email
            send_deposit_confirmation(txn)
            
            logger.info(f"Deposit credited: ${txn.amount} to {user.username}")
        
        return {"status": "success", "amount": str(txn.amount)}
        
    except Transaction.DoesNotExist:
        return {"status": "error", "message": "Transaction not found"}
    except Exception as e:
        logger.error(f"Error verifying deposit: {e}")
        return {"status": "error", "message": str(e)}


@shared_task
def process_withdrawal_crypto(transaction_id):
    """
    Process a withdrawal by sending USDT from master wallet
    Called after admin approval
    
    Args:
        transaction_id: Transaction model ID
    """
    try:
        from django.conf import settings
        
        txn = Transaction.objects.get(id=transaction_id)
        
        if txn.type != Transaction.WITHDRAWAL:
            return {"status": "error", "message": "Not a withdrawal transaction"}
        
        if txn.status != Transaction.PROCESSING:
            return {"status": "error", "message": "Transaction not in processing state"}
        
        # Get master wallet private key from settings
        master_key = settings.MASTER_WALLET_KEY
        if not master_key:
            return {"status": "error", "message": "Master wallet not configured"}
        
        # Send USDT
        result = send_usdt(
            from_private_key=master_key,
            to_address=txn.wallet_address,
            amount=txn.net_amount
        )
        
        if result['success']:
            # Update transaction
            txn.txn_hash = result['txn_hash']
            txn.mark_completed()
            
            # Send notification email
            send_withdrawal_processed(txn)
            
            logger.info(f"Withdrawal processed: ${txn.net_amount} to {txn.wallet_address}")
            
            return {
                "status": "success",
                "txn_hash": result['txn_hash'],
                "amount": str(txn.net_amount)
            }
        else:
            # Mark as failed
            txn.mark_failed(result['error'])
            logger.error(f"Withdrawal failed: {result['error']}")
            
            return {
                "status": "error",
                "message": result['error']
            }
        
    except Transaction.DoesNotExist:
        return {"status": "error", "message": "Transaction not found"}
    except Exception as e:
        logger.error(f"Error processing withdrawal: {e}")
        return {"status": "error", "message": str(e)}


@shared_task
def consolidate_deposits():
    """
    Consolidate USDT from user deposit addresses to master wallet
    Run daily to move funds to master wallet for better management
    
    This is optional but recommended for better fund management
    """
    from django.conf import settings
    
    master_address = settings.MASTER_WALLET_ADDRESS
    if not master_address:
        logger.warning("Master wallet address not configured")
        return
    
    # Get deposit addresses with USDT balance
    addresses = DepositAddress.objects.all()
    consolidated_count = 0
    total_amount = Decimal('0')
    
    for deposit_addr in addresses:
        try:
            balance_info = deposit_addr.get_balance()
            usdt_balance = balance_info['usdt_balance']
            
            if usdt_balance > Decimal('1'):  # Only consolidate if > $1
                # Send to master wallet
                private_key = deposit_addr.get_private_key()
                
                result = send_usdt(
                    from_private_key=private_key,
                    to_address=master_address,
                    amount=usdt_balance
                )
                
                if result['success']:
                    consolidated_count += 1
                    total_amount += usdt_balance
                    logger.info(f"Consolidated ${usdt_balance} from {deposit_addr.address}")
                
        except Exception as e:
            logger.error(f"Error consolidating from {deposit_addr.address}: {e}")
            continue
    
    logger.info(f"Consolidation complete: {consolidated_count} addresses, ${total_amount} total")
    
    return {
        "status": "completed",
        "addresses_consolidated": consolidated_count,
        "total_amount": str(total_amount)
    }
