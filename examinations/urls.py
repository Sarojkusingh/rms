from django.urls import path
from . import views

urlpatterns = [
    path('examinations/', views.examination_list, name='examination_list'),
    path('examinations/create/', views.examination_create, name='examination_create'),
    path('examinations/registrations/', views.exam_registration_list, name='exam_registration_list'),
    path('examinations/admit-card/<int:registration_id>/', views.student_admit_card, name='student_admit_card'),
]
