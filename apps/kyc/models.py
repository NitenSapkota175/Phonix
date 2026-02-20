"""
KYC models — document upload and admin approval workflow.
"""
from django.db import models
from apps.core.models import TimeStampedModel


class KYCDocument(TimeStampedModel):
    """
    One KYC record per user (OneToOne).
    Admin reviews and sets status to approved or rejected.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    class DocumentType(models.TextChoices):
        PASSPORT = 'passport', 'Passport'
        NATIONAL_ID = 'national_id', 'National ID'
        DRIVERS_LICENSE = 'drivers_license', "Driver's License"

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='kyc_document',
    )
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    front_image = models.ImageField(upload_to='kyc/front/%Y/%m/')
    back_image = models.ImageField(upload_to='kyc/back/%Y/%m/', blank=True)
    selfie_image = models.ImageField(upload_to='kyc/selfie/%Y/%m/', blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True,
    )
    admin_note = models.TextField(blank=True, help_text='Reason for rejection or approval note.')
    reviewed_by = models.ForeignKey(
        'accounts.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='kyc_reviews',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'KYC Document'
        verbose_name_plural = 'KYC Documents'
        indexes = [models.Index(fields=['status'])]

    def __str__(self):
        return f'{self.user.username} KYC — {self.status}'

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED
