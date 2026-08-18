from django.urls import path
from . import views

urlpatterns = [
    path('marks/entry/', views.marks_entry, name='marks_entry'),
    path('marks/save-ajax/', views.save_marks_ajax, name='save_marks_ajax'),
    path('marks/submit/', views.marks_submit, name='marks_submit'),
    path('marks/verifications/', views.marks_verification_list, name='marks_verification_list'),
    path('marks/verifications/review/<int:exam_id>/<int:subject_id>/', views.marks_approve_reject, name='marks_approve_reject_no_sec'),
    path('marks/verifications/review/<int:exam_id>/<int:subject_id>/<int:section_id>/', views.marks_approve_reject, name='marks_approve_reject'),
    path('marks/lock-control/', views.controller_marks_verification, name='controller_marks_verification'),
]
