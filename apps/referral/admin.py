"""
Admin configuration for the referral app.
"""
from django.contrib import admin
from .models import BinaryNode


@admin.register(BinaryNode)
class BinaryNodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'parent', 'position', 'left_volume', 'right_volume',
                    'fresh_left_volume', 'fresh_right_volume')
    list_filter = ('position',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('left_volume', 'right_volume', 'fresh_left_volume',
                       'fresh_right_volume', 'created_at', 'updated_at')
    list_select_related = ('user', 'parent', 'left_child', 'right_child')
    raw_id_fields = ('user', 'parent', 'left_child', 'right_child')
