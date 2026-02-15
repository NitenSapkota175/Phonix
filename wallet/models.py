from django.db import models
from django.utils import timezone
from decimal import Decimal


class Transaction(models.Model):
    """
    Track all financial transactions in the system.
    """
    
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    PURCHASE = 'purchase'
    COMMISSION = 'commission'
    BONUS = 'bonus'
    DAILY_INCOME = 'daily_income'
    WEEKLY_BONUS = 'weekly_bonus'
    
    TYPE_CHOICES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
        (PURCHASE, 'Package Purchase'),
        (COMMISSION, 'Referral Commission'),
        (BONUS, 'Registration Bonus'),
        (DAILY_INCOME, 'Daily Bond Income'),
        (WEEKLY_BONUS, 'Weekly Rank Bonus'),
    ]
    
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    
    # Crypto-specific fields
    txn_hash = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="TRC20 transaction hash"
    )
    wallet_address = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="TRC20 wallet address"
    )
    
    # Fees
    fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Transaction fee (5% for withdrawals)"
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount after fees"
    )
    
    # Status and metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    description = models.TextField(
        blank=True,
        help_text="Additional details about the transaction"
    )
    
    # Related objects
    subscription = models.ForeignKey(
        'investment.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.type} - ${self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Calculate net amount on save"""
        if not self.net_amount:
            self.net_amount = self.amount - self.fee
        super().save(*args, **kwargs)
    
    def mark_completed(self):
        """Mark transaction as completed"""
        self.status = self.COMPLETED
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, reason=""):
        """Mark transaction as failed"""
        self.status = self.FAILED
        if reason:
            self.description += f"\nFailed: {reason}"
        self.save()
    
    @staticmethod
    def calculate_withdrawal_fee(amount):
        """Calculate 5% withdrawal fee"""
        return amount * Decimal('0.05')


class DepositAddress(models.Model):
    """
    Store unique TRC20 deposit addresses for users.
    Each user gets a unique address for deposits.
    """
    
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='deposit_address'
    )
    address = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique TRC20 address for deposits"
    )
    private_key_encrypted = models.TextField(
        blank=True,
        help_text="Encrypted private key for this address"
    )
    last_checked = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this address was checked for deposits"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Deposit Address'
        verbose_name_plural = 'Deposit Addresses'
    
    def __str__(self):
        return f"{self.user.username} - {self.address}"
    
    def save(self, *args, **kwargs):
        """Auto-generate TRC20 address on first save"""
        if not self.address:
            from wallet.tron_utils import generate_wallet
            from wallet.encryption import encrypt_private_key
            
            # Generate new wallet
            wallet = generate_wallet()
            self.address = wallet['address']
            
            # Encrypt and store private key
            self.private_key_encrypted = encrypt_private_key(wallet['private_key'])
        
        super().save(*args, **kwargs)
    
    def get_private_key(self):
        """
        Decrypt and return private key
        WARNING: Use with caution! Only call when needed.
        """
        if not self.private_key_encrypted:
            return None
        
        from wallet.encryption import decrypt_private_key
        return decrypt_private_key(self.private_key_encrypted)
    
    def get_balance(self):
        """Get current TRX and USDT balance for this address"""
        from wallet.tron_utils import get_account_balance
        return get_account_balance(self.address)
