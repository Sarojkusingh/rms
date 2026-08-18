import datetime
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
from tenants.models import Institution, InstitutionSettings
from academics.models import AcademicSession, Department, Program, Semester, Subject
from students.models import Student
from examinations.models import Examination, ExamSubject, ExamRegistration
from marks.models import Marks
from results.models import Result
from results.services.result_calculator import ResultCalculator

User = get_user_model()

class ResultManagementSystemTests(TestCase):
    def setUp(self):
        # 1. Create Institution
        self.inst = Institution.objects.create(
            name="Test University",
            slug="testuni",
            is_active=True
        )
        
        # 2. Create Users
        self.admin_user = User.objects.create_user(
            username="test_admin",
            email="admin@test.edu",
            password="password123",
            role=User.Role.INSTITUTION_ADMIN,
            institution=self.inst
        )
        
        self.student_user = User.objects.create_user(
            username="test_student",
            email="student@test.edu",
            password="password123",
            role=User.Role.STUDENT,
            institution=self.inst
        )
        
        # 3. Academic Structure
        self.session = AcademicSession.objects.create(
            institution=self.inst,
            name="Spring 2026",
            is_active=True
        )
        
        self.settings = InstitutionSettings.objects.create(
            institution=self.inst,
            current_session=self.session,
            passing_marks=40,
            grading_system={'A+': 10.0, 'A': 9.0, 'F': 0.0}
        )
        
        self.dept = Department.objects.create(
            institution=self.inst,
            name="Computer Science",
            code="CSE"
        )
        
        self.program = Program.objects.create(
            institution=self.inst,
            department=self.dept,
            name="B.Tech CSE",
            code="BTECH-CSE",
            duration_years=4
        )
        
        self.semester = Semester.objects.create(
            institution=self.inst,
            program=self.program,
            number=1
        )
        
        self.subject = Subject.objects.create(
            institution=self.inst,
            program=self.program,
            semester=self.semester,
            name="Programming",
            code="CS-101",
            credits=4
        )
        
        # 4. Student profile mapping
        self.student = Student.objects.create(
            institution=self.inst,
            user=self.student_user,
            student_id="STU-001",
            department=self.dept,
            program=self.program,
            semester=self.semester,
            academic_session=self.session
        )
        
        # 5. Examination
        self.exam = Examination.objects.create(
            institution=self.inst,
            name="Mid-Term Exams 2026",
            exam_type=Examination.ExamType.END_SEM,
            academic_session=self.session,
            program=self.program,
            semester=self.semester,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=10),
            status=Examination.Status.ACTIVE
        )
        
        self.exam_sub = ExamSubject.objects.create(
            examination=self.exam,
            subject=self.subject,
            exam_date=timezone.now().date(),
            start_time=datetime.time(10, 0),
            max_marks=100,
            passing_marks=40
        )
        
        self.registration = ExamRegistration.objects.create(
            institution=self.inst,
            student=self.student,
            examination=self.exam
        )

    def test_user_role_rbac(self):
        """
        Verify role assignments on user model.
        """
        self.assertTrue(self.admin_user.is_institution_admin)
        self.assertFalse(self.student_user.is_institution_admin)
        self.assertEqual(self.student_user.role, User.Role.STUDENT)

    def test_result_calculator_engine(self):
        """
        Locks student marks and runs ResultCalculator to verify SGPA math.
        """
        # Create draft marks sheet
        marks = Marks.objects.create(
            institution=self.inst,
            exam_registration=self.registration,
            subject=self.subject,
            entered_by=self.admin_user,
            theory_marks=85.0,
            internal_marks=10.0,
            total_marks=95.0,
            status=Marks.Status.LOCKED  # Lock it so calculator reads it
        )
        
        # Execute Calculator
        result = ResultCalculator.calculate_student_result(self.student, self.exam)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.total_credits, 4)
        self.assertEqual(result.earned_credits, 4)
        self.assertEqual(result.sgpa, 10.0)  # 95% maps to grade A+ (gp=10.0)
        self.assertEqual(result.cgpa, 10.0)
