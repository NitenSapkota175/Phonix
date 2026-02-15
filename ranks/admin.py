from django.contrib import admin
from .models import Rank


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    """Admin interface for Rank model"""
    
    list_display = [
        'user', 'current_rank', 'main_leg_volume', 'other_legs_volume',
        'weekly_bonus_amount', 'weeks_remaining', 'last_rank_check'
    ]
    
    list_filter = ['current_rank', 'last_rank_check']
    
    search_fields = ['user__username', 'user__email']
    
    readonly_fields = ['last_rank_check', 'rank_achieved_at']
    
    fieldsets = (
        ('User & Rank', {
            'fields': ('user', 'current_rank', 'rank_achieved_at')
        }),
        ('Leg Volumes', {
            'fields': ('main_leg_volume', 'other_legs_volume')
        }),
        ('Weekly Bonus', {
            'fields': ('weekly_bonus_amount', 'weeks_remaining')
        }),
        ('Timestamps', {
            'fields': ('last_rank_check',)
        }),
    )
