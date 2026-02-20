"""
Signals for the accounts app.
Post-registration hooks: initialize wallets, binary tree placement,
update direct_referrals_count on sponsor.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def on_user_created(sender, instance, created, **kwargs):
    """
    Triggered once when a new user is saved for the first time.
    Initialises wallets, places in binary tree, and awards registration bonus.
    """
    if not created:
        return

    # 1. Initialize 3 wallets for the new user
    from apps.wallets.services import WalletService
    WalletService.initialize_user_wallets(instance)

    # 2. Place user in binary tree
    from apps.referral.services import ReferralService
    if instance.referred_by_id:
        ReferralService.on_user_registered(instance, instance.referred_by)
    else:
        # Root-level user — create binary node with no parent
        ReferralService.create_root_node(instance)

    # 3. Award registration bonus to Main Wallet
    from django.conf import settings
    bonus = getattr(settings, 'REGISTRATION_BONUS_AMOUNT', 10.00)
    if bonus > 0:
        from apps.wallets.services import WalletService as WS
        from apps.wallets.models import Wallet
        WS.credit_system(
            user=instance,
            wallet_type=Wallet.WalletType.MAIN,
            amount=bonus,
            txn_type='reg_bonus',
            description='Registration bonus',
        )

    # 4. Update sponsor's direct_referrals_count
    if instance.referred_by_id:
        User.objects.filter(pk=instance.referred_by_id).update(
            direct_referrals_count=User.objects.filter(
                referred_by_id=instance.referred_by_id
            ).count()
        )
