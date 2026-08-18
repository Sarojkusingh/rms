import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from academics.models import Department, Program, Semester, Subject
from examinations.models import Examination
from students.models import Student
from marks.models import Marks
from academics.views import admin_required

@login_required
def reports_home(request):
    """
    Renders the general reports homepage with filters to export lists.
    """
    inst = request.user.institution
    exams = Examination.objects.filter(institution=inst)
    programs = Program.objects.filter(institution=inst)
    semesters = Semester.objects.filter(institution=inst)
    subjects = Subject.objects.filter(institution=inst)
    
    return render(request, 'reports/reports_home.html', {
        'exams': exams,
        'programs': programs,
        'semesters': semesters,
        'subjects': subjects,
        'breadcrumbs': [{'name': 'Reports', 'url': '#'}]
    })

@login_required
@admin_required
def export_students_csv(request):
    """
    Streams a CSV file containing filtered student records.
    """
    inst = request.user.institution
    prog_id = request.GET.get('program')
    sem_id = request.GET.get('semester')
    
    students = Student.objects.filter(institution=inst).select_related('user', 'department', 'program', 'semester')
    if prog_id:
        students = students.filter(program_id=prog_id)
    if sem_id:
        students = students.filter(semester_id=sem_id)
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_report.csv"'
    
    writer = csv.writer(response)
    # Write Header
    writer.writerow(['Roll/Student ID', 'First Name', 'Last Name', 'Email', 'Department', 'Program', 'Semester', 'Status'])
    
    for s in students:
        writer.writerow([
            s.student_id,
            s.user.first_name,
            s.user.last_name,
            s.user.email,
            s.department.code,
            s.program.code,
            f"Semester {s.semester.number}",
            s.status
        ])
        
    return response

@login_required
@admin_required
def export_marks_csv(request):
    """
    Streams a CSV file containing locked student marks.
    """
    inst = request.user.institution
    exam_id = request.GET.get('examination')
    sub_id = request.GET.get('subject')
    
    if not exam_id or not sub_id:
        messages.error(request, "Exporting marks requires selecting both Examination and Subject filters.")
        return redirect('reports_home')
        
    exam = get_object_or_404(Examination, id=exam_id, institution=inst)
    subject = get_object_or_404(Subject, id=sub_id, institution=inst)
    
    marks_records = Marks.objects.filter(
        institution=inst,
        exam_registration__examination=exam,
        subject=subject
    ).select_related('exam_registration__student__user')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="marks_{subject.code}_{exam.id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Roll Number', 'Student Name', 'Internal', 'Theory', 'Practical', 'Assignment', 'Attendance', 'Total', 'Grade', 'Status'])
    
    for m in marks_records:
        writer.writerow([
            m.exam_registration.student.student_id,
            m.exam_registration.student.user.get_full_name(),
            m.internal_marks,
            m.theory_marks,
            m.practical_marks,
            m.assignment_marks,
            m.attendance_marks,
            m.total_marks,
            m.grade or 'N/A',
            m.get_status_display()
        ])
        
    return response

def analytics_dashboard(request):
    inst = request.user.institution
    from results.models import Result, ResultSubject
    
    # Query published results
    results = Result.objects.filter(institution=inst, status=Result.Status.PUBLISHED)
    total_results = results.count()
    
    fail_results_count = results.filter(subjects__is_pass=False).distinct().count()
    pass_results_count = total_results - fail_results_count
    
    # Grade distribution mapping
    grades = ['A+', 'A', 'B+', 'B', 'C', 'D', 'F']
    grade_counts = []
    for g in grades:
        count = ResultSubject.objects.filter(
            result__institution=inst, 
            result__status=Result.Status.PUBLISHED, 
            grade=g
        ).count()
        grade_counts.append(count)
        
    # Department Rank Comparisons
    departments = Department.objects.filter(institution=inst)
    dept_names = []
    dept_sgpas = []
    for dept in departments:
        dept_avg = Result.objects.filter(
            institution=inst, 
            status=Result.Status.PUBLISHED, 
            student__department=dept
        ).aggregate(models.Avg('sgpa'))['sgpa__avg'] or 0.0
        dept_names.append(dept.code)
        dept_sgpas.append(round(dept_avg, 2))
        
    return render(request, 'reports/analytics.html', {
        'total': total_results,
        'pass': pass_results_count,
        'fail': fail_results_count,
        'grades': grades,
        'grade_counts': grade_counts,
        'dept_names': dept_names,
        'dept_sgpas': dept_sgpas,
        'breadcrumbs': [{'name': 'Analytics', 'url': '#'}]
    })

