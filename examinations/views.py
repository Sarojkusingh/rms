from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.db.models import Q
from academics.models import Program, Semester, Subject, AcademicSession
from .models import Examination, ExamSubject, ExamRegistration
from students.models import Student
from academics.views import admin_required
from audit.models import AuditLog

@login_required
def examination_list(request):
    inst = request.user.institution
    exams = Examination.objects.filter(institution=inst).select_related('academic_session', 'program', 'semester')
    
    q = request.GET.get('q', '')
    if q:
        exams = exams.filter(name__icontains=q)
        
    return render(request, 'examinations/examination_list.html', {
        'examinations': exams,
        'q': q,
        'breadcrumbs': [{'name': 'Examinations', 'url': '#'}]
    })

@login_required
@admin_required
def examination_create(request):
    inst = request.user.institution
    programs = Program.objects.filter(institution=inst)
    semesters = Semester.objects.filter(institution=inst)
    active_session = inst.settings.current_session
    
    if not active_session:
        messages.error(request, "Configure an active academic session first.")
        return redirect('examination_list')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        exam_type = request.POST.get('exam_type')
        prog_id = request.POST.get('program')
        sem_id = request.POST.get('semester')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Subject schedules lists
        subject_ids = request.POST.getlist('subjects[]')
        dates = request.POST.getlist('dates[]')
        times = request.POST.getlist('times[]')
        durations = request.POST.getlist('durations[]')
        max_marks = request.POST.getlist('max_marks[]')
        passing_marks = request.POST.getlist('passing_marks[]')
        
        if name and exam_type and prog_id and sem_id and start_date and end_date:
            prog = get_object_or_404(Program, id=prog_id, institution=inst)
            sem = get_object_or_404(Semester, id=sem_id, program=prog)
            
            try:
                with transaction.atomic():
                    # 1. Create Exam
                    exam = Examination.objects.create(
                        institution=inst,
                        name=name,
                        exam_type=exam_type,
                        academic_session=active_session,
                        program=prog,
                        semester=sem,
                        start_date=start_date,
                        end_date=end_date,
                        status=Examination.Status.ACTIVE
                    )
                    
                    # 2. Add Exam Subjects
                    for sub_id, dt, tm, dur, mm, pm in zip(subject_ids, dates, times, durations, max_marks, passing_marks):
                        if sub_id and dt and tm:
                            sub = get_object_or_404(Subject, id=sub_id, program=prog)
                            ExamSubject.objects.create(
                                examination=exam,
                                subject=sub,
                                exam_date=dt,
                                start_time=tm,
                                duration_minutes=int(dur),
                                max_marks=int(mm),
                                passing_marks=int(pm)
                            )
                            
                    # 3. Auto-Register all active students in this Program & Semester for this Exam
                    enrolled_students = Student.objects.filter(
                        institution=inst,
                        program=prog,
                        semester=sem,
                        status=Student.Status.ACTIVE
                    )
                    for st in enrolled_students:
                        ExamRegistration.objects.create(
                            institution=inst,
                            student=st,
                            examination=exam
                        )
                        
                    AuditLog.objects.create(
                        institution=inst,
                        user=request.user,
                        user_role=request.user.get_role_display(),
                        action=f"Created exam '{name}' and auto-registered {enrolled_students.count()} students.",
                        module="EXAMINATIONS",
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                messages.success(request, f"Examination '{name}' scheduled and student registrations generated successfully.")
                return redirect('examination_list')
            except Exception as e:
                messages.error(request, f"Scheduling failed: {e}")
        else:
            messages.error(request, "Please enter all required examination fields.")
            
    # Subjects catalog lookup for dynamic JS rendering
    context = {
        'programs': programs,
        'semesters': semesters,
        'exam_types': Examination.ExamType.choices,
        'subjects_json': list(Subject.objects.filter(institution=inst).values('id', 'name', 'code', 'program_id', 'semester_id')),
        'breadcrumbs': [{'name': 'Examinations', 'url': '/examinations/'}, {'name': 'Create Schedule', 'url': '#'}]
    }
    return render(request, 'examinations/examination_form.html', context)

@login_required
def student_admit_card(request, registration_id):
    inst = request.user.institution
    reg = get_object_or_404(ExamRegistration, id=registration_id, institution=inst)
    
    # Security check: Students can only view their own admit card
    if request.user.role == 'STUDENT' and request.user.student.id != reg.student.id:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
        
    schedules = ExamSubject.objects.filter(examination=reg.examination).select_related('subject')
    return render(request, 'examinations/admit_card.html', {
        'registration': reg,
        'schedules': schedules,
        'breadcrumbs': [{'name': 'My Exams', 'url': '#'}, {'name': 'Admit Card', 'url': '#'}]
    })

@login_required
def exam_registration_list(request):
    inst = request.user.institution
    if request.user.role == 'STUDENT':
        registrations = ExamRegistration.objects.filter(
            institution=inst, 
            student=request.user.student
        ).select_related('examination__academic_session')
        return render(request, 'examinations/student_exam_list.html', {
            'registrations': registrations,
            'breadcrumbs': [{'name': 'My Exams', 'url': '#'}]
        })
    else:
        # Administrators view
        registrations = ExamRegistration.objects.filter(institution=inst).select_related('student__user', 'examination')
        return render(request, 'examinations/registration_list.html', {
            'registrations': registrations,
            'breadcrumbs': [{'name': 'Examinations', 'url': '/examinations/'}, {'name': 'Registrations', 'url': '#'}]
        })
