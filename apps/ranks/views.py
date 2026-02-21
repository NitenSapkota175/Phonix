"""
Rank views — overview of all ranks with progress, payout history.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView

from .models import Rank, UserRank, RankPayout


class RankOverviewView(LoginRequiredMixin, View):
    template_name = 'ranks/overview.html'

    def get(self, request):
        all_ranks = Rank.objects.all()
        user_ranks = {
            ur.rank_id: ur
            for ur in UserRank.objects.filter(user=request.user)
        }

        # Build rank progress data
        try:
            node = request.user.binary_node
            left_vol = node.left_volume
            right_vol = node.right_volume
        except Exception:
            left_vol = right_vol = 0

        # Get highest achieved rank
        current_rank = None
        user_rank_objs = UserRank.objects.filter(
            user=request.user, is_active=True
        ).select_related('rank').order_by('-rank__level').first()
        if user_rank_objs:
            current_rank = user_rank_objs

        rank_data = []
        for rank in all_ranks:
            ur = user_ranks.get(rank.pk)
            rank_data.append({
                'rank': rank,
                'achieved': ur is not None,
                'user_rank': ur,
                'left_progress': min(100, int((left_vol / rank.left_target) * 100)) if rank.left_target else 0,
                'right_progress': min(100, int((right_vol / rank.right_target) * 100)) if rank.right_target else 0,
            })

        ctx = {
            'rank_data': rank_data,
            'current_rank': current_rank,
            'left_volume': left_vol,
            'right_volume': right_vol,
        }
        return render(request, self.template_name, ctx)


class RankPayoutListView(LoginRequiredMixin, ListView):
    model = RankPayout
    template_name = 'ranks/payouts.html'
    context_object_name = 'payouts'
    paginate_by = 20

    def get_queryset(self):
        return RankPayout.objects.filter(
            user=self.request.user
        ).select_related('rank')
