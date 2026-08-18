from django.urls import path
from . import views

urlpatterns = [
    path('reports/', views.reports_home, name='reports'),
    path('reports/students-csv/', views.export_students_csv, name='export_students_csv'),
    path('reports/marks-csv/', views.export_marks_csv, name='export_marks_csv'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
]
