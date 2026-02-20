"""
Referral models — Binary MLM tree structure and income tracking.

BinaryNode: One per user.
- parent, left_child, right_child define the binary tree
- left_volume, right_volume are cumulative and indexed for rank queries
- fresh_left_volume, fresh_right_volume reset weekly for matching bonus
"""
from decimal import Decimal
from django.db import models
from apps.core.models import TimeStampedModel


class BinaryNode(TimeStampedModel):
    """
    Binary tree node for the MLM structure.
    Each user has exactly one BinaryNode (OneToOne).
    """

    class Position(models.TextChoices):
        LEFT = 'left', 'Left'
        RIGHT = 'right', 'Right'

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='binary_node',
    )
    parent = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
    )
    left_child = models.OneToOneField(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='left_of',
    )
    right_child = models.OneToOneField(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='right_of',
    )
    position = models.CharField(
        max_length=5,
        choices=Position.choices,
        blank=True,
        help_text='Which leg of the parent this node is on.',
    )

    # ── Cumulative volumes (never reset) ──────────────────────────────────────
    left_volume = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal('0.00'),
    )
    right_volume = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal('0.00'),
    )

    # ── Fresh volumes (reset weekly for matching bonus calculation) ────────────
    fresh_left_volume = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal('0.00'),
    )
    fresh_right_volume = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal('0.00'),
    )

    class Meta:
        verbose_name = 'Binary Node'
        verbose_name_plural = 'Binary Nodes'
        indexes = [
            models.Index(fields=['left_volume']),
            models.Index(fields=['right_volume']),
            models.Index(fields=['fresh_left_volume']),
            models.Index(fields=['fresh_right_volume']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f'BinaryNode({self.user.username}, L={self.left_volume}, R={self.right_volume})'

    @property
    def power_leg_volume(self) -> Decimal:
        """The leg with the larger cumulative volume."""
        return max(self.left_volume, self.right_volume)

    @property
    def other_leg_volume(self) -> Decimal:
        """The leg with the smaller cumulative volume."""
        return min(self.left_volume, self.right_volume)

    @property
    def total_team_volume(self) -> Decimal:
        return self.left_volume + self.right_volume
