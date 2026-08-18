from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from tenants.models import Institution
from payments.models import Payment
from students.models import Student
from faculty.models import Faculty
from .models import Plan, Subscription, Usage
from academics.views import admin_required
from audit.models import AuditLog

@login_required
@admin_required
def billing_dashboard(request):
    """
    Renders active subscription plan details, limits usage progress bars, 
    and transaction ledgers.
    """
    inst = request.user.institution
    sub = getattr(inst, 'subscription', None)
    
    if not sub:
        # Default fallback subscription
        default_plan = Plan.objects.filter(is_active=True).first()
        sub = Subscription.objects.create(
            institution=inst,
            plan=default_plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            next_billing_date=timezone.now() + timedelta(days=30),
            status=Subscription.Status.TRIAL
        )
        
    # Calculate limits progress percentages
    students_count = Student.objects.filter(institution=inst).count()
    faculty_count = Faculty.objects.filter(institution=inst).count()
    
    max_students = sub.plan.student_limit
    max_faculty = sub.plan.faculty_limit
    
    students_pct = min(int((students_count / max_students) * 100), 100) if max_students > 0 else 100
    faculty_pct = min(int((faculty_count / max_faculty) * 100), 100) if max_faculty > 0 else 100
    
    # Fetch billing history
    payments = Payment.objects.filter(institution=inst).order_by('-created_at')
    plans = Plan.objects.filter(is_active=True)
    
    return render(request, 'subscriptions/billing_dashboard.html', {
        'subscription': sub,
        'students_count': students_count,
        'faculty_count': faculty_count,
        'students_pct': students_pct,
        'faculty_pct': faculty_pct,
        'payments': payments,
        'plans': plans,
        'breadcrumbs': [{'name': 'Settings', 'url': '#'}, {'name': 'Billing', 'url': '#'}]
    })

@login_required
@admin_required
def checkout_mock(request, plan_id):
    """
    Simulates Stripe credit card payment and upgrades plan.
    """
    inst = request.user.institution
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)
    
    if request.method == 'POST':
        # Simulate payment confirmation
        card_name = request.POST.get('card_holder')
        card_number = request.POST.get('card_number')
        
        if card_name and card_number:
            try:
                with transaction.atomic():
                    # 1. Update/Extend Subscription
                    sub = inst.subscription
                    sub.plan = plan
                    sub.start_date = timezone.now()
                    sub.end_date = timezone.now() + timedelta(days=30)
                    sub.status = Subscription.Status.ACTIVE
                    sub.save()
                    
                    # 2. Record payment transaction
                    Payment.objects.create(
                        institution=inst,
                        amount=plan.price_monthly,
                        transaction_id=f"TXN-MOCK-{timezone.now().timestamp():.0f}",
                        status=Payment.Status.SUCCESS
                    )
                    
                    AuditLog.objects.create(
                        institution=inst,
                        user=request.user,
                        user_role=request.user.get_role_display(),
                        action=f"Upgraded subscription to plan '{plan.name}' (mock charge ${plan.price_monthly}).",
                        module="SUBSCRIPTIONS",
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                messages.success(request, f"Billing update successful! Plan upgraded to '{plan.name}'.")
                return redirect('billing_dashboard')
            except Exception as e:
                messages.error(request, f"Checkout failed: {e}")
        else:
            messages.error(request, "Enter credit card parameters to complete mock checkout.")
            
    return render(request, 'subscriptions/checkout_mock.html', {
        'plan': plan,
        'breadcrumbs': [{'name': 'Billing', 'url': '/billing/'}, {'name': 'Checkout', 'url': '#'}]
    })
