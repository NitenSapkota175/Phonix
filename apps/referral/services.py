"""
ReferralService — binary tree placement, volume propagation, generation income,
matching bonus calculation, and fresh volume reset.
"""
import logging
from collections import deque
from decimal import Decimal
from django.db import transaction
from django.db.models import F

from apps.core.exceptions import BinaryPlacementError, SelfReferralError
from apps.wallets.models import Wallet
from apps.wallets.services import WalletService
from .models import BinaryNode

logger = logging.getLogger(__name__)

# ─── 20-Level Generation Income Rates ─────────────────────────────────────────
GENERATION_RATES = {
    1: Decimal('0.10'),    # 10%
    2: Decimal('0.05'),    # 5%
    3: Decimal('0.03'),    # 3%
    4: Decimal('0.02'),    # 2%
    5: Decimal('0.02'),    # 2%
    6: Decimal('0.01'),    # 1%
    7: Decimal('0.01'),    # 1%
    8: Decimal('0.01'),    # 1%
    9: Decimal('0.01'),    # 1%
    10: Decimal('0.01'),   # 1%
    11: Decimal('0.005'),  # 0.5%
    12: Decimal('0.005'),
    13: Decimal('0.005'),
    14: Decimal('0.005'),
    15: Decimal('0.005'),
    16: Decimal('0.003'),  # 0.3%
    17: Decimal('0.003'),
    18: Decimal('0.003'),
    19: Decimal('0.003'),
    20: Decimal('0.003'),
}

# Minimum direct referrals required to earn at each level
DIRECT_REQUIREMENTS = {
    3: 2, 4: 2,
    5: 3, 6: 3,
    7: 4, 8: 4,
    9: 5, 10: 5,
    11: 6, 12: 6,
    13: 7, 14: 7,
    15: 8, 16: 8,
    17: 9, 18: 9,
    19: 10, 20: 10,
}


class ReferralService:
    """
    Manages binary MLM tree operations.
    Call from signals, services, and Celery tasks only.
    """

    # ─── Tree Initialization ──────────────────────────────────────────────────

    @staticmethod
    def create_root_node(user):
        """Create a standalone BinaryNode for users with no sponsor."""
        BinaryNode.objects.get_or_create(user=user)

    @staticmethod
    def on_user_registered(new_user, sponsor):
        """
        Place a new user in the binary tree under their sponsor.
        Uses BFS to find the first available left/right slot.
        """
        try:
            sponsor_node, _ = BinaryNode.objects.get_or_create(user=sponsor)
            new_node = ReferralService._bfs_place(new_user, sponsor_node)
            return new_node
        except Exception as exc:
            logger.error('Binary placement failed for user %s: %s', new_user.pk, exc)
            # Still create the node to avoid orphans — place at root level
            node, _ = BinaryNode.objects.get_or_create(user=new_user)
            return node

    @staticmethod
    def _bfs_place(new_user, root_node) -> BinaryNode:
        """
        BFS traversal of the binary tree to find the first empty left or right slot.
        Left slots are filled before right slots (left-priority BFS).
        """
        queue = deque([root_node])

        while queue:
            node = queue.popleft()

            with transaction.atomic():
                # Lock this node to prevent concurrent placement at the same slot
                locked_node = BinaryNode.objects.select_for_update().get(pk=node.pk)

                if not locked_node.left_child_id:
                    new_node = BinaryNode.objects.create(
                        user=new_user,
                        parent=locked_node,
                        position=BinaryNode.Position.LEFT,
                    )
                    BinaryNode.objects.filter(pk=locked_node.pk).update(left_child=new_node)
                    ReferralService._propagate_volume(new_node, Decimal('0.00'))  # ready for future volume
                    return new_node

                if not locked_node.right_child_id:
                    new_node = BinaryNode.objects.create(
                        user=new_user,
                        parent=locked_node,
                        position=BinaryNode.Position.RIGHT,
                    )
                    BinaryNode.objects.filter(pk=locked_node.pk).update(right_child=new_node)
                    ReferralService._propagate_volume(new_node, Decimal('0.00'))
                    return new_node

            # Both slots taken — add children to queue
            if locked_node.left_child_id:
                queue.append(BinaryNode.objects.get(pk=locked_node.left_child_id))
            if locked_node.right_child_id:
                queue.append(BinaryNode.objects.get(pk=locked_node.right_child_id))

        raise BinaryPlacementError('No available slot found in binary tree.')

    # ─── Volume Propagation ───────────────────────────────────────────────────

    @staticmethod
    def propagate_volume(node: BinaryNode, amount: Decimal):
        """
        Public entry point: walk up the tree and add `amount` to
        the left_volume or right_volume of each ancestor.
        Also updates fresh_* volumes for the weekly matching bonus.
        """
        ReferralService._propagate_volume(node, amount)

    @staticmethod
    def _propagate_volume(node: BinaryNode, amount: Decimal):
        """Walk up the tree updating ancestor volumes using F() expressions."""
        if amount <= 0:
            return

        current = node
        while current.parent_id:
            parent = BinaryNode.objects.select_for_update().get(pk=current.parent_id)

            if parent.left_child_id == current.pk:
                BinaryNode.objects.filter(pk=parent.pk).update(
                    left_volume=F('left_volume') + amount,
                    fresh_left_volume=F('fresh_left_volume') + amount,
                )
            else:
                BinaryNode.objects.filter(pk=parent.pk).update(
                    right_volume=F('right_volume') + amount,
                    fresh_right_volume=F('fresh_right_volume') + amount,
                )
            # Move up
            current = BinaryNode.objects.get(pk=current.parent_id)

    # ─── Generation Income Distribution ──────────────────────────────────────

    @staticmethod
    def distribute_generation_income(trade):
        """
        Distribute 20-level generation income using `referred_by` chain.
        Called asynchronously after trade activation.
        """
        from apps.accounts.models import User

        distributed = 0
        total = Decimal('0.00')
        upline = trade.user.referred_by
        level = 1

        while upline and level <= 20:
            rate = GENERATION_RATES.get(level, Decimal('0'))
            req = DIRECT_REQUIREMENTS.get(level, 0)

            # Check rate and direct referral requirement
            if rate > 0 and upline.direct_referrals_count >= req:
                income_amount = trade.amount * rate
                try:
                    WalletService.credit_system(
                        user=upline,
                        wallet_type=Wallet.WalletType.AFFILIATE,
                        amount=income_amount,
                        txn_type='generation',
                        description=f'Level {level} generation income from trade #{trade.pk}',
                        source_user=trade.user,
                    )
                    total += income_amount
                    distributed += 1
                except Exception as exc:
                    logger.warning('Gen income level %s for user %s failed: %s', level, upline.pk, exc)

            upline = upline.referred_by
            level += 1

        # Propagate volume up the binary tree
        try:
            node = trade.user.binary_node
            ReferralService._propagate_volume(node, trade.amount)
        except BinaryNode.DoesNotExist:
            logger.warning('No BinaryNode for user %s during volume propagation', trade.user.pk)

        return {'distributed_levels': distributed, 'total_amount': str(total)}

    # ─── Matching Bonus (Weekly) ──────────────────────────────────────────────

    @staticmethod
    def calculate_weekly_matching_bonus():
        """
        Weekly matching bonus calculation.
        Bonus = min(fresh_left_volume, fresh_right_volume) × 10%
        Credited to Affiliate Wallet.
        """
        MATCHING_RATE = Decimal('0.10')  # 10% of matched volume
        nodes = BinaryNode.objects.select_related('user').filter(
            fresh_left_volume__gt=0,
            fresh_right_volume__gt=0,
        )
        processed = 0
        for node in nodes:
            matched = min(node.fresh_left_volume, node.fresh_right_volume)
            if matched <= 0:
                continue
            bonus = (matched * MATCHING_RATE).quantize(Decimal('0.01'))
            try:
                WalletService.credit_system(
                    user=node.user,
                    wallet_type=Wallet.WalletType.AFFILIATE,
                    amount=bonus,
                    txn_type='matching',
                    description=f'Weekly matching bonus — matched ${matched}',
                )
                processed += 1
            except Exception as exc:
                logger.warning('Matching bonus for user %s failed: %s', node.user.pk, exc)

        return {'matching_bonuses_paid': processed}

    # ─── Weekly Fresh Volume Reset ────────────────────────────────────────────

    @staticmethod
    def reset_fresh_volumes():
        """Reset all fresh_left_volume and fresh_right_volume to 0 every Monday."""
        updated = BinaryNode.objects.update(
            fresh_left_volume=Decimal('0.00'),
            fresh_right_volume=Decimal('0.00'),
        )
        logger.info('Fresh volumes reset for %s binary nodes', updated)
        return {'nodes_reset': updated}
