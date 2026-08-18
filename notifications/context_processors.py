from .models import Notification

def unread_notifications(request):
    """
    Injects unread notifications count and list for authenticated users globally.
    """
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
        return {
            'unread_notifications': unread_notifications,
            'unread_notifications_list': unread_notifications,
            'unread_notifications_count': unread_notifications.count()
        }
    return {}
