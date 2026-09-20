from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login_view, name='admin_login'),
    path('', views.admin_dashboard_view, name='admin_dashboard'),
    path('attendance/mark/', views.batch_mark_attendance_view, name='admin_batch_mark'),
    path('attendance/export/', views.export_all_attendance_csv, name='admin_export_attendance'),
    path('quizzes/', views.admin_quizzes_view, name='admin_quizzes'),
    path('quizzes/create/', views.create_quiz_view, name='admin_create_quiz'),
    path('quizzes/<int:quiz_id>/edit/', views.edit_quiz_view, name='admin_edit_quiz'),
    path('quizzes/<int:quiz_id>/delete/', views.delete_quiz_view, name='admin_delete_quiz'),
    path('quizzes/<int:quiz_id>/analytics/', views.quiz_analytics_view, name='admin_quiz_analytics'),
    path('activities/', views.admin_activities_view, name='admin_activities'),
    path('students/', views.admin_students_view, name='admin_students'),
]
