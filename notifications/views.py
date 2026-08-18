from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.urls import reverse
from .models import Notification

@login_required
def mark_notification_as_read(request, id):
    """
    Marks a notification as read and redirects to referrer.
    """
    notification = get_object_or_404(Notification, id=id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def mark_all_notifications_as_read(request):
    """
    Marks all notifications for the user as read.
    """
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def notifications_list(request):
    """
    Lists all notifications for the logged-in user.
    Supports filtering by 'status' (unread, read).
    """
    status_filter = request.GET.get('status', 'all')
    notifications = Notification.objects.filter(user=request.user)

    if status_filter == 'unread':
        notifications = notifications.filter(is_read=False)
    elif status_filter == 'read':
        notifications = notifications.filter(is_read=True)

    # Order by newest first
    notifications = notifications.order_by('-created_at')

    paginator = Paginator(notifications, 15)  # 15 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'notifications/notifications_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'breadcrumbs': [{'name': 'Notifications', 'url': '#'}]
    })

@login_required
def notification_detail(request, id):
    """
    Marks the notification as read and shows its detail page.
    """
    notification = get_object_or_404(Notification, id=id, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()
        
    return render(request, 'notifications/notification_detail.html', {
        'notification': notification,
        'breadcrumbs': [
            {'name': 'Notifications', 'url': reverse('notifications_list')},
            {'name': f"Notification #{notification.id}", 'url': '#'}
        ]
    })

