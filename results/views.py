import io
import base64
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.utils import timezone
from academics.models import Program, Semester
from examinations.models import Examination, ExamRegistration
from .models import Result, ResultSubject, ResultApproval
from .services.result_calculator import ResultCalculator
from audit.models import AuditLog
from notifications.models import Notification

@login_required
def results_process(request):
    """
    Exam Controller Result Processing and Approval timeline.
    """
    inst = request.user.institution
    if request.user.role not in ['EXAM_CONTROLLER', 'HOD', 'INSTITUTION_ADMIN', 'INSTITUTION_OWNER']:
        messages.error(request, "Access denied. Requires Exam Controller, HOD, or Admin role.")
        return redirect('dashboard')
        
    exams = Examination.objects.filter(institution=inst, status=Examination.Status.ACTIVE)
    programs = Program.objects.filter(institution=inst)
    semesters = Semester.objects.filter(institution=inst)
    
    exam_id = request.GET.get('examination', '')
    prog_id = request.GET.get('program', '')
    sem_id = request.GET.get('semester', '')
    
    results = []
    stats = {'total': 0, 'pass': 0, 'fail': 0, 'avg': 0.0}
    
    if exam_id and prog_id and sem_id:
        exam = get_object_or_404(Examination, id=exam_id, institution=inst)
        prog = get_object_or_404(Program, id=prog_id, institution=inst)
        sem = get_object_or_404(Semester, id=sem_id, program=prog)
        
        # Fetch calculated results
        results = Result.objects.filter(
            institution=inst,
            examination=exam,
            student__program=prog,
            semester=sem
        ).select_related('student__user')
        
        if results.exists():
            stats['total'] = results.count()
            # A student is pass if they didn't get any F grade in result subjects
            stats['pass'] = results.filter(subjects__is_pass=False).distinct().count()
            stats['pass'] = stats['total'] - stats['pass']
            stats['fail'] = stats['total'] - stats['pass']
            stats['avg'] = round(results.aggregate(models.Avg('sgpa'))['sgpa__avg'] or 0.0, 2)
            
    # POST to trigger bulk calculation
    if request.method == 'POST' and 'calculate' in request.POST:
        exam_id = request.POST.get('examination')
        prog_id = request.POST.get('program')
        sem_id = request.POST.get('semester')
        
        exam = get_object_or_404(Examination, id=exam_id, institution=inst)
        prog = get_object_or_404(Program, id=prog_id, institution=inst)
        sem = get_object_or_404(Semester, id=sem_id, program=prog)
        
        # Fetch registered students
        registrations = ExamRegistration.objects.filter(examination=exam, student__program=prog, student__semester=sem)
        
        count = 0
        with transaction.atomic():
            for reg in registrations:
                res = ResultCalculator.calculate_student_result(reg.student, exam)
                if res:
                    count += 1
                    
            AuditLog.objects.create(
                institution=inst,
                user=request.user,
                user_role=request.user.get_role_display(),
                action=f"Calculated academic results for {count} students in exam '{exam.name}'.",
                module="RESULTS",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
        messages.success(request, f"Successfully calculated results for {count} registered students!")
        return redirect(f'/results/process/?examination={exam_id}&program={prog_id}&semester={sem_id}')

    return render(request, 'results/results_process.html', {
        'exams': exams,
        'programs': programs,
        'semesters': semesters,
        'exam_filter': int(exam_id) if exam_id else '',
        'prog_filter': int(prog_id) if prog_id else '',
        'sem_filter': int(sem_id) if sem_id else '',
        'results': results,
        'stats': stats,
        'breadcrumbs': [{'name': 'Results Cell', 'url': '#'}]
    })

@login_required
def results_approve_publish(request):
    """
    HOD or Exam Controller timeline approvals and final publishing.
    """
    inst = request.user.institution
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')  # review, approve, publish
        exam_id = request.POST.get('examination')
        prog_id = request.POST.get('program')
        sem_id = request.POST.get('semester')
        
        exam = get_object_or_404(Examination, id=exam_id, institution=inst)
        prog = get_object_or_404(Program, id=prog_id, institution=inst)
        sem = get_object_or_404(Semester, id=sem_id, program=prog)
        
        results = Result.objects.filter(
            institution=inst,
            examination=exam,
            student__program=prog,
            semester=sem
        )
        
        count = results.count()
        if count == 0:
            messages.warning(request, "No calculated results found to update.")
            return redirect('results_process')
            
        with transaction.atomic():
            if action == 'review' and user.role == 'HOD':
                # HOD marks reviewed
                results.update(status=Result.Status.REVIEWED)
                # Create timeline approval logs
                for r in results:
                    ResultApproval.objects.create(
                        institution=inst, result=r, role_acted='HOD', user=user,
                        status_before=Result.Status.CALCULATED, status_after=Result.Status.REVIEWED
                    )
                messages.success(request, f"HOD verified {count} student results cards.")
                
            elif action == 'approve' and user.role == 'EXAM_CONTROLLER':
                results.update(status=Result.Status.APPROVED)
                for r in results:
                    ResultApproval.objects.create(
                        institution=inst, result=r, role_acted='CONTROLLER', user=user,
                        status_before=Result.Status.REVIEWED, status_after=Result.Status.APPROVED
                    )
                messages.success(request, f"Exam Controller approved {count} student results.")
                
            elif action == 'publish' and user.role == 'EXAM_CONTROLLER':
                results.update(status=Result.Status.PUBLISHED, published_at=timezone.now())
                for r in results:
                    ResultApproval.objects.create(
                        institution=inst, result=r, role_acted='CONTROLLER_PUBLISH', user=user,
                        status_before=Result.Status.APPROVED, status_after=Result.Status.PUBLISHED
                    )
                    # Notify student
                    Notification.objects.create(
                        user=r.student.user,
                        title="Academic Result Published",
                        message=f"Your results for {exam.name} have been published. View your marksheet.",
                        notification_type="RESULT_PUBLISHED"
                    )
                messages.success(request, f"Successfully published results for {count} students! Notifications sent.")
                
            AuditLog.objects.create(
                institution=inst,
                user=user,
                user_role=user.get_role_display(),
                action=f"Updated results workflow step to '{action}' for {count} records.",
                module="RESULTS",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
        return redirect(f'/results/process/?examination={exam_id}&program={prog_id}&semester={sem_id}')
        
    return redirect('results_process')


@login_required
def student_results(request):
    """
    Student Portal Results dashboard.
    """
    inst = request.user.institution
    if request.user.role != 'STUDENT':
        messages.error(request, "Student login required.")
        return redirect('dashboard')
        
    results = Result.objects.filter(
        institution=inst,
        student=request.user.student,
        status=Result.Status.PUBLISHED
    ).select_related('examination')
    
    return render(request, 'results/student_results.html', {
        'results': results,
        'breadcrumbs': [{'name': 'My Results', 'url': '#'}]
    })

@login_required
def student_marksheet(request, result_id):
    """
    Official print-friendly Marksheet Grade Card.
    """
    inst = request.user.institution
    result = get_object_or_404(Result, id=result_id, institution=inst)
    
    # Security check: Students can only access their own results
    if request.user.role == 'STUDENT' and request.user.student.id != result.student.id:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    # Check if result is published
    if result.status != Result.Status.PUBLISHED and request.user.role == 'STUDENT':
        messages.error(request, "This result card is not yet published.")
        return redirect('student_results')
        
    # Generate Verification QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(f"https://portal.rmssaas.com/verify/result/{result.verification_id}/")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Dump image to buffer as base64 string
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    result_subjects = ResultSubject.objects.filter(result=result).select_related('subject')
    
    return render(request, 'results/marksheet.html', {
        'result': result,
        'result_subjects': result_subjects,
        'qr_code': qr_base64,
        'breadcrumbs': [{'name': 'My Results', 'url': '/results/my-results/'}, {'name': 'Grade Card', 'url': '#'}]
    })

@login_required
def student_transcript(request, student_id):
    """
    Academic transcript summarizing all completed semesters.
    """
    inst = request.user.institution
    student = get_object_or_404(Student, id=student_id, institution=inst)
    
    if request.user.role == 'STUDENT' and request.user.student.id != student.id:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    published_results = Result.objects.filter(
        institution=inst,
        student=student,
        status=Result.Status.PUBLISHED
    ).order_by('semester__number')
    
    semesters_data = []
    for r in published_results:
        subjects = ResultSubject.objects.filter(result=r).select_related('subject')
        semesters_data.append({
            'result': r,
            'subjects': subjects
        })
        
    return render(request, 'results/transcript.html', {
        'student': student,
        'semesters_data': semesters_data,
        'breadcrumbs': [{'name': 'My Results', 'url': '/results/my-results/'}, {'name': 'Transcript', 'url': '#'}]
    })
