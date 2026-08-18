import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.http import JsonResponse
from academics.models import Program, Semester, Subject, Section
from examinations.models import Examination, ExamSubject, ExamRegistration
from faculty.models import FacultySubject
from .models import Marks
from audit.models import AuditLog

@login_required
def marks_entry(request):
    inst = request.user.institution
    user = request.user
    
    # Context variables
    exams = Examination.objects.filter(institution=inst, status=Examination.Status.ACTIVE)
    programs = Program.objects.filter(institution=inst)
    semesters = Semester.objects.filter(institution=inst)
    subjects = Subject.objects.filter(institution=inst)
    sections = Section.objects.filter(institution=inst)
    
    # Filter selection
    exam_id = request.GET.get('examination', '')
    prog_id = request.GET.get('program', '')
    sem_id = request.GET.get('semester', '')
    sub_id = request.GET.get('subject', '')
    sec_id = request.GET.get('section', '')
    
    students_data = []
    exam_sub = None
    marks_status = 'N/A'
    
    if exam_id and prog_id and sem_id and sub_id:
        exam = get_object_or_404(Examination, id=exam_id, institution=inst)
        prog = get_object_or_404(Program, id=prog_id, institution=inst)
        sem = get_object_or_404(Semester, id=sem_id, program=prog)
        subject = get_object_or_404(Subject, id=sub_id, program=prog)
        section = get_object_or_404(Section, id=sec_id, program=prog) if sec_id else None
        
        # 1. Check if subject is scheduled for this exam
        exam_sub = ExamSubject.objects.filter(examination=exam, subject=subject).first()
        
        if not exam_sub:
            messages.error(request, "This subject is not scheduled in the selected examination.")
        else:
            # 2. Check permissions: Faculty can only enter marks for assigned subject allocations
            if user.role == 'FACULTY':
                # Check allocation
                allocated = FacultySubject.objects.filter(
                    faculty=user.faculty_profile,
                    subject=subject,
                    section=section,
                    academic_session=exam.academic_session
                ).exists()
                if not allocated:
                    messages.error(request, "Permission Denied: You are not allocated to teach this subject class.")
                    return redirect('marks_entry')
            
            # Fetch registered students
            registrations = ExamRegistration.objects.filter(examination=exam, student__program=prog, student__semester=sem)
            if section:
                registrations = registrations.filter(student__section=section)
                
            for reg in registrations:
                # Find or create draft marks record
                marks_rec, _ = Marks.objects.get_or_create(
                    institution=inst,
                    exam_registration=reg,
                    subject=subject,
                    defaults={'status': Marks.Status.DRAFT, 'entered_by': user}
                )
                students_data.append({
                    'registration_id': reg.id,
                    'student_id': reg.student.student_id,
                    'name': reg.student.user.get_full_name() or reg.student.user.username,
                    'marks': marks_rec
                })
                
            if students_data:
                # Common status display
                marks_status = students_data[0]['marks'].get_status_display()
                
    context = {
        'exams': exams,
        'programs': programs,
        'semesters': semesters,
        'subjects': subjects,
        'sections': sections,
        'exam_filter': int(exam_id) if exam_id else '',
        'prog_filter': int(prog_id) if prog_id else '',
        'sem_filter': int(sem_id) if sem_id else '',
        'sub_filter': int(sub_id) if sub_id else '',
        'sec_filter': int(sec_id) if sec_id else '',
        
        'students_data': students_data,
        'exam_sub': exam_sub,
        'marks_status': marks_status,
        'breadcrumbs': [{'name': 'Academics', 'url': '#'}, {'name': 'Marks Entry', 'url': '#'}]
    }
    return render(request, 'marks/marks_entry.html', context)

@login_required
def save_marks_ajax(request):
    """
    AJAX endpoint to save student marks dynamically.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
        
    try:
        data = json.loads(request.body)
        marks_id = data.get('marks_id')
        
        internal = float(data.get('internal', 0))
        theory = float(data.get('theory', 0))
        practical = float(data.get('practical', 0))
        assignment = float(data.get('assignment', 0))
        attendance = float(data.get('attendance', 0))
        
        marks_rec = get_object_or_404(Marks, id=marks_id, institution=request.user.institution)
        
        # 1. Permissions Check
        if request.user.role == 'FACULTY':
            if marks_rec.status in [Marks.Status.SUBMITTED, Marks.Status.APPROVED, Marks.Status.LOCKED]:
                return JsonResponse({'success': False, 'error': 'Marks locked/submitted. Modifications blocked.'})
                
        # 2. Maximum Marks Check
        exam_sub = ExamSubject.objects.filter(
            examination=marks_rec.exam_registration.examination, 
            subject=marks_rec.subject
        ).first()
        
        if not exam_sub:
            return JsonResponse({'success': False, 'error': 'Subject schedules not found for this exam.'})
            
        total = internal + theory + practical + assignment + attendance
        
        if internal < 0 or theory < 0 or practical < 0 or assignment < 0 or attendance < 0:
            return JsonResponse({'success': False, 'error': 'Marks values cannot be negative.'})
            
        if total > exam_sub.max_marks:
            return JsonResponse({'success': False, 'error': f"Total marks ({total}) exceeds maximum limit ({exam_sub.max_marks})."})
            
        # 3. Save Values
        marks_rec.internal_marks = internal
        marks_rec.theory_marks = theory
        marks_rec.practical_marks = practical
        marks_rec.assignment_marks = assignment
        marks_rec.attendance_marks = attendance
        marks_rec.total_marks = total
        
        # Determine pass/fail grade based on settings
        settings = request.user.institution.settings
        is_pass = total >= exam_sub.passing_marks
        
        if is_pass:
            marks_rec.grade = 'A'  # Simple grade calculation fallback
            marks_rec.grade_point = 9.0
        else:
            marks_rec.grade = 'F'
            marks_rec.grade_point = 0.0
            
        marks_rec.entered_by = request.user
        marks_rec.save()
        
        return JsonResponse({
            'success': True,
            'total': total,
            'grade': marks_rec.grade,
            'grade_point': marks_rec.grade_point
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def marks_submit(request):
    """
    Submits draft marks to HOD for verification.
    """
    if request.method == 'POST':
        exam_id = request.POST.get('examination')
        sub_id = request.POST.get('subject')
        sec_id = request.POST.get('section')
        
        inst = request.user.institution
        
        marks_to_submit = Marks.objects.filter(
            institution=inst,
            exam_registration__examination_id=exam_id,
            subject_id=sub_id,
            status=Marks.Status.DRAFT
        )
        if sec_id:
            marks_to_submit = marks_to_submit.filter(exam_registration__student__section_id=sec_id)
            
        count = marks_to_submit.count()
        if count == 0:
            messages.warning(request, "No draft marks records found to submit.")
            return redirect('marks_entry')
            
        with transaction.atomic():
            marks_to_submit.update(status=Marks.Status.SUBMITTED)
            
            AuditLog.objects.create(
                institution=inst,
                user=request.user,
                user_role=request.user.get_role_display(),
                action=f"Submitted {count} marks sheets to HOD for approval.",
                module="MARKS",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
        messages.success(request, f"Successfully submitted {count} student marks sheets to HOD!")
        
    return redirect('marks_entry')

@login_required
def marks_verification_list(request):
    """
    HOD Portal Marks Verification list.
    """
    inst = request.user.institution
    if request.user.role != 'HOD':
        messages.error(request, "HOD Access required.")
        return redirect('dashboard')
        
    # Group submitted marks
    submitted_groups = Marks.objects.filter(
        institution=inst,
        status=Marks.Status.SUBMITTED,
        subject__program__department=request.user.faculty_profile.department
    ).select_related('exam_registration__examination', 'subject', 'exam_registration__student__section').values(
        'exam_registration__examination__id', 'exam_registration__examination__name',
        'subject__id', 'subject__name', 'subject__code',
        'exam_registration__student__section__id', 'exam_registration__student__section__name'
    ).annotate(count=models.Count('id'))
    
    return render(request, 'marks/verification_list.html', {
        'groups': submitted_groups,
        'breadcrumbs': [{'name': 'Marks Approvals', 'url': '#'}]
    })

@login_required
def marks_approve_reject(request, exam_id, subject_id, section_id=None):
    inst = request.user.institution
    if request.user.role != 'HOD':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    marks_records = Marks.objects.filter(
        institution=inst,
        exam_registration__examination_id=exam_id,
        subject_id=subject_id,
        status=Marks.Status.SUBMITTED
    )
    if section_id:
        marks_records = marks_records.filter(exam_registration__student__section_id=section_id)
        
    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('remarks')
        
        with transaction.atomic():
            if action == 'approve':
                marks_records.update(status=Marks.Status.APPROVED, remarks=comments)
                messages.success(request, "Successfully approved all marks sheets.")
            elif action == 'reject':
                marks_records.update(status=Marks.Status.REJECTED, remarks=comments)
                messages.warning(request, "Marks sheets rejected and sent back to faculty for correction.")
                
            AuditLog.objects.create(
                institution=inst,
                user=request.user,
                user_role=request.user.get_role_display(),
                action=f"HOD {action}d marks sheets for subject ID {subject_id}.",
                module="MARKS",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
        return redirect('marks_verification_list')
        
    return render(request, 'marks/approval_form.html', {
        'records': marks_records,
        'exam_id': exam_id,
        'subject_id': subject_id,
        'section_id': section_id,
        'breadcrumbs': [{'name': 'Marks Approvals', 'url': '/marks/verifications/'}, {'name': 'Review Sheets', 'url': '#'}]
    })

@login_required
def controller_marks_verification(request):
    """
    Exam Controller Portal Marks Verification list to LOCK marks.
    """
    inst = request.user.institution
    if request.user.role != 'EXAM_CONTROLLER':
        messages.error(request, "Exam Controller access required.")
        return redirect('dashboard')
        
    approved_groups = Marks.objects.filter(
        institution=inst,
        status=Marks.Status.APPROVED
    ).select_related('exam_registration__examination', 'subject', 'exam_registration__student__section').values(
        'exam_registration__examination__id', 'exam_registration__examination__name',
        'subject__id', 'subject__name', 'subject__code',
        'exam_registration__student__section__id', 'exam_registration__student__section__name'
    ).annotate(count=models.Count('id'))
    
    if request.method == 'POST':
        exam_id = request.POST.get('examination')
        subject_id = request.POST.get('subject')
        section_id = request.POST.get('section')
        
        target_records = Marks.objects.filter(
            institution=inst,
            exam_registration__examination_id=exam_id,
            subject_id=subject_id,
            status=Marks.Status.APPROVED
        )
        if section_id:
            target_records = target_records.filter(exam_registration__student__section_id=section_id)
            
        count = target_records.count()
        with transaction.atomic():
            target_records.update(status=Marks.Status.LOCKED)
            
            AuditLog.objects.create(
                institution=inst,
                user=request.user,
                user_role=request.user.get_role_display(),
                action=f"Exam Controller locked {count} marks sheets.",
                module="MARKS",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
        messages.success(request, f"Successfully locked and archived {count} student marks sheets!")
        return redirect('controller_marks_verification')
        
    return render(request, 'marks/controller_verification.html', {
        'groups': approved_groups,
        'breadcrumbs': [{'name': 'Marks Lock Control', 'url': '#'}]
    })
