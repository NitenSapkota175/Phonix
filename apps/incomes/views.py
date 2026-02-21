"""
Income views — paginated and filterable income history.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.views.generic import ListView

from .models import Income


class IncomeListView(LoginRequiredMixin, ListView):
    model = Income
    template_name = 'incomes/list.html'
    context_object_name = 'incomes'
    paginate_by = 20

    def get_queryset(self):
        qs = Income.objects.filter(user=self.request.user)
        income_type = self.request.GET.get('type')
        if income_type:
            qs = qs.filter(income_type=income_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['income_types'] = Income.IncomeType.choices
        ctx['selected_type'] = self.request.GET.get('type', '')

        # Aggregate totals by type
        totals = (
            Income.objects.filter(user=self.request.user)
            .values('income_type')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        ctx['income_totals'] = {t['income_type']: t['total'] for t in totals}
        ctx['grand_total'] = sum(t['total'] for t in totals)
        return ctx
