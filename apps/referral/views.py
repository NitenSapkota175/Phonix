"""
Referral views — binary tree dashboard and team list.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from apps.accounts.models import User
from .models import BinaryNode


class ReferralDashboardView(LoginRequiredMixin, View):
    template_name = 'referral/dashboard.html'

    def get(self, request):
        try:
            node = request.user.binary_node
        except BinaryNode.DoesNotExist:
            node = None

        direct_referrals = User.objects.filter(
            referred_by=request.user
        ).only('username', 'email', 'is_active_investor', 'joined_at')

        ctx = {
            'node': node,
            'direct_referrals': direct_referrals,
            'referral_code': request.user.referral_code,
            'total_directs': request.user.direct_referrals_count,
        }
        return render(request, self.template_name, ctx)


class TeamListView(LoginRequiredMixin, View):
    template_name = 'referral/team.html'

    def get(self, request):
        direct_referrals = User.objects.filter(
            referred_by=request.user
        ).select_related('binary_node').only(
            'username', 'email', 'is_active_investor', 'joined_at',
            'direct_referrals_count',
        )
        ctx = {
            'team_members': direct_referrals,
        }
        return render(request, self.template_name, ctx)
