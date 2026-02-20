"""
Custom exceptions for the Phonix platform.

Raise these from service layers — views catch and convert
them into HTTP responses or form errors.
"""


class PhonixBaseError(Exception):
    """Root exception for all platform-specific errors."""
    default_message = 'An error occurred.'

    def __init__(self, message=None):
        self.message = message or self.default_message
        super().__init__(self.message)

    def __str__(self):
        return self.message


# ─── Wallet / Financial Exceptions ────────────────────────────────────────────

class InsufficientBalanceError(PhonixBaseError):
    """Raised when a wallet does not have enough funds for an operation."""
    default_message = 'Insufficient wallet balance.'


class CapExceededError(PhonixBaseError):
    """Raised when a user or subscription has reached its earnings cap (3X)."""
    default_message = 'Earnings cap has been reached.'


class WithdrawalRateLimitError(PhonixBaseError):
    """Raised when a user attempts more than one withdrawal within the rate limit window."""
    default_message = 'You can only make one withdrawal every 24 hours.'


class MinimumWithdrawalError(PhonixBaseError):
    """Raised when a withdrawal amount is below the platform minimum."""
    default_message = 'Minimum withdrawal amount is $10.'


class InvalidWalletOperationError(PhonixBaseError):
    """Raised for disallowed wallet operations (e.g., swapping from wrong wallet)."""
    default_message = 'Invalid wallet operation.'


# ─── Trade Exceptions ─────────────────────────────────────────────────────────

class TradeAlreadyActiveError(PhonixBaseError):
    """Raised if business logic prevents a duplicate active trade."""
    default_message = 'You already have an active trade package.'


class MinimumTradeAmountError(PhonixBaseError):
    """Raised when trade amount is below the minimum allowed."""
    default_message = 'Minimum trade amount is $50.'


# ─── Referral / MLM Exceptions ────────────────────────────────────────────────

class BinaryPlacementError(PhonixBaseError):
    """Raised when binary tree placement fails."""
    default_message = 'Could not place user in the binary tree.'


class SelfReferralError(PhonixBaseError):
    """Raised when a user attempts to use their own referral code."""
    default_message = 'You cannot refer yourself.'


# ─── Auth / KYC Exceptions ────────────────────────────────────────────────────

class InvalidTransactionPasswordError(PhonixBaseError):
    """Raised when a transaction password check fails."""
    default_message = 'Invalid transaction password.'


class KYCNotApprovedError(PhonixBaseError):
    """Raised when a user tries a restricted action without approved KYC."""
    default_message = 'Your KYC verification must be approved before proceeding.'


# ─── General Exceptions ───────────────────────────────────────────────────────

class InvalidOperationError(PhonixBaseError):
    """Generic invalid operation."""
    default_message = 'This operation is not allowed.'
