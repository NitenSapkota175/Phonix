"""
Transaction views — paginated/filtered transaction history.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView

from .models import Transaction


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/list.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user).select_related('wallet')
        txn_type = self.request.GET.get('type')
        status = self.request.GET.get('status')
        if txn_type:
            qs = qs.filter(txn_type=txn_type)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['txn_types'] = Transaction.TxnType.choices
        ctx['statuses'] = Transaction.TxnStatus.choices
        ctx['selected_type'] = self.request.GET.get('type', '')
        ctx['selected_status'] = self.request.GET.get('status', '')
        return ctx


class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = 'transactions/detail.html'
    context_object_name = 'txn'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
