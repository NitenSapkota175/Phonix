"""
Admin configuration for the KYC app.
"""
from django.contrib import admin
from django.utils import timezone
from .models import KYCDocument


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'document_type')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')
    list_select_related = ('user', 'reviewed_by')
    actions = ['approve_kyc', 'reject_kyc']

    @admin.action(description='Approve selected KYC documents')
    def approve_kyc(self, request, queryset):
        queryset.filter(status=KYCDocument.Status.PENDING).update(
            status=KYCDocument.Status.APPROVED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )

    @admin.action(description='Reject selected KYC documents')
    def reject_kyc(self, request, queryset):
        queryset.filter(status=KYCDocument.Status.PENDING).update(
            status=KYCDocument.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
