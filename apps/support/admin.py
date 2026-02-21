"""
Admin configuration for the support app.
"""
from django.contrib import admin
from .models import Ticket, TicketReply


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1
    readonly_fields = ('created_at',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'user', 'subject', 'status',
                    'priority', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('ticket_number', 'user__username', 'subject')
    readonly_fields = ('ticket_number', 'created_at', 'updated_at')
    list_select_related = ('user', 'assigned_to')
    inlines = [TicketReplyInline]
    actions = ['mark_resolved', 'mark_closed']

    @admin.action(description='Mark selected tickets as resolved')
    def mark_resolved(self, request, queryset):
        queryset.update(status=Ticket.Status.RESOLVED)

    @admin.action(description='Mark selected tickets as closed')
    def mark_closed(self, request, queryset):
        queryset.update(status=Ticket.Status.CLOSED)
