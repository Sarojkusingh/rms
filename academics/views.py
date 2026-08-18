from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model
from tenants.models import Institution, InstitutionSettings
from .models import AcademicSession, Department, Program, Course, Semester, Subject, Section
from students.models import Student, StudentAcademicHistory
from faculty.models import Faculty
from django.http import Http404

User = get_user_model()

# Custom Decorator to enforce Institution Admin/Owner access
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_super_admin and not request.user.is_institution_admin:
            messages.error(request, "Permission Denied: Admin access required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@admin_required
def onboarding_wizard(request):
    inst = request.user.institution
    settings = inst.settings
    
    # Get current step, default to what is in database
    current_step = settings.onboarding_step
    
    # Allow requesting a previous step via query parameter, but block skipping ahead
    requested_step = request.GET.get('step')
    if requested_step:
        try:
            requested_step = int(requested_step)
            if 1 <= requested_step <= current_step:
                step = requested_step
            else:
                step = current_step
        except ValueError:
            step = current_step
    else:
        step = current_step
        
    context = {
        'step': step,
        'onboarding_step': current_step,
        'institution': inst,
        'settings': settings,
        'progress_percent': int((step - 1) * 11.1),  # 9 transitional points to 10th step
    }

    if request.method == 'POST':
        if step == 1:
            # Step 1: Update Institution Profile
            inst.name = request.POST.get('name')
            inst.contact_phone = request.POST.get('contact_phone')
            inst.address = request.POST.get('address')
            if request.FILES.get('logo'):
                inst.logo = request.FILES.get('logo')
            inst.save()
            
            # Advance onboarding if we are at the front edge of progress
            if current_step == 1:
                settings.onboarding_step = 2
                settings.save()
            return redirect('/onboarding/?step=2')
            
        elif step == 2:
            # Step 2: Create Academic Session
            session_name = request.POST.get('session_name')
            if session_name:
                session, _ = AcademicSession.objects.get_or_create(
                    institution=inst, 
                    name=session_name,
                    defaults={'is_active': True}
                )
                settings.current_session = session
                settings.save()
                
                if current_step == 2:
                    settings.onboarding_step = 3
                    settings.save()
                return redirect('/onboarding/?step=3')
            else:
                messages.error(request, "Academic session name is required.")
                
        elif step == 3:
            # Step 3: Create Department
            dept_name = request.POST.get('dept_name')
            dept_code = request.POST.get('dept_code')
            if dept_name and dept_code:
                Department.objects.get_or_create(
                    institution=inst,
                    code=dept_code.upper(),
                    defaults={'name': dept_name}
                )
                
                # Check if they want to add another or move next
                if 'add_another' in request.POST:
                    messages.success(request, f"Department '{dept_name}' added successfully.")
                    return redirect('/onboarding/?step=3')
                
                if current_step == 3:
                    settings.onboarding_step = 4
                    settings.save()
                return redirect('/onboarding/?step=4')
            else:
                messages.error(request, "Both name and code are required.")
                
        elif step == 4:
            # Step 4: Create Program
            dept_id = request.POST.get('department')
            prog_name = request.POST.get('prog_name')
            prog_code = request.POST.get('prog_code')
            duration = request.POST.get('duration_years', 4)
            if dept_id and prog_name and prog_code:
                dept = get_object_or_404(Department, id=dept_id, institution=inst)
                Program.objects.get_or_create(
                    institution=inst,
                    department=dept,
                    code=prog_code.upper(),
                    defaults={'name': prog_name, 'duration_years': int(duration)}
                )
                
                if 'add_another' in request.POST:
                    messages.success(request, f"Program '{prog_name}' added successfully.")
                    return redirect('/onboarding/?step=4')
                
                if current_step == 4:
                    settings.onboarding_step = 5
                    settings.save()
                return redirect('/onboarding/?step=5')
            else:
                messages.error(request, "All fields are required.")
                
        elif step == 5:
            # Step 5: Configure Semesters for Programs
            program_ids = request.POST.getlist('programs')
            if program_ids:
                with transaction.atomic():
                    for pid in program_ids:
                        prog = get_object_or_404(Program, id=pid, institution=inst)
                        # Create semesters based on duration_years (2 semesters per year)
                        num_semesters = prog.duration_years * 2
                        for s_num in range(1, num_semesters + 1):
                            Semester.objects.get_or_create(
                                institution=inst,
                                program=prog,
                                number=s_num
                            )
                
                if current_step == 5:
                    settings.onboarding_step = 6
                    settings.save()
                return redirect('/onboarding/?step=6')
            else:
                messages.error(request, "Select at least one program to create semesters.")
                
        elif step == 6:
            # Step 6: Create Subject
            prog_id = request.POST.get('program')
            sem_id = request.POST.get('semester')
            sub_name = request.POST.get('sub_name')
            sub_code = request.POST.get('sub_code')
            credits = request.POST.get('credits', 4)
            if prog_id and sem_id and sub_name and sub_code:
                prog = get_object_or_404(Program, id=prog_id, institution=inst)
                sem = get_object_or_404(Semester, id=sem_id, program=prog)
                Subject.objects.get_or_create(
                    institution=inst,
                    program=prog,
                    semester=sem,
                    code=sub_code.upper(),
                    defaults={'name': sub_name, 'credits': int(credits)}
                )
                
                if 'add_another' in request.POST:
                    messages.success(request, f"Subject '{sub_name}' added.")
                    return redirect('/onboarding/?step=6')
                
                if current_step == 6:
                    settings.onboarding_step = 7
                    settings.save()
                return redirect('/onboarding/?step=7')
            else:
                messages.error(request, "All fields are required.")
                
        elif step == 7:
            # Step 7: Create Faculty Profile
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            emp_id = request.POST.get('employee_id')
            dept_id = request.POST.get('department')
            designation = request.POST.get('designation')
            if username and email and password and emp_id and dept_id:
                dept = get_object_or_404(Department, id=dept_id, institution=inst)
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        role=User.Role.FACULTY,
                        institution=inst
                    )
                    Faculty.objects.create(
                        institution=inst,
                        user=user,
                        employee_id=emp_id,
                        department=dept,
                        designation=designation
                    )
                
                if 'add_another' in request.POST:
                    messages.success(request, f"Faculty member '{username}' registered.")
                    return redirect('/onboarding/?step=7')
                
                if current_step == 7:
                    settings.onboarding_step = 8
                    settings.save()
                return redirect('/onboarding/?step=8')
            else:
                messages.error(request, "All fields are required.")
                
        elif step == 8:
            # Step 8: Create Student Profile
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            student_id = request.POST.get('student_id')
            dept_id = request.POST.get('department')
            prog_id = request.POST.get('program')
            sem_id = request.POST.get('semester')
            if username and email and password and student_id and dept_id and prog_id and sem_id:
                dept = get_object_or_404(Department, id=dept_id, institution=inst)
                prog = get_object_or_404(Program, id=prog_id, institution=inst)
                sem = get_object_or_404(Semester, id=sem_id, program=prog)
                
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        role=User.Role.STUDENT,
                        institution=inst
                    )
                    student = Student.objects.create(
                        institution=inst,
                        user=user,
                        student_id=student_id,
                        department=dept,
                        program=prog,
                        semester=sem,
                        academic_session=settings.current_session
                    )
                    StudentAcademicHistory.objects.get_or_create(student=student)
                
                if 'add_another' in request.POST:
                    messages.success(request, f"Student '{username}' registered.")
                    return redirect('/onboarding/?step=8')
                
                if current_step == 8:
                    settings.onboarding_step = 9
                    settings.save()
                return redirect('/onboarding/?step=9')
            else:
                messages.error(request, "All fields are required.")
                
        elif step == 9:
            # Step 9: Configure Grading System
            # Extract grading points
            grades = request.POST.getlist('grades[]')
            points = request.POST.getlist('points[]')
            passing_marks = request.POST.get('passing_marks', 40)
            
            if grades and points:
                new_grading = {}
                for g, p in zip(grades, points):
                    if g.strip() and p.strip():
                        new_grading[g.strip().upper()] = float(p)
                settings.grading_system = new_grading
            
            settings.passing_marks = int(passing_marks)
            settings.save()
            
            if current_step == 9:
                settings.onboarding_step = 10
                settings.save()
            return redirect('/onboarding/?step=10')
            
        elif step == 10:
            # Step 10: Complete Onboarding
            settings.is_onboarded = True
            settings.save()
            messages.success(request, "Institution onboarding completed successfully! Welcome to your Dashboard.")
            return redirect('dashboard')

    # Query helper data for rendering forms
    if step == 3:
        context['departments'] = Department.objects.filter(institution=inst)
    elif step == 4:
        context['departments'] = Department.objects.filter(institution=inst)
        context['programs'] = Program.objects.filter(institution=inst)
    elif step == 5:
        context['programs'] = Program.objects.filter(institution=inst)
    elif step == 6:
        context['programs'] = Program.objects.filter(institution=inst)
        # Fetch semesters linked to any program in this institution
        context['semesters'] = Semester.objects.filter(institution=inst)
        context['subjects'] = Subject.objects.filter(institution=inst)
    elif step == 7:
        context['departments'] = Department.objects.filter(institution=inst)
        context['faculties'] = Faculty.objects.filter(institution=inst)
    elif step == 8:
        context['departments'] = Department.objects.filter(institution=inst)
        context['programs'] = Program.objects.filter(institution=inst)
        context['semesters'] = Semester.objects.filter(institution=inst)
        context['students'] = Student.objects.filter(institution=inst)
        
    return render(request, 'institution/onboarding_wizard.html', context)


# --- GENERAL ACADEMIC CRUD VIEWS ---

@login_required
def department_list(request):
    inst = request.user.institution
    depts = Department.objects.filter(institution=inst)
    
    # Query parameters for Search/Filter
    q = request.GET.get('q', '')
    if q:
        depts = depts.filter(name__icontains=q) | depts.filter(code__icontains=q)
        
    return render(request, 'academics/department_list.html', {
        'departments': depts,
        'q': q,
        'breadcrumbs': [{'name': 'Academics', 'url': '#'}, {'name': 'Departments', 'url': '#'}]
    })

@login_required
@admin_required
def department_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        if name and code:
            Department.objects.create(
                institution=request.user.institution,
                name=name,
                code=code.upper()
            )
            messages.success(request, f"Department '{name}' added successfully.")
            return redirect('department_list')
    return render(request, 'academics/department_form.html', {
        'title': 'Add Department',
        'breadcrumbs': [{'name': 'Departments', 'url': '/academic/departments/'}, {'name': 'Add', 'url': '#'}]
    })

@login_required
@admin_required
def department_edit(request, id):
    inst = request.user.institution
    dept = get_object_or_404(Department, id=id, institution=inst)
    
    if request.method == 'POST':
        dept.name = request.POST.get('name')
        dept.code = request.POST.get('code').upper()
        dept.save()
        messages.success(request, "Department updated successfully.")
        return redirect('department_list')
        
    return render(request, 'academics/department_form.html', {
        'title': 'Edit Department',
        'department': dept,
        'breadcrumbs': [{'name': 'Departments', 'url': '/academic/departments/'}, {'name': 'Edit', 'url': '#'}]
    })


@login_required
def program_list(request):
    inst = request.user.institution
    progs = Program.objects.filter(institution=inst).select_related('department')
    
    q = request.GET.get('q', '')
    if q:
        progs = progs.filter(name__icontains=q) | progs.filter(code__icontains=q)
        
    return render(request, 'academics/program_list.html', {
        'programs': progs,
        'q': q,
        'breadcrumbs': [{'name': 'Academics', 'url': '#'}, {'name': 'Programs', 'url': '#'}]
    })

@login_required
@admin_required
def program_add(request):
    inst = request.user.institution
    depts = Department.objects.filter(institution=inst)
    
    if request.method == 'POST':
        dept_id = request.POST.get('department')
        name = request.POST.get('name')
        code = request.POST.get('code')
        duration = request.POST.get('duration_years', 4)
        if dept_id and name and code:
            dept = get_object_or_404(Department, id=dept_id, institution=inst)
            prog = Program.objects.create(
                institution=inst,
                department=dept,
                name=name,
                code=code.upper(),
                duration_years=int(duration)
            )
            # Auto create semesters
            num_semesters = int(duration) * 2
            for s_num in range(1, num_semesters + 1):
                Semester.objects.get_or_create(
                    institution=inst,
                    program=prog,
                    number=s_num
                )
            messages.success(request, f"Program '{name}' and its semesters were successfully created.")
            return redirect('program_list')
            
    return render(request, 'academics/program_form.html', {
        'title': 'Add Program',
        'departments': depts,
        'breadcrumbs': [{'name': 'Programs', 'url': '/academic/programs/'}, {'name': 'Add', 'url': '#'}]
    })


@login_required
def subject_list(request):
    inst = request.user.institution
    subs = Subject.objects.filter(institution=inst).select_related('program', 'semester')
    
    program_filter = request.GET.get('program', '')
    semester_filter = request.GET.get('semester', '')
    
    if program_filter:
        subs = subs.filter(program_id=program_filter)
    if semester_filter:
        subs = subs.filter(semester_id=semester_filter)
        
    q = request.GET.get('q', '')
    if q:
        subs = subs.filter(name__icontains=q) | subs.filter(code__icontains=q)
        
    programs = Program.objects.filter(institution=inst)
    semesters = Semester.objects.filter(institution=inst)
    
    return render(request, 'academics/subject_list.html', {
        'subjects': subs,
        'programs': programs,
        'semesters': semesters,
        'program_filter': int(program_filter) if program_filter else '',
        'semester_filter': int(semester_filter) if semester_filter else '',
        'q': q,
        'breadcrumbs': [{'name': 'Academics', 'url': '#'}, {'name': 'Subjects', 'url': '#'}]
    })

@login_required
@admin_required
def subject_add(request):
    inst = request.user.institution
    programs = Program.objects.filter(institution=inst)
    semesters = Semester.objects.filter(institution=inst)
    
    if request.method == 'POST':
        prog_id = request.POST.get('program')
        sem_id = request.POST.get('semester')
        name = request.POST.get('name')
        code = request.POST.get('code')
        credits = request.POST.get('credits', 4)
        is_elective = request.POST.get('is_elective') == 'on'
        
        if prog_id and sem_id and name and code:
            prog = get_object_or_404(Program, id=prog_id, institution=inst)
            sem = get_object_or_404(Semester, id=sem_id, program=prog)
            Subject.objects.create(
                institution=inst,
                program=prog,
                semester=sem,
                name=name,
                code=code.upper(),
                credits=int(credits),
                is_elective=is_elective
            )
            messages.success(request, f"Subject '{name}' created successfully.")
            return redirect('subject_list')
            
    return render(request, 'academics/subject_form.html', {
        'title': 'Add Subject',
        'programs': programs,
        'semesters': semesters,
        'breadcrumbs': [{'name': 'Subjects', 'url': '/academic/subjects/'}, {'name': 'Add', 'url': '#'}]
    })

@login_required
@admin_required
def institution_settings_view(request):
    inst = request.user.institution
    settings = inst.settings
    sessions = AcademicSession.objects.filter(institution=inst)
    from audit.models import AuditLog
    
    if request.method == 'POST':
        session_id = request.POST.get('current_session')
        passing_marks = request.POST.get('passing_marks', 40)
        
        # Grading system inputs
        grades = request.POST.getlist('grades[]')
        points = request.POST.getlist('points[]')
        
        if session_id:
            settings.current_session = get_object_or_404(AcademicSession, id=session_id, institution=inst)
        
        settings.passing_marks = int(passing_marks)
        
        if grades and points:
            new_grading = {}
            for g, p in zip(grades, points):
                if g.strip() and p.strip():
                    new_grading[g.strip().upper()] = float(p)
            settings.grading_system = new_grading
            
        settings.save()
        
        AuditLog.objects.create(
            institution=inst,
            user=request.user,
            user_role=request.user.get_role_display(),
            action="Updated global institution grading settings.",
            module="ACADEMICS",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, "Institution settings updated successfully.")
        return redirect('dashboard')
        
    # Format grading system dict for form listing
    grading_list = []
    if settings.grading_system:
        for g, p in settings.grading_system.items():
            grading_list.append({'grade': g, 'point': p})
    else:
        # Default fallback
        for g, p in [('A+', 10), ('A', 9), ('B+', 8), ('B', 7), ('C', 6), ('D', 5), ('F', 0)]:
            grading_list.append({'grade': g, 'point': p})
            
    return render(request, 'academics/institution_settings.html', {
        'settings': settings,
        'sessions': sessions,
        'grading_list': grading_list,
        'breadcrumbs': [{'name': 'Settings', 'url': '#'}]
    })

