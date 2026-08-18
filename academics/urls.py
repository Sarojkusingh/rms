from django.urls import path
from . import views

urlpatterns = [
    # Wizard
    path('onboarding/', views.onboarding_wizard, name='onboarding_wizard'),
    
    # Departments
    path('academic/departments/', views.department_list, name='department_list'),
    path('academic/departments/add/', views.department_add, name='department_add'),
    path('academic/departments/<int:id>/edit/', views.department_edit, name='department_edit'),
    
    # Programs
    path('academic/programs/', views.program_list, name='program_list'),
    path('academic/programs/add/', views.program_add, name='program_add'),
    
    # Subjects
    path('academic/subjects/', views.subject_list, name='subject_list'),
    path('academic/subjects/add/', views.subject_add, name='subject_add'),
    
    # Grading Settings
    path('settings/grading/', views.institution_settings_view, name='institution_settings'),
    path('settings/', views.institution_settings_view, name='settings'),
]
