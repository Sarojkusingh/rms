from django.urls import path
from . import views

urlpatterns = [
    path('results/process/', views.results_process, name='results_process'),
    path('results/workflow/', views.results_approve_publish, name='results_approve_publish'),
    path('results/my-results/', views.student_results, name='student_results'),
    path('results/marksheet/<int:result_id>/', views.student_marksheet, name='student_marksheet'),
    path('results/transcript/<int:student_id>/', views.student_transcript, name='student_transcript'),
]
