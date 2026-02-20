"""
RankService — rank evaluation, weekly payout, duplicate prevention.
"""
import logging
from datetime import date
from decimal import Decimal

from django.db import transaction, IntegrityError
from django.db.models import F

from apps.wallets.models import Wallet
from apps.wallets.services import WalletService
from .models import Rank, UserRank, RankPayout

logger = logging.getLogger(__name__)


class RankService:

    @staticmethod
    def evaluate_and_assign(user):
        """
        Evaluate a user's binary leg volumes against all rank definitions.
        Assigns up to the highest qualifying rank.

        Executive rank: asymmetric check.
        Others: both left_target AND right_target must be met.

        Called from the weekly Celery task (evaluate_all_ranks).
        """
        try:
            node = user.binary_node
        except Exception:
            return None

        left = node.left_volume
        right = node.right_volume

        qualified_rank = None

        # Check from highest to lowest — stop at first match
        for rank in Rank.objects.order_by('-level'):
            if rank.is_asymmetric:
                # Executive: one leg ≥500k AND other ≥100k (either side)
                qualifies = (
                    (left >= Decimal('500000') and right >= Decimal('100000')) or
                    (right >= Decimal('500000') and left >= Decimal('100000'))
                )
            else:
                qualifies = left >= rank.left_target and right >= rank.right_target

            if qualifies:
                qualified_rank = rank
                break

        if not qualified_rank:
            return None

        # Create UserRank if not already awarded this rank
        user_rank, created = UserRank.objects.get_or_create(
            user=user,
            rank=qualified_rank,
            defaults={'achieved_date': date.today(), 'is_active': True},
        )

        if created:
            logger.info('User %s achieved rank: %s', user.username, qualified_rank.name)

        return user_rank

    @staticmethod
    def pay_weekly_bonuses():
        """
        Weekly Celery task that pays rank bonuses.

        For each active UserRank where weeks_paid < 52:
        1. Calculate next week_number = weeks_paid + 1
        2. Check RankPayout for duplicate (belt-and-suspenders beyond unique_together)
        3. Credit Affiliate Wallet
        4. Create RankPayout record
        5. Increment weeks_paid
        6. Deactivate if weeks_paid reaches duration_weeks

        Runs inside a transaction per user-rank to isolate failures.
        """
        active_ranks = (
            UserRank.objects
            .select_related('user', 'rank')
            .filter(is_active=True)
            .annotate(max_weeks=F('rank__duration_weeks'))
        )

        paid = 0
        skipped_cap = 0
        skipped_duplicate = 0

        for ur in active_ranks:
            if ur.weeks_paid >= ur.rank.duration_weeks:
                UserRank.objects.filter(pk=ur.pk).update(is_active=False)
                continue

            week_num = ur.weeks_paid + 1

            try:
                with transaction.atomic():
                    # Duplicate guard — beyond the DB unique constraint
                    exists = RankPayout.objects.filter(
                        user=ur.user, rank=ur.rank, week_number=week_num,
                    ).exists()
                    if exists:
                        skipped_duplicate += 1
                        continue

                    amount = ur.rank.weekly_bonus

                    # Credit to Affiliate Wallet
                    WalletService.credit_system(
                        user=ur.user,
                        wallet_type=Wallet.WalletType.AFFILIATE,
                        amount=amount,
                        txn_type='rank_bonus',
                        description=f'{ur.rank.name} rank bonus — week {week_num}/52',
                    )

                    # Immutable payout record
                    RankPayout.objects.create(
                        user=ur.user,
                        rank=ur.rank,
                        week_number=week_num,
                        amount=amount,
                    )

                    # Update weeks_paid
                    new_weeks = ur.weeks_paid + 1
                    update_kwargs = {'weeks_paid': new_weeks}
                    if new_weeks >= ur.rank.duration_weeks:
                        update_kwargs['is_active'] = False

                    UserRank.objects.filter(pk=ur.pk).update(**update_kwargs)
                    paid += 1

            except IntegrityError:
                # Race condition — unique_together caught it
                skipped_duplicate += 1
                logger.warning('Duplicate rank payout attempt for user %s rank %s week %s',
                               ur.user.pk, ur.rank.pk, week_num)
            except Exception as exc:
                logger.error('Rank payout failed for UserRank %s: %s', ur.pk, exc)
                continue

        logger.info('Rank payouts — paid=%s skipped_dup=%s skipped_cap=%s', paid, skipped_duplicate, skipped_cap)
        return {'paid': paid, 'skipped_duplicate': skipped_duplicate}
