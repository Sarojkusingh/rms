from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:id>/', views.notification_detail, name='notification_detail'),
    path('notifications/read/<int:id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('notifications/read-all/', views.mark_all_notifications_as_read, name='mark_all_notifications_read'),
    path('notifications/read-all-as-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
]
