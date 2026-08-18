from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.contrib.auth import get_user_model
from .models import Institution, InstitutionSettings
from students.models import Student
from faculty.models import Faculty
from academics.models import Department, Program
from examinations.models import Examination
from marks.models import Marks
from results.models import Result
from backlogs.models import Backlog
from support.models import SupportTicket
from audit.models import AuditLog
from subscriptions.models import Plan, Subscription, Usage
from payments.models import Payment

User = get_user_model()

@login_required
def dashboard_router(request):
    """
    Unified entry point for the /dashboard/ URL. 
    Routes the request to the role-specific dashboard template.
    """
    user = request.user
    
    if user.is_super_admin:
        return redirect('superadmin_dashboard')
        
    inst = user.institution
    if not inst:
        messages.error(request, "Your account is not mapped to an active institution.")
        return redirect('logout')
        
    settings = getattr(inst, 'settings', None)
    if settings and not settings.is_onboarded and (user.role in [User.Role.INSTITUTION_OWNER, User.Role.INSTITUTION_ADMIN]):
        messages.info(request, "Please complete your institution setup wizard first.")
        return redirect('onboarding_wizard')
        
    # Gather role-based statistics
    if user.role in [User.Role.INSTITUTION_OWNER, User.Role.INSTITUTION_ADMIN]:
        # Institution Admin Dashboard
        context = {
            'total_students': Student.objects.filter(institution=inst).count(),
            'total_faculty': Faculty.objects.filter(institution=inst).count(),
            'total_depts': Department.objects.filter(institution=inst).count(),
            'total_progs': Program.objects.filter(institution=inst).count(),
            'active_exams': Examination.objects.filter(institution=inst, status=Examination.Status.ACTIVE).count(),
            'recent_exams': Examination.objects.filter(institution=inst).order_by('-created_at')[:5],
            'pending_marks': Marks.objects.filter(institution=inst, status=Marks.Status.SUBMITTED).count(),
            'published_results': Result.objects.filter(institution=inst, status=Result.Status.PUBLISHED).count(),
            'backlogs_count': Backlog.objects.filter(institution=inst, status=Backlog.Status.ACTIVE).count()
        }
        return render(request, 'institution/dashboard.html', context)
        
    elif user.role == User.Role.EXAM_CONTROLLER:
        # Exam Controller Dashboard
        context = {
            'total_exams': Examination.objects.filter(institution=inst).count(),
            'active_exams': Examination.objects.filter(institution=inst, status=Examination.Status.ACTIVE),
            'pending_locks': Marks.objects.filter(institution=inst, status=Marks.Status.APPROVED).values('subject__code', 'subject__name').annotate(count=models.Count('id')),
            'active_backlogs': Backlog.objects.filter(institution=inst, status=Backlog.Status.ACTIVE).count(),
            'pending_revals': Marks.objects.filter(institution=inst, revaluation_applications__status='APPLIED').count()
        }
        return render(request, 'examinations/dashboard.html', context)
        
    elif user.role == User.Role.HOD:
        # HOD Dashboard
        dept = user.faculty_profile.department
        context = {
            'dept': dept,
            'total_students': Student.objects.filter(institution=inst, department=dept).count(),
            'total_faculty': Faculty.objects.filter(institution=inst, department=dept).count(),
            'pending_approvals': Marks.objects.filter(institution=inst, status=Marks.Status.SUBMITTED, subject__program__department=dept).values('subject__code', 'subject__name').annotate(count=models.Count('id')),
            'recent_results': Result.objects.filter(institution=inst, student__department=dept).order_by('-updated_at')[:5]
        }
        return render(request, 'faculty/hod_dashboard.html', context)
        
    elif user.role == User.Role.FACULTY:
        # Faculty Dashboard
        from faculty.models import FacultySubject
        allocations = FacultySubject.objects.filter(faculty=user.faculty_profile, academic_session=inst.settings.current_session)
        
        context = {
            'allocations': allocations,
            'pending_entries': Marks.objects.filter(institution=inst, entered_by=user, status=Marks.Status.DRAFT).count(),
            'submitted_sheets': Marks.objects.filter(institution=inst, entered_by=user, status=Marks.Status.SUBMITTED).count()
        }
        return render(request, 'faculty/dashboard.html', context)
        
    elif user.role == User.Role.STUDENT:
        # Student Dashboard
        from students.models import StudentAcademicHistory
        student = user.student
        history, _ = StudentAcademicHistory.objects.get_or_create(
            student=student,
            defaults={'cgpa': 0.0, 'total_credits_completed': 0}
        )
        latest_result = Result.objects.filter(student=student, status=Result.Status.PUBLISHED).order_by('-published_at').first()
        if latest_result and history.cgpa == 0.0:
            history.cgpa = latest_result.cgpa
            history.total_credits_completed = latest_result.earned_credits
            history.save()

        active_backlogs = Backlog.objects.filter(student=student, status=Backlog.Status.ACTIVE)
        
        context = {
            'student': student,
            'history': history,
            'latest_result': latest_result,
            'active_backlogs_count': active_backlogs.count(),
            'recent_notifications': user.user_notifications.all()[:5]
        }
        return render(request, 'students/dashboard.html', context)
        
    return redirect('logout')


# --- SUPER ADMIN PORTAL VIEWS ---

@login_required
def superadmin_dashboard(request):
    if not request.user.is_super_admin:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    # Aggregate platform KPIs
    context = {
        'total_institutions': Institution.objects.count(),
        'active_institutions': Institution.objects.filter(is_active=True).count(),
        'suspended_institutions': Institution.objects.filter(is_active=False).count(),
        'trial_subs': Subscription.objects.filter(status=Subscription.Status.TRIAL).count(),
        'total_students': Student.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'mrr': Subscription.objects.filter(status=Subscription.Status.ACTIVE).aggregate(total=models.Sum('plan__price_monthly'))['total'] or 0.0,
        'recent_activity': AuditLog.objects.all()[:10],
        'breadcrumbs': [{'name': 'SuperAdmin Dashboard', 'url': '#'}]
    }
    return render(request, 'superadmin/dashboard.html', context)

@login_required
def superadmin_institutions(request):
    if not request.user.is_super_admin:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    institutions = Institution.objects.all()
    plans = Plan.objects.filter(is_active=True)
    
    # POST to update plan / suspend / activate
    if request.method == 'POST':
        action = request.POST.get('action')
        inst_id = request.POST.get('institution_id')
        inst = get_object_or_404(Institution, id=inst_id)
        
        if action == 'suspend':
            inst.is_active = False
            inst.save()
            messages.warning(request, f"Institution '{inst.name}' has been suspended.")
        elif action == 'activate':
            inst.is_active = True
            inst.save()
            messages.success(request, f"Institution '{inst.name}' has been activated.")
        elif action == 'change_plan':
            plan_id = request.POST.get('plan')
            plan = get_object_or_404(Plan, id=plan_id)
            # Update subscription
            sub = inst.subscription
            sub.plan = plan
            sub.save()
            messages.success(request, f"Subscription plan for '{inst.name}' upgraded to {plan.name}.")
            
        return redirect('superadmin_institutions')
        
    return render(request, 'superadmin/institutions.html', {
        'institutions': institutions,
        'plans': plans,
        'breadcrumbs': [{'name': 'Institutions List', 'url': '#'}]
    })

@login_required
def superadmin_plans(request):
    if not request.user.is_super_admin:
        return redirect('dashboard')
    plans = Plan.objects.all()
    return render(request, 'superadmin/plans.html', {'plans': plans, 'breadcrumbs': [{'name': 'Pricing Plans', 'url': '#'}]})

@login_required
def superadmin_subscriptions(request):
    if not request.user.is_super_admin:
        return redirect('dashboard')
    subs = Subscription.objects.all().select_related('institution', 'plan')
    return render(request, 'superadmin/subscriptions.html', {'subscriptions': subs, 'breadcrumbs': [{'name': 'Subscriptions log', 'url': '#'}]})

@login_required
def superadmin_payments(request):
    if not request.user.is_super_admin:
        return redirect('dashboard')
    payments = Payment.objects.all().select_related('institution')
    return render(request, 'superadmin/payments.html', {'payments': payments, 'breadcrumbs': [{'name': 'Payments Ledger', 'url': '#'}]})

@login_required
def superadmin_support(request):
    if not request.user.is_super_admin:
        return redirect('dashboard')
    tickets = SupportTicket.objects.all().select_related('institution', 'user')
    return render(request, 'superadmin/support.html', {'tickets': tickets, 'breadcrumbs': [{'name': 'Support Queue', 'url': '#'}]})

@login_required
def superadmin_audit(request):
    if not request.user.is_super_admin:
        return redirect('dashboard')
    logs = AuditLog.objects.all().select_related('institution', 'user')
    return render(request, 'superadmin/audit.html', {'logs': logs, 'breadcrumbs': [{'name': 'Global Audit logs', 'url': '#'}]})
