"""
Support models — ticket system with threaded replies.
"""
import uuid
from django.db import models
from apps.core.models import TimeStampedModel


class Ticket(TimeStampedModel):

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='tickets',
    )
    ticket_number = models.CharField(max_length=20, unique=True)
    subject = models.CharField(max_length=200)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.OPEN, db_index=True,
    )
    priority = models.CharField(
        max_length=8, choices=Priority.choices, default=Priority.MEDIUM,
    )
    assigned_to = models.ForeignKey(
        'accounts.User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='assigned_tickets',
    )

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', '-created_at']),
            models.Index(fields=['status', 'priority']),
        ]

    def __str__(self):
        return f'#{self.ticket_number} — {self.subject} [{self.status}]'

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f'TKT-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)


class TicketReply(TimeStampedModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='support/attachments/%Y/%m/', blank=True)

    class Meta:
        verbose_name = 'Ticket Reply'
        ordering = ['created_at']

    def __str__(self):
        return f'Reply to #{self.ticket.ticket_number} by {self.author.username}'
