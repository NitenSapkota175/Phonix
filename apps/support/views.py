"""
Support views — ticket management with threaded replies.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView

from .models import Ticket, TicketReply


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'support/list.html'
    context_object_name = 'tickets'
    paginate_by = 10

    def get_queryset(self):
        qs = Ticket.objects.filter(user=self.request.user)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['statuses'] = Ticket.Status.choices
        ctx['selected_status'] = self.request.GET.get('status', '')
        return ctx


class TicketCreateView(LoginRequiredMixin, View):
    template_name = 'support/create.html'

    def get(self, request):
        return render(request, self.template_name, {
            'priorities': Ticket.Priority.choices,
        })

    def post(self, request):
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()
        priority = request.POST.get('priority', Ticket.Priority.MEDIUM)

        if not subject or not message_text:
            messages.error(request, 'Subject and message are required.')
            return render(request, self.template_name, {
                'priorities': Ticket.Priority.choices,
            })

        ticket = Ticket.objects.create(
            user=request.user,
            subject=subject,
            priority=priority,
        )
        # Create the initial message as a reply
        TicketReply.objects.create(
            ticket=ticket,
            author=request.user,
            message=message_text,
            is_staff_reply=False,
        )
        messages.success(request, f'Ticket #{ticket.ticket_number} created.')
        return redirect('support:detail', pk=ticket.pk)


class TicketDetailView(LoginRequiredMixin, View):
    template_name = 'support/detail.html'

    def get(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
        replies = ticket.replies.select_related('author').all()
        return render(request, self.template_name, {
            'ticket': ticket,
            'replies': replies,
        })

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
        message_text = request.POST.get('message', '').strip()

        if not message_text:
            messages.error(request, 'Reply cannot be empty.')
            return redirect('support:detail', pk=pk)

        if ticket.status == Ticket.Status.CLOSED:
            messages.error(request, 'This ticket is closed and cannot receive replies.')
            return redirect('support:detail', pk=pk)

        TicketReply.objects.create(
            ticket=ticket,
            author=request.user,
            message=message_text,
            is_staff_reply=request.user.is_support_role,
        )
        messages.success(request, 'Reply added.')
        return redirect('support:detail', pk=pk)
