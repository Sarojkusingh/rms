from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/import/', views.student_import, name='student_import'),
    path('students/promotion/', views.student_promotion, name='student_promotion'),
    path('students/<int:id>/', views.student_profile, name='student_profile'),
    path('students/<int:id>/edit/', views.student_edit, name='student_edit'),
]
