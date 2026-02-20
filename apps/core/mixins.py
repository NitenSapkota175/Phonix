"""
Shared mixins for Phonix views.

Usage:
    class MyView(ServiceExceptionMixin, LoginRequiredMixin, View):
        ...
"""
from django.contrib import messages
from django.shortcuts import redirect

from apps.core.exceptions import (
    PhonixBaseError,
    InsufficientBalanceError,
    WithdrawalRateLimitError,
    MinimumWithdrawalError,
    KYCNotApprovedError,
    InvalidTransactionPasswordError,
)


class ServiceExceptionMixin:
    """
    Catches known service-layer exceptions and converts them to
    Django messages + redirects for template views.
    """
    error_redirect_url = None  # subclass can override

    def handle_service_error(self, request, exc, redirect_url=None):
        messages.error(request, str(exc))
        url = redirect_url or self.error_redirect_url or request.META.get('HTTP_REFERER', '/')
        return redirect(url)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except (
            InsufficientBalanceError,
            WithdrawalRateLimitError,
            MinimumWithdrawalError,
            KYCNotApprovedError,
            InvalidTransactionPasswordError,
            PhonixBaseError,
        ) as exc:
            return self.handle_service_error(request, exc)
