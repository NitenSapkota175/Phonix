"""
IncomeService — records income events called by WalletService.credit_system().
"""
from .models import Income


class IncomeService:

    @staticmethod
    def record(user, income_type: str, amount, wallet_type: str,
               source_user=None, level: int = None, description: str = ''):
        """
        Create an Income record.
        Called automatically by WalletService.credit_system().
        Do not call directly from views.
        """
        Income.objects.create(
            user=user,
            source_user=source_user,
            income_type=income_type,
            amount=amount,
            wallet_type=wallet_type,
            level=level,
            description=description,
        )
