from django.db import transaction
from tenants.models import InstitutionSettings
from academics.models import Subject
from examinations.models import Examination, ExamSubject
from marks.models import Marks
from backlogs.models import Backlog
from students.models import StudentAcademicHistory
from ..models import Result, ResultSubject, ResultApproval

class ResultCalculator:
    @staticmethod
    def calculate_student_result(student, examination):
        """
        Processes and calculates marks, grades, SGPA, CGPA, and backlogs for a student in an examination.
        """
        inst = student.institution
        settings = inst.settings
        
        # 1. Fetch locked marks records for this student and exam
        marks_records = Marks.objects.filter(
            institution=inst,
            exam_registration__student=student,
            exam_registration__examination=examination,
            status=Marks.Status.LOCKED
        ).select_related('subject')
        
        if not marks_records.exists():
            return None
            
        total_obtained = 0.0
        total_max = 0
        total_credits = 0
        earned_credits = 0
        sum_grade_points_credits = 0.0
        
        subjects_data = []
        has_failed = False
        failed_subjects = []
        
        # Fetch grading scale mapping
        grading_scale = settings.grading_system
        if not grading_scale:
            grading_scale = {'A+': 10, 'A': 9, 'B+': 8, 'B': 7, 'C': 6, 'D': 5, 'F': 0}
            
        with transaction.atomic():
            # 2. Iterate and evaluate each subject score
            for marks in marks_records:
                sub = marks.subject
                exam_sub = ExamSubject.objects.filter(examination=examination, subject=sub).first()
                if not exam_sub:
                    continue
                    
                total_max += exam_sub.max_marks
                total_obtained += marks.total_marks
                total_credits += sub.credits
                
                # Check pass status
                is_pass = marks.total_marks >= exam_sub.passing_marks
                
                # Map score to grade
                grade = 'F'
                gp = 0.0
                
                if is_pass:
                    earned_credits += sub.credits
                    # Simple scale mapping (Percentage logic fallback)
                    pct = (marks.total_marks / exam_sub.max_marks) * 100
                    if pct >= 90:
                        grade = 'A+'
                    elif pct >= 80:
                        grade = 'A'
                    elif pct >= 70:
                        grade = 'B+'
                    elif pct >= 60:
                        grade = 'B'
                    elif pct >= 50:
                        grade = 'C'
                    elif pct >= settings.passing_marks:
                        grade = 'D'
                    gp = float(grading_scale.get(grade, 0.0))
                else:
                    has_failed = True
                    failed_subjects.append(sub)
                    gp = 0.0
                    grade = 'F'
                    
                sum_grade_points_credits += (gp * sub.credits)
                
                subjects_data.append({
                    'subject': sub,
                    'credits': sub.credits,
                    'internal_marks': marks.internal_marks,
                    'theory_marks': marks.theory_marks,
                    'practical_marks': marks.practical_marks,
                    'assignment_marks': marks.assignment_marks,
                    'attendance_marks': marks.attendance_marks,
                    'total_marks': marks.total_marks,
                    'grade': grade,
                    'grade_point': gp,
                    'is_pass': is_pass
                })
            
            # 3. Calculate SGPA: SUM(Credits * GP) / SUM(Credits)
            sgpa = 0.0
            if total_credits > 0:
                sgpa = round(sum_grade_points_credits / total_credits, 2)
                
            percentage = 0.0
            if total_max > 0:
                percentage = round((total_obtained / total_max) * 100, 2)
                
            # 4. Calculate CGPA: weighted cumulative average of all previous semesters
            # Fetch past published results
            past_results = Result.objects.filter(
                student=student,
                status=Result.Status.PUBLISHED
            ).exclude(examination=examination)
            
            total_past_credits = sum(r.total_credits for r in past_results)
            total_past_points = sum(r.sgpa * r.total_credits for r in past_results)
            
            cumulative_credits = total_past_credits + total_credits
            cumulative_points = total_past_points + (sgpa * total_credits)
            
            cgpa = 0.0
            if cumulative_credits > 0:
                cgpa = round(cumulative_points / cumulative_credits, 2)
                
            # 5. Save/Update Result Table
            result, created = Result.objects.get_or_create(
                institution=inst,
                student=student,
                examination=examination,
                defaults={
                    'semester': student.semester,
                    'academic_session': examination.academic_session,
                }
            )
            result.total_credits = total_credits
            result.earned_credits = earned_credits
            result.sgpa = sgpa
            result.cgpa = cgpa
            result.percentage = percentage
            result.status = Result.Status.CALCULATED
            result.save()
            
            # 6. Delete old result subjects and write new ones
            ResultSubject.objects.filter(result=result).delete()
            for sub_res in subjects_data:
                ResultSubject.objects.create(
                    result=result,
                    subject=sub_res['subject'],
                    credits=sub_res['credits'],
                    internal_marks=sub_res['internal_marks'],
                    theory_marks=sub_res['theory_marks'],
                    practical_marks=sub_res['practical_marks'],
                    assignment_marks=sub_res['assignment_marks'],
                    attendance_marks=sub_res['attendance_marks'],
                    total_marks=sub_res['total_marks'],
                    grade=sub_res['grade'],
                    grade_point=sub_res['grade_point'],
                    is_pass=sub_res['is_pass']
                )
                
            # 7. Generate Backlogs dynamically for failed subjects
            for sub in failed_subjects:
                # Find active backlog attempts
                past_backlogs = Backlog.objects.filter(student=student, subject=sub, status=Backlog.Status.ACTIVE)
                if not past_backlogs.exists():
                    # Create new backlog
                    Backlog.objects.create(
                        institution=inst,
                        student=student,
                        subject=sub,
                        semester=student.semester,
                        attempt_number=1,
                        status=Backlog.Status.ACTIVE
                    )
                    
            # 8. Update Student Dashboard Overview History
            history, _ = StudentAcademicHistory.objects.get_or_create(student=student)
            history.cgpa = cgpa
            history.total_credits_completed += earned_credits
            
            active_backlogs_count = Backlog.objects.filter(student=student, status=Backlog.Status.ACTIVE).count()
            history.active_backlogs = active_backlogs_count
            history.save()
            
            return result
