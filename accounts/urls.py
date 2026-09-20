from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('profile/', views.my_profile_view, name='my_profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<str:roll_number>/', views.public_profile_view, name='public_profile'),
    path('profile/<str:roll_number>/follow/', views.follow_toggle_view, name='follow_toggle'),
    path('directory/', views.students_directory_view, name='students_directory'),
    
    # OTP Password Reset URLs
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
]
