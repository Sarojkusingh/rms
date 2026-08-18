from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Notification
from .context_processors import unread_notifications

User = get_user_model()

class NotificationTests(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
            role=User.Role.SUPER_ADMIN
        )
        # Create some notifications
        self.notif1 = Notification.objects.create(
            user=self.user,
            title="Notification 1",
            message="Message 1",
            is_read=False
        )
        self.notif2 = Notification.objects.create(
            user=self.user,
            title="Notification 2",
            message="Message 2",
            is_read=True
        )

    def test_context_processor(self):
        # Test context processor values
        class DummyRequest:
            def __init__(self, user):
                self.user = user
        
        request = DummyRequest(self.user)
        context = unread_notifications(request)
        self.assertIn('unread_notifications', context)
        self.assertIn('unread_notifications_list', context)
        self.assertIn('unread_notifications_count', context)
        self.assertEqual(context['unread_notifications_count'], 1)
        self.assertEqual(context['unread_notifications_list'].first(), self.notif1)

    def test_login_required(self):
        # Verify views require login
        response = self.client.get(reverse('notifications_list'))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('notification_detail', args=[self.notif1.id]))
        self.assertEqual(response.status_code, 302)

    def test_notifications_list_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse('notifications_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notification 1")
        self.assertContains(response, "Notification 2")

    def test_notification_detail_view(self):
        self.client.login(username="testuser", password="testpassword")
        # Detail view for unread notification should mark it as read
        response = self.client.get(reverse('notification_detail', args=[self.notif1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notification 1")
        self.assertContains(response, "Message 1")
        
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    def test_mark_notification_as_read(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse('mark_notification_as_read', args=[self.notif1.id]))
        # Should redirect
        self.assertEqual(response.status_code, 302)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    def test_mark_all_notifications_read(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse('mark_all_notifications_read'))
        # Should redirect
        self.assertEqual(response.status_code, 302)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

