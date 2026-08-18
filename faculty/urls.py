from django.urls import path
from . import views

urlpatterns = [
    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/add/', views.faculty_add, name='faculty_add'),
    path('faculty/allocation/', views.faculty_allocation, name='faculty_allocation'),
    path('faculty/<int:id>/', views.faculty_profile, name='faculty_profile'),
    path('faculty/<int:id>/edit/', views.faculty_edit, name='faculty_edit'),
]
