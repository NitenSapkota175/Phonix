"""
Admin configuration for the ranks app.
"""
from django.contrib import admin
from .models import Rank, UserRank, RankPayout


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ('level', 'name', 'left_target', 'right_target',
                    'weekly_bonus', 'duration_weeks', 'is_asymmetric')
    ordering = ('level',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserRank)
class UserRankAdmin(admin.ModelAdmin):
    list_display = ('user', 'rank', 'achieved_date', 'weeks_paid', 'is_active')
    list_filter = ('is_active', 'rank')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('achieved_date', 'created_at', 'updated_at')
    list_select_related = ('user', 'rank')


@admin.register(RankPayout)
class RankPayoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'rank', 'week_number', 'amount', 'paid_at')
    list_filter = ('rank',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('paid_at', 'created_at', 'updated_at')
    list_select_related = ('user', 'rank')
