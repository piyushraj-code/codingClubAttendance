from django.urls import path
from . import views

urlpatterns = [
    path('daily/', views.daily_quiz_view, name='daily_quiz'),
    path('submit/<int:quiz_id>/', views.submit_quiz_view, name='submit_quiz'),
    path('history/', views.quiz_history_view, name='quiz_history'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]
