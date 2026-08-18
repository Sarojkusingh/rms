from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_router, name='dashboard'),
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/institutions/', views.superadmin_institutions, name='superadmin_institutions'),
    path('superadmin/plans/', views.superadmin_plans, name='superadmin_plans'),
    path('superadmin/subscriptions/', views.superadmin_subscriptions, name='superadmin_subscriptions'),
    path('superadmin/payments/', views.superadmin_payments, name='superadmin_payments'),
    path('superadmin/support/', views.superadmin_support, name='superadmin_support'),
    path('superadmin/audit/', views.superadmin_audit, name='superadmin_audit'),
]
