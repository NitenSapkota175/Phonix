from django.db import models
from decimal import Decimal


class Rank(models.Model):
    """
    User rank based on leg volumes for weekly bonus distribution.
    """
    
    NONE = 'none'
    CONNECTOR = 'connector'
    BUILDER = 'builder'
    PROFESSIONAL = 'professional'
    EXECUTIVE = 'executive'
    DIRECTOR = 'director'
    CROWN = 'crown'
    
    RANK_CHOICES = [
        (NONE, 'No Rank'),
        (CONNECTOR, 'Connector'),
        (BUILDER, 'Builder'),
        (PROFESSIONAL, 'Professional'),
        (EXECUTIVE, 'Executive'),
        (DIRECTOR, 'Director'),
        (CROWN, 'Crown'),
    ]
    
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='rank'
    )
    current_rank = models.CharField(
        max_length=20,
        choices=RANK_CHOICES,
        default=NONE
    )
    
    # Leg volumes
    main_leg_volume = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Volume of the largest leg"
    )
    other_legs_volume = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Combined volume of all other legs"
    )
    
    # Weekly bonus
    weekly_bonus_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Weekly bonus for current rank"
    )
    weeks_remaining = models.IntegerField(
        default=0,
        help_text="Weeks remaining for bonus payment (max 52)"
    )
    
    # Timestamps
    last_rank_check = models.DateTimeField(auto_now=True)
    rank_achieved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Rank'
        verbose_name_plural = 'Ranks'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_current_rank_display()}"
    
    def update_volumes(self, main_leg, other_legs):
        """Update leg volumes"""
        self.main_leg_volume = main_leg
        self.other_legs_volume = other_legs
        self.save()
    
    def check_rank_advancement(self):
        """
        Check if user qualifies for a higher rank based on leg volumes.
        Returns new rank if advanced, None otherwise.
        """
        from django.utils import timezone
        
        new_rank = self.calculate_rank()
        
        if new_rank != self.current_rank:
            self.current_rank = new_rank
            self.weekly_bonus_amount = RANK_BONUSES.get(new_rank, Decimal('0.00'))
            self.weeks_remaining = 52  # Reset to 52 weeks
            self.rank_achieved_at = timezone.now()
            self.save()
            return new_rank
        
        return None
    
    def calculate_rank(self):
        """Calculate rank based on current leg volumes"""
        # Check from highest to lowest rank
        for rank_name, requirements in RANK_REQUIREMENTS.items():
            main_req = requirements['main_leg']
            other_req = requirements['other_legs']
            
            if (self.main_leg_volume >= main_req and 
                self.other_legs_volume >= other_req):
                return rank_name
        
        return self.NONE


# Rank requirements (main_leg : other_legs)
RANK_REQUIREMENTS = {
    'crown': {
        'main_leg': Decimal('200000.00'),
        'other_legs': Decimal('200000.00'),
    },
    'director': {
        'main_leg': Decimal('100000.00'),
        'other_legs': Decimal('100000.00'),
    },
    'executive': {
        'main_leg': Decimal('50000.00'),
        'other_legs': Decimal('50000.00'),
    },
    'professional': {
        'main_leg': Decimal('20000.00'),
        'other_legs': Decimal('20000.00'),
    },
    'builder': {
        'main_leg': Decimal('10000.00'),
        'other_legs': Decimal('10000.00'),
    },
    'connector': {
        'main_leg': Decimal('5000.00'),
        'other_legs': Decimal('5000.00'),
    },
}

# Weekly bonus amounts for each rank
RANK_BONUSES = {
    'connector': Decimal('50.00'),
    'builder': Decimal('200.00'),
    'professional': Decimal('500.00'),
    'executive': Decimal('1000.00'),
    'director': Decimal('2000.00'),
    'crown': Decimal('5000.00'),
    'none': Decimal('0.00'),
}
