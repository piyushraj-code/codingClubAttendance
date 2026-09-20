from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from .models import DailyQuiz, QuizOption, QuizSubmission
from accounts.models import StudentUser


@login_required
def daily_quiz_view(request):
    """
    Displays today's active Daily Quiz in an interactive poll format.
    If already answered, displays poll results, correct answer, and explanation.
    """
    today = timezone.now().date()
    quiz = DailyQuiz.objects.filter(date=today, is_active=True).prefetch_related('options').first()

    # Fallback to the latest active quiz if none specifically for today
    if not quiz:
        quiz = DailyQuiz.objects.filter(is_active=True).prefetch_related('options').order_by('-date').first()

    submission = None
    options_stats = []
    has_submitted = False

    if quiz:
        submission = QuizSubmission.objects.filter(student=request.user, quiz=quiz).first()
        has_submitted = (submission is not None)
        options_stats = quiz.get_options_stats()

    return render(request, 'quizzes/daily_quiz.html', {
        'quiz': quiz,
        'submission': submission,
        'has_submitted': has_submitted,
        'options_stats': options_stats,
    })


@login_required
def submit_quiz_view(request, quiz_id):
    """
    Processes the student's poll vote for a quiz.
    Prevents duplicate submissions and awards points if correct.
    """
    if request.method != 'POST':
        return redirect('daily_quiz')

    quiz = get_object_or_404(DailyQuiz, pk=quiz_id, is_active=True)
    option_id = request.POST.get('selected_option')

    if not option_id:
        messages.warning(request, "Please select an option before submitting your answer.")
        return redirect('daily_quiz')

    option = get_object_or_404(QuizOption, pk=option_id, quiz=quiz)

    # Check if already submitted
    existing = QuizSubmission.objects.filter(student=request.user, quiz=quiz).first()
    if existing:
        messages.info(request, "You have already answered this daily quiz.")
        return redirect('daily_quiz')

    with transaction.atomic():
        is_correct = option.is_correct
        points = quiz.points if is_correct else 0

        submission = QuizSubmission.objects.create(
            student=request.user,
            quiz=quiz,
            selected_option=option,
            is_correct=is_correct,
            points_awarded=points
        )

        if is_correct:
            request.user.quiz_points = F('quiz_points') + points
            request.user.save(update_fields=['quiz_points'])
            request.user.refresh_from_db()
            messages.success(request, f"🎉 Excellent! Correct answer! You earned +{points} club points.")
        else:
            messages.info(request, "Nice try! Review the correct answer and explanation below.")

    return redirect('daily_quiz')


@login_required
def quiz_history_view(request):
    """View past quizzes and performance history."""
    quizzes = DailyQuiz.objects.filter(is_active=True).order_by('-date')
    submissions = {
        s.quiz_id: s for s in QuizSubmission.objects.filter(student=request.user)
    }

    quiz_list = []
    for q in quizzes:
        sub = submissions.get(q.id)
        quiz_list.append({
            'quiz': q,
            'submission': sub,
            'is_attempted': sub is not None,
            'is_correct': sub.is_correct if sub else False,
        })

    return render(request, 'quizzes/quiz_history.html', {
        'quiz_list': quiz_list,
    })


@login_required
def leaderboard_view(request):
    """
    Club Leaderboard ranking students by Quiz Points and Attendance Rate.
    """
    top_quiz_students = StudentUser.objects.filter(is_active=True).order_by('-quiz_points', 'name')[:20]

    # Pre-calculate attendance percentages for display
    students_with_stats = []
    all_students = StudentUser.objects.filter(is_active=True)
    for s in all_students:
        pct = s.get_attendance_percentage()
        students_with_stats.append({
            'student': s,
            'attendance_percentage': pct,
            'quiz_points': s.quiz_points,
        })

    # Sort by attendance percentage descending
    top_attendance_students = sorted(
        students_with_stats,
        key=lambda x: (x['attendance_percentage'], x['quiz_points']),
        reverse=True
    )[:20]

    return render(request, 'quizzes/leaderboard.html', {
        'top_quiz_students': top_quiz_students,
        'top_attendance_students': top_attendance_students,
    })
