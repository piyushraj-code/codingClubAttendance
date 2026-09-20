from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Avg, Q
from django.http import HttpResponse
import csv
from datetime import datetime

from accounts.models import StudentUser
from attendance.models import ClubActivity, AttendanceRecord
from attendance.forms import ClubActivityForm
from quizzes.models import DailyQuiz, QuizOption, QuizSubmission


def is_admin(user):
    return user.is_authenticated and (user.is_club_admin or user.is_superuser or user.is_staff)


admin_required = user_passes_test(is_admin, login_url='admin_login')


def admin_login_view(request):
    """Dedicated Master Admin login portal."""
    if request.user.is_authenticated and is_admin(request.user):
        return redirect('admin_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = authenticate(username=email, password=password)
        if not user:
            # Also try matching case-insensitively
            try:
                matched_user = StudentUser.objects.get(email__iexact=email)
                user = authenticate(username=matched_user.email, password=password)
            except StudentUser.DoesNotExist:
                user = None

        if user and is_admin(user):
            login(request, user)
            messages.success(request, f"Master Admin access granted. Welcome, {user.name}!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid administrator credentials or unauthorized account.")

    return render(request, 'admin_portal/login.html')


@admin_required
def admin_dashboard_view(request):
    """Master Admin central command dashboard."""
    today = timezone.now().date()

    total_students = StudentUser.objects.filter(is_club_admin=False).count()
    total_activities = ClubActivity.objects.count()
    today_records = AttendanceRecord.objects.filter(date=today)
    today_present = today_records.filter(status__in=['PRESENT', 'LATE']).count()

    today_quiz = DailyQuiz.objects.filter(date=today).prefetch_related('options').first()
    quiz_votes_today = today_quiz.total_votes() if today_quiz else 0

    recent_students = StudentUser.objects.filter(is_club_admin=False).order_by('-date_joined')[:5]
    upcoming_activities = ClubActivity.objects.filter(date__gte=today).order_by('date')[:4]

    return render(request, 'admin_portal/dashboard.html', {
        'total_students': total_students,
        'total_activities': total_activities,
        'today_present': today_present,
        'today_quiz': today_quiz,
        'quiz_votes_today': quiz_votes_today,
        'recent_students': recent_students,
        'upcoming_activities': upcoming_activities,
        'today': today,
    })


@admin_required
def batch_mark_attendance_view(request):
    """
    Day-wise batch attendance marking for all club students.
    Select date and activity, filter students, mark Present/Absent/Late/Excused with fast batch toggles.
    """
    selected_date_str = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
    selected_activity_id = request.GET.get('activity', '')
    branch_filter = request.GET.get('branch', '')
    semester_filter = request.GET.get('semester', '')
    search_query = request.GET.get('q', '').strip()

    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()

    activities = ClubActivity.objects.filter(date=selected_date)
    if not activities.exists():
        activities = ClubActivity.objects.all().order_by('-date')[:10]

    selected_activity = None
    if selected_activity_id:
        selected_activity = ClubActivity.objects.filter(pk=selected_activity_id).first()

    # Query students
    students = StudentUser.objects.filter(is_active=True, is_club_admin=False)
    if branch_filter:
        students = students.filter(branch=branch_filter)
    if semester_filter:
        students = students.filter(semester=semester_filter)
    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) |
            Q(roll_number__icontains=search_query)
        )
    students = students.order_by('roll_number')

    # Fetch existing attendance records for the selected date & activity
    existing_records_qs = AttendanceRecord.objects.filter(date=selected_date)
    if selected_activity:
        existing_records_qs = existing_records_qs.filter(activity=selected_activity)

    existing_records_map = {r.student_id: r for r in existing_records_qs}

    # Handle POST saving of attendance batch
    if request.method == 'POST':
        saved_count = 0
        with transaction.atomic():
            for student in students:
                status_key = f"status_{student.id}"
                remarks_key = f"remarks_{student.id}"

                status = request.POST.get(status_key)
                remarks = request.POST.get(remarks_key, '').strip()

                if status in ['PRESENT', 'ABSENT', 'LATE', 'EXCUSED']:
                    # Update or create
                    record, created = AttendanceRecord.objects.update_or_create(
                        student=student,
                        date=selected_date,
                        activity=selected_activity,
                        defaults={
                            'status': status,
                            'remarks': remarks,
                            'marked_by': request.user,
                        }
                    )
                    saved_count += 1

        messages.success(
            request,
            f"Successfully saved attendance for {saved_count} students on {selected_date}."
        )
        return redirect(f"{request.path}?date={selected_date_str}&activity={selected_activity_id}")

    # Build student rows for template with their current status
    student_rows = []
    for s in students:
        rec = existing_records_map.get(s.id)
        current_status = rec.status if rec else 'PRESENT'  # Default to present for convenience
        remarks = rec.remarks if rec else ''
        student_rows.append({
            'student': s,
            'current_status': current_status,
            'remarks': remarks,
            'has_existing': (rec is not None),
        })

    return render(request, 'admin_portal/batch_mark.html', {
        'selected_date': selected_date,
        'selected_date_str': selected_date_str,
        'activities': activities,
        'selected_activity': selected_activity,
        'student_rows': student_rows,
        'branch_filter': branch_filter,
        'semester_filter': semester_filter,
        'search_query': search_query,
        'branches': StudentUser.BRANCH_CHOICES,
        'semesters': StudentUser.SEMESTER_CHOICES,
    })


@admin_required
def admin_quizzes_view(request):
    """List of all daily quizzes with status and vote metrics."""
    quizzes = DailyQuiz.objects.all().order_by('-date').prefetch_related('options')
    return render(request, 'admin_portal/quizzes_list.html', {
        'quizzes': quizzes,
    })


@admin_required
def create_quiz_view(request):
    """
    Create a new Daily Quiz with question, 4 poll options, correct answer indicator, and explanation.
    """
    if request.method == 'POST':
        date_str = request.POST.get('date')
        title = request.POST.get('title', '').strip()
        question = request.POST.get('question', '').strip()
        explanation = request.POST.get('explanation', '').strip()
        points = int(request.POST.get('points', 10))
        correct_index = request.POST.get('correct_option')  # '0', '1', '2', '3'

        options_texts = [
            request.POST.get(f'option_{i}', '').strip()
            for i in range(1, 5)
        ]

        # Validation
        if not question or not explanation or not date_str:
            messages.error(request, "Question, Explanation, and Date are required.")
        elif not any(options_texts):
            messages.error(request, "Please provide at least 2 options for the poll.")
        elif correct_index is None:
            messages.error(request, "Please mark which option is the correct answer.")
        else:
            try:
                quiz_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                quiz_date = timezone.now().date()

            with transaction.atomic():
                quiz = DailyQuiz.objects.create(
                    date=quiz_date,
                    title=title,
                    question=question,
                    explanation=explanation,
                    points=points,
                    created_by=request.user,
                    is_active=True
                )

                for i, text in enumerate(options_texts, start=1):
                    if text:
                        is_correct = (str(i) == str(correct_index))
                        QuizOption.objects.create(
                            quiz=quiz,
                            option_text=text,
                            is_correct=is_correct
                        )

            messages.success(request, f"Daily Quiz for {quiz.date} created successfully!")
            return redirect('admin_quizzes')

    return render(request, 'admin_portal/create_quiz.html', {
        'today': timezone.now().date().strftime('%Y-%m-%d'),
    })


@admin_required
def edit_quiz_view(request, quiz_id):
    """Edit an existing quiz question, options, and explanation."""
    quiz = get_object_or_404(DailyQuiz, pk=quiz_id)
    options = list(quiz.options.all().order_by('id'))

    if request.method == 'POST':
        quiz.title = request.POST.get('title', '').strip()
        quiz.question = request.POST.get('question', '').strip()
        quiz.explanation = request.POST.get('explanation', '').strip()
        quiz.points = int(request.POST.get('points', 10))
        quiz.is_active = ('is_active' in request.POST)
        correct_index = request.POST.get('correct_option')

        with transaction.atomic():
            quiz.save()
            for i, opt in enumerate(options, start=1):
                new_text = request.POST.get(f'option_{i}', '').strip()
                if new_text:
                    opt.option_text = new_text
                    opt.is_correct = (str(i) == str(correct_index))
                    opt.save()

        messages.success(request, f"Quiz for {quiz.date} updated successfully!")
        return redirect('admin_quizzes')

    return render(request, 'admin_portal/edit_quiz.html', {
        'quiz': quiz,
        'options': options,
    })


@admin_required
def delete_quiz_view(request, quiz_id):
    """Delete a daily quiz."""
    quiz = get_object_or_404(DailyQuiz, pk=quiz_id)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, "Daily Quiz deleted successfully.")
    return redirect('admin_quizzes')


@admin_required
def quiz_analytics_view(request, quiz_id):
    """View analytics and breakdown of student votes for a specific quiz."""
    quiz = get_object_or_404(DailyQuiz, pk=quiz_id)
    options_stats = quiz.get_options_stats()
    submissions = QuizSubmission.objects.filter(quiz=quiz).select_related('student', 'selected_option').order_by('-submitted_at')

    return render(request, 'admin_portal/quiz_analytics.html', {
        'quiz': quiz,
        'options_stats': options_stats,
        'submissions': submissions,
        'total_submissions': submissions.count(),
    })


@admin_required
def admin_activities_view(request):
    """List and manage club activities."""
    activities = ClubActivity.objects.all().order_by('-date')
    form = ClubActivityForm()

    if request.method == 'POST':
        form = ClubActivityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Club activity created successfully!")
            return redirect('admin_activities')

    return render(request, 'admin_portal/activities.html', {
        'activities': activities,
        'form': form,
    })


@admin_required
def admin_students_view(request):
    """List of all registered club members with attendance rates and quick actions."""
    search_query = request.GET.get('q', '').strip()
    branch_filter = request.GET.get('branch', '')
    semester_filter = request.GET.get('semester', '')

    students_qs = StudentUser.objects.filter(is_club_admin=False)
    if search_query:
        students_qs = students_qs.filter(
            Q(name__icontains=search_query) |
            Q(roll_number__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    if branch_filter:
        students_qs = students_qs.filter(branch=branch_filter)
    if semester_filter:
        students_qs = students_qs.filter(semester=semester_filter)

    students_data = []
    for s in students_qs.order_by('roll_number'):
        summary = s.get_attendance_summary()
        students_data.append({
            'student': s,
            'summary': summary,
        })

    return render(request, 'admin_portal/students_list.html', {
        'students_data': students_data,
        'search_query': search_query,
        'branch_filter': branch_filter,
        'semester_filter': semester_filter,
        'branches': StudentUser.BRANCH_CHOICES,
        'semesters': StudentUser.SEMESTER_CHOICES,
        'total_count': students_qs.count(),
    })


@admin_required
def export_all_attendance_csv(request):
    """Export complete club attendance records to CSV."""
    records = AttendanceRecord.objects.all().select_related('student', 'activity').order_by('-date', 'student__roll_number')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="club_attendance_master.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Roll Number', 'Student Name', 'Branch', 'Semester', 'Activity', 'Status', 'Remarks', 'Marked By'])

    for r in records:
        writer.writerow([
            r.date.strftime('%Y-%m-%d'),
            r.student.roll_number,
            r.student.name,
            r.student.get_branch_display(),
            f"Sem {r.student.semester}",
            r.activity.title if r.activity else 'General Meeting',
            r.get_status_display(),
            r.remarks,
            r.marked_by.name if r.marked_by else 'Admin'
        ])

    return response
