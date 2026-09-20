"""
URL configuration for club_attendance project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', lambda request: redirect('student_dashboard' if request.user.is_authenticated else 'login'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('attendance/', include('attendance.urls')),
    path('quiz/', include('quizzes.urls')),
    path('admin-portal/', include('admin_portal.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
