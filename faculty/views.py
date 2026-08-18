from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.db.models import Q
from django.contrib.auth import get_user_model
from academics.models import Department, Subject, Section, AcademicSession
from .models import Faculty, FacultySubject
from academics.views import admin_required
from audit.models import AuditLog

User = get_user_model()

@login_required
def faculty_list(request):
    inst = request.user.institution
    faculties = Faculty.objects.filter(institution=inst).select_related('user', 'department')
    
    # Filters
    dept_id = request.GET.get('department')
    q = request.GET.get('q', '')
    
    if dept_id:
        faculties = faculties.filter(department_id=dept_id)
    if q:
        faculties = faculties.filter(
            Q(user__first_name__icontains=q) | 
            Q(user__last_name__icontains=q) |
            Q(employee_id__icontains=q)
        )
        
    return render(request, 'faculty/faculty_list.html', {
        'faculties': faculties,
        'departments': Department.objects.filter(institution=inst),
        'dept_filter': int(dept_id) if dept_id else '',
        'q': q,
        'breadcrumbs': [{'name': 'Faculty', 'url': '#'}]
    })

@login_required
@admin_required
def faculty_add(request):
    inst = request.user.institution
    depts = Department.objects.filter(institution=inst)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        emp_id = request.POST.get('employee_id')
        dept_id = request.POST.get('department')
        designation = request.POST.get('designation')
        qualification = request.POST.get('qualification')
        joining_date = request.POST.get('joining_date')
        
        if username and email and password and emp_id and dept_id:
            dept = get_object_or_404(Department, id=dept_id, institution=inst)
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        role=User.Role.FACULTY,
                        institution=inst
                    )
                    
                    faculty = Faculty.objects.create(
                        institution=inst,
                        user=user,
                        employee_id=emp_id,
                        department=dept,
                        designation=designation,
                        qualification=qualification,
                        joining_date=joining_date if joining_date else None
                    )
                    
                    AuditLog.objects.create(
                        institution=inst,
                        user=request.user,
                        user_role=request.user.get_role_display(),
                        action=f"Created faculty profile: {emp_id}.",
                        module="FACULTY",
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                messages.success(request, f"Faculty '{first_name} {last_name}' registered successfully.")
                if 'add_another' in request.POST:
                    return redirect('faculty_add')
                return redirect('faculty_list')
            except Exception as e:
                messages.error(request, f"Failed to register faculty: {e}")
        else:
            messages.error(request, "All required fields must be completed.")
            
    return render(request, 'faculty/faculty_form.html', {
        'title': 'Add Faculty',
        'departments': depts,
        'breadcrumbs': [{'name': 'Faculty', 'url': '/faculty/'}, {'name': 'Add Faculty', 'url': '#'}]
    })

@login_required
@admin_required
def faculty_edit(request, id):
    inst = request.user.institution
    faculty = get_object_or_404(Faculty, id=id, institution=inst)
    depts = Department.objects.filter(institution=inst)
    
    if request.method == 'POST':
        faculty.user.first_name = request.POST.get('first_name')
        faculty.user.last_name = request.POST.get('last_name')
        faculty.user.email = request.POST.get('email')
        faculty.user.save()
        
        dept_id = request.POST.get('department')
        faculty.department = get_object_or_404(Department, id=dept_id, institution=inst)
        faculty.designation = request.POST.get('designation')
        faculty.qualification = request.POST.get('qualification')
        j_date = request.POST.get('joining_date')
        faculty.joining_date = j_date if j_date else None
        faculty.save()
        
        AuditLog.objects.create(
            institution=inst,
            user=request.user,
            user_role=request.user.get_role_display(),
            action=f"Edited faculty profile: {faculty.employee_id}.",
            module="FACULTY",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, "Faculty profile updated successfully.")
        return redirect('faculty_list')
        
    return render(request, 'faculty/faculty_form.html', {
        'title': 'Edit Faculty',
        'faculty': faculty,
        'departments': depts,
        'breadcrumbs': [{'name': 'Faculty', 'url': '/faculty/'}, {'name': 'Edit Faculty', 'url': '#'}]
    })

@login_required
def faculty_profile(request, id):
    inst = request.user.institution
    faculty = get_object_or_404(Faculty, id=id, institution=inst)
    
    # Security: A faculty user can only see their own profile
    if request.user.role == User.Role.FACULTY and request.user.faculty_profile.id != faculty.id:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    return render(request, 'faculty/faculty_profile.html', {
        'faculty': faculty,
        'breadcrumbs': [{'name': 'Faculty', 'url': '/faculty/'}, {'name': 'Profile', 'url': '#'}]
    })

@login_required
@admin_required
def faculty_allocation(request):
    inst = request.user.institution
    faculties = Faculty.objects.filter(institution=inst)
    subjects = Subject.objects.filter(institution=inst)
    sections = Section.objects.filter(institution=inst)
    allocations = FacultySubject.objects.filter(institution=inst).select_related('faculty__user', 'subject', 'section')
    
    if request.method == 'POST':
        fac_id = request.POST.get('faculty')
        sub_id = request.POST.get('subject')
        sec_id = request.POST.get('section')
        
        if fac_id and sub_id:
            faculty = get_object_or_404(Faculty, id=fac_id, institution=inst)
            subject = get_object_or_404(Subject, id=sub_id, institution=inst)
            section = get_object_or_404(Section, id=sec_id, institution=inst) if sec_id else None
            active_session = inst.settings.current_session
            
            if not active_session:
                messages.error(request, "Configure an active academic session first.")
                return redirect('faculty_allocation')
                
            try:
                FacultySubject.objects.create(
                    institution=inst,
                    faculty=faculty,
                    subject=subject,
                    section=section,
                    academic_session=active_session
                )
                
                AuditLog.objects.create(
                    institution=inst,
                    user=request.user,
                    user_role=request.user.get_role_display(),
                    action=f"Allocated subject {subject.code} to faculty {faculty.employee_id}.",
                    module="FACULTY",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f"Allocated '{subject.name}' to faculty '{faculty.user.get_full_name()}' successfully.")
                return redirect('faculty_allocation')
            except Exception as e:
                messages.error(request, f"Allocation failed: Subject is already allocated to a faculty for this section.")
                return redirect('faculty_allocation')
                
    return render(request, 'faculty/faculty_allocation.html', {
        'faculties': faculties,
        'subjects': subjects,
        'sections': sections,
        'allocations': allocations,
        'breadcrumbs': [{'name': 'Faculty', 'url': '/faculty/'}, {'name': 'Subject Allocation', 'url': '#'}]
    })
