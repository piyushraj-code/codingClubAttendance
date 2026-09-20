from django.utils import timezone

def club_context(request):
    """
    Global context processor providing club stats, notifications, and navigation helpers.
    """
    context = {
        'current_year': timezone.now().year,
        'today_date': timezone.now().date(),
    }

    if request.user.is_authenticated:
        # Check if user has taken today's quiz
        from quizzes.models import DailyQuiz, QuizSubmission
        today = timezone.now().date()
        today_quiz = DailyQuiz.objects.filter(date=today).first()
        user_attempted_today = False
        if today_quiz:
            user_attempted_today = QuizSubmission.objects.filter(
                student=request.user,
                quiz=today_quiz
            ).exists()

        context.update({
            'today_quiz': today_quiz,
            'user_attempted_today_quiz': user_attempted_today,
            'is_club_admin_user': request.user.is_club_admin or request.user.is_superuser or request.user.is_staff,
        })
    else:
        context['is_club_admin_user'] = False

    return context
