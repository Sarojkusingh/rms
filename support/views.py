from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SupportTicket
from audit.models import AuditLog

@login_required
def ticket_list(request):
    """
    Lists support tickets submitted by the institution, and handles new ticket submissions.
    """
    inst = request.user.institution
    tickets = SupportTicket.objects.filter(institution=inst, user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        priority = request.POST.get('priority')
        
        if subject and message and priority:
            try:
                ticket = SupportTicket.objects.create(
                    institution=inst,
                    user=request.user,
                    subject=subject,
                    message=message,
                    priority=priority,
                    status=SupportTicket.Status.OPEN
                )
                
                AuditLog.objects.create(
                    institution=inst,
                    user=request.user,
                    user_role=request.user.get_role_display(),
                    action=f"Created support ticket: {subject}.",
                    module="SUPPORT",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f"Support ticket #{ticket.id} created successfully! Our staff will review it shortly.")
                return redirect('ticket_list')
            except Exception as e:
                messages.error(request, f"Failed to submit ticket: {e}")
        else:
            messages.error(request, "Please enter all required fields.")
            
    return render(request, 'support/ticket_list.html', {
        'tickets': tickets,
        'priorities': SupportTicket.Priority.choices,
        'breadcrumbs': [{'name': 'Support Tickets', 'url': '#'}]
    })
