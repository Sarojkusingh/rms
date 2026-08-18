from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from tenants.models import Institution, InstitutionSettings
from academics.models import AcademicSession, Department, Program, Semester, Subject
from students.models import Student, StudentAcademicHistory
from faculty.models import Faculty, FacultySubject
from subscriptions.models import Plan, Subscription

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds the database with commercial-ready multi-tenant demo data."

    def handle(self, *args, **options):
        self.stdout.write("Initializing database seeder...")
        
        try:
            with transaction.atomic():
                # 1. Create Pricing Plans
                plan_basic, _ = Plan.objects.get_or_create(
                    name="Basic Plan",
                    defaults={
                        'price_monthly': 49.00,
                        'student_limit': 500,
                        'faculty_limit': 30,
                        'storage_limit_gb': 10,
                        'is_active': True
                    }
                )
                plan_prem, _ = Plan.objects.get_or_create(
                    name="Premium Plan",
                    defaults={
                        'price_monthly': 99.00,
                        'student_limit': 2000,
                        'faculty_limit': 100,
                        'storage_limit_gb': 50,
                        'is_active': True
                    }
                )
                plan_ent, _ = Plan.objects.get_or_create(
                    name="Enterprise Plan",
                    defaults={
                        'price_monthly': 299.00,
                        'student_limit': 10000,
                        'faculty_limit': 500,
                        'storage_limit_gb': 200,
                        'is_active': True
                    }
                )
                
                # 2. Create Global Platform SuperAdmin
                if not User.objects.filter(username="admin").exists():
                    User.objects.create_superuser(
                        username="admin",
                        email="platformadmin@rmssaas.com",
                        password="admin123",
                        role=User.Role.SUPER_ADMIN
                    )
                    self.stdout.write("Created SuperAdmin: admin / admin123")
                    
                # 3. Create Demo Institution
                inst, inst_created = Institution.objects.get_or_create(
                    slug="vit",
                    defaults={
                        'name': "Vikas Institute of Technology",
                        'contact_email': "contact@vit.edu",
                        'is_active': True
                    }
                )
                
                # 4. Map Subscription Plan to Institution
                if inst_created or not hasattr(inst, 'subscription'):
                    Subscription.objects.get_or_create(
                        institution=inst,
                        defaults={
                            'plan': plan_prem,
                            'start_date': timezone.now(),
                            'end_date': timezone.now() + timedelta(days=365),
                            'next_billing_date': timezone.now() + timedelta(days=30),
                            'status': Subscription.Status.ACTIVE
                        }
                    )
                
                # 5. Create Academic Session
                session, _ = AcademicSession.objects.get_or_create(
                    institution=inst,
                    name="Autumn Session 2025",
                    defaults={
                        'is_active': True
                    }
                )
                
                # Create Institution Settings
                settings, _ = InstitutionSettings.objects.get_or_create(
                    institution=inst,
                    defaults={
                        'current_session': session,
                        'passing_marks': 40,
                        'grading_system': {'A+': 10.0, 'A': 9.0, 'B+': 8.0, 'B': 7.0, 'C': 6.0, 'D': 5.0, 'F': 0.0},
                        'onboarding_step': 10,
                        'is_onboarded': True
                    }
                )
                
                # 6. Create Departments
                dept_cse, _ = Department.objects.get_or_create(
                    institution=inst,
                    code="CSE",
                    defaults={'name': "Computer Science & Engineering"}
                )
                dept_ee, _ = Department.objects.get_or_create(
                    institution=inst,
                    code="EE",
                    defaults={'name': "Electrical Engineering"}
                )
                
                # 7. Create Programs
                prog_cse, _ = Program.objects.get_or_create(
                    institution=inst,
                    department=dept_cse,
                    code="BTECH-CSE",
                    defaults={'name': "Bachelor of Technology in CSE", 'duration_years': 4}
                )
                prog_ee, _ = Program.objects.get_or_create(
                    institution=inst,
                    department=dept_ee,
                    code="BTECH-EE",
                    defaults={'name': "Bachelor of Technology in EE", 'duration_years': 4}
                )
                
                # 8. Create Semesters & Subjects for BTECH-CSE
                for s_num in range(1, 9):
                    Semester.objects.get_or_create(institution=inst, program=prog_cse, number=s_num)
                    Semester.objects.get_or_create(institution=inst, program=prog_ee, number=s_num)
                    
                sem1_cse = Semester.objects.get(institution=inst, program=prog_cse, number=1)
                
                sub_cp, _ = Subject.objects.get_or_create(
                    institution=inst, program=prog_cse, semester=sem1_cse, code="CS-101",
                    defaults={'name': "Computer Programming", 'credits': 4, 'is_elective': False}
                )
                sub_math, _ = Subject.objects.get_or_create(
                    institution=inst, program=prog_cse, semester=sem1_cse, code="MA-101",
                    defaults={'name': "Engineering Mathematics I", 'credits': 4, 'is_elective': False}
                )
                sub_physics, _ = Subject.objects.get_or_create(
                    institution=inst, program=prog_cse, semester=sem1_cse, code="PH-101",
                    defaults={'name': "Engineering Physics", 'credits': 3, 'is_elective': False}
                )
                
                # 9. Create Users for Role Based Access Controls
                roles_to_create = [
                    ('owner', User.Role.INSTITUTION_OWNER, "owner@vit.edu"),
                    ('inst_admin', User.Role.INSTITUTION_ADMIN, "admin@vit.edu"),
                    ('controller', User.Role.EXAM_CONTROLLER, "controller@vit.edu"),
                    ('hod_cse', User.Role.HOD, "hod.cse@vit.edu"),
                    ('faculty_cs', User.Role.FACULTY, "faculty.cs@vit.edu"),
                    ('student1', User.Role.STUDENT, "student1@vit.edu"),
                ]
                
                created_users = {}
                for username, role, email in roles_to_create:
                    if not User.objects.filter(username=username).exists():
                        u = User.objects.create_user(
                            username=username,
                            email=email,
                            password="admin123",
                            role=role,
                            institution=inst,
                            first_name=username.capitalize(),
                            last_name="Demo"
                        )
                        created_users[role] = u
                        self.stdout.write(f"Created {role}: {username} / admin123")
                    else:
                        created_users[role] = User.objects.get(username=username)
                        
                # 10. Map HOD Profile
                hod_user = created_users[User.Role.HOD]
                Faculty.objects.get_or_create(
                    institution=inst,
                    user=hod_user,
                    employee_id="EMP-HOD-CSE",
                    defaults={
                        'department': dept_cse,
                        'designation': "Professor & HOD",
                        'qualification': "Ph.D. in Computer Science"
                    }
                )
                
                # Map Faculty Profile
                faculty_user = created_users[User.Role.FACULTY]
                faculty_profile, _ = Faculty.objects.get_or_create(
                    institution=inst,
                    user=faculty_user,
                    employee_id="EMP-FAC-01",
                    defaults={
                        'department': dept_cse,
                        'designation': "Assistant Professor",
                        'qualification': "M.Tech in Software Systems"
                    }
                )
                
                # 11. Allocate Subject to Faculty
                FacultySubject.objects.get_or_create(
                    institution=inst,
                    faculty=faculty_profile,
                    subject=sub_cp,
                    academic_session=session
                )
                
                # 12. Map Student Profile
                student_user = created_users[User.Role.STUDENT]
                student, _ = Student.objects.get_or_create(
                    institution=inst,
                    user=student_user,
                    student_id="STU-2025-001",
                    defaults={
                        'registration_number': "REG-2025-09920",
                        'department': dept_cse,
                        'program': prog_cse,
                        'semester': sem1_cse,
                        'academic_session': session
                    }
                )
                StudentAcademicHistory.objects.get_or_create(student=student)
                
            self.stdout.write(self.style.SUCCESS("Database seeded with multi-tenant Vit Institution demo data successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Seeding failed: {e}"))
