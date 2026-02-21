"""
KYC views — document upload and status display.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View

from .models import KYCDocument


class KYCView(LoginRequiredMixin, View):
    template_name = 'kyc/upload.html'

    def get(self, request):
        try:
            kyc = request.user.kyc_document
        except KYCDocument.DoesNotExist:
            kyc = None
        ctx = {
            'kyc': kyc,
            'document_types': KYCDocument.DocumentType.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        # Check if already approved
        try:
            existing = request.user.kyc_document
            if existing.is_approved:
                messages.info(request, 'Your KYC is already approved.')
                return redirect('kyc:upload')
            # Update existing submission
            existing.document_type = request.POST.get('document_type', '')
            if request.FILES.get('front_image'):
                existing.front_image = request.FILES['front_image']
            if request.FILES.get('back_image'):
                existing.back_image = request.FILES['back_image']
            if request.FILES.get('selfie_image'):
                existing.selfie_image = request.FILES['selfie_image']
            existing.status = KYCDocument.Status.PENDING
            existing.admin_note = ''
            existing.save()
            messages.success(request, 'KYC documents re-submitted for review.')
        except KYCDocument.DoesNotExist:
            # Create new submission
            KYCDocument.objects.create(
                user=request.user,
                document_type=request.POST.get('document_type', ''),
                front_image=request.FILES.get('front_image'),
                back_image=request.FILES.get('back_image'),
                selfie_image=request.FILES.get('selfie_image'),
            )
            messages.success(request, 'KYC documents submitted for review.')

        return redirect('kyc:upload')
