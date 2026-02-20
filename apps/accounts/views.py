"""
Accounts views — login, register, email verification, profile, password management.
Business logic delegated to AccountService.
"""
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View

from apps.core.mixins import ServiceExceptionMixin
from apps.core.exceptions import InvalidOperationError
from .services import AccountService
from .models import User


class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        ref_code = request.GET.get('ref', '')
        return render(request, self.template_name, {'ref_code': ref_code})

    def post(self, request):
        data = request.POST
        try:
            user = AccountService.register_user(
                username=data.get('username', '').strip(),
                email=data.get('email', '').strip(),
                password=data.get('password', ''),
                referral_code=data.get('referral_code', '').strip() or None,
                phone=data.get('phone', '').strip(),
            )
            messages.success(request, 'Account created! Please check your email to verify your account.')
            return redirect('accounts:login')
        except InvalidOperationError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {'ref_code': data.get('referral_code', '')})


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return render(request, self.template_name)

    def post(self, request):
        from django.contrib.auth import authenticate
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        messages.error(request, 'Invalid username or password.')
        return render(request, self.template_name)


class LogoutView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        return redirect('accounts:login')


class VerifyEmailView(View):
    def get(self, request, token):
        try:
            AccountService.verify_email(token)
            messages.success(request, 'Email verified! You can now log in.')
        except InvalidOperationError as exc:
            messages.error(request, str(exc))
        return redirect('accounts:login')


class ProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        return render(request, self.template_name, {'user': request.user})

    def post(self, request):
        user = request.user
        user.phone = request.POST.get('phone', '').strip()
        user.save(update_fields=['phone'])
        messages.success(request, 'Profile updated.')
        return redirect('accounts:profile')


class ChangePasswordView(ServiceExceptionMixin, LoginRequiredMixin, View):
    template_name = 'accounts/change_password.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        AccountService.change_password(
            user=request.user,
            current_password=request.POST.get('current_password', ''),
            new_password=request.POST.get('new_password', ''),
        )
        messages.success(request, 'Password changed successfully. Please log in again.')
        logout(request)
        return redirect('accounts:login')


class SetTransactionPasswordView(ServiceExceptionMixin, LoginRequiredMixin, View):
    template_name = 'accounts/set_txn_password.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        AccountService.set_transaction_password(
            user=request.user,
            raw_password=request.POST.get('txn_password', ''),
            confirm_password=request.POST.get('confirm_txn_password', ''),
        )
        messages.success(request, 'Transaction password set successfully.')
        return redirect('accounts:profile')


class ResendVerificationView(LoginRequiredMixin, View):
    def post(self, request):
        if request.user.is_email_verified:
            messages.info(request, 'Your email is already verified.')
        else:
            AccountService.send_verification_email(request.user)
            messages.success(request, 'Verification email sent. Check your inbox.')
        return redirect('accounts:profile')
