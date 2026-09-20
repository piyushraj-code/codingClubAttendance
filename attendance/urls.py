from django.urls import path
from . import views

urlpatterns = [
    path('my-attendance/', views.my_attendance_view, name='my_attendance'),
    path('peer/<str:roll_number>/', views.peer_attendance_view, name='peer_attendance'),
    path('activities/', views.activities_list_view, name='activities_list'),
    path('activities/<int:activity_id>/', views.activity_detail_view, name='activity_detail'),
    path('my-attendance/export/', views.export_my_attendance_csv, name='export_my_attendance'),
]
