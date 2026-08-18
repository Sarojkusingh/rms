from django.urls import path
from . import views

urlpatterns = [
    path('billing/', views.billing_dashboard, name='billing_dashboard'),
    path('billing/checkout/<int:plan_id>/', views.checkout_mock, name='checkout_mock'),
]
