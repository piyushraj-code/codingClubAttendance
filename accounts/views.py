from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from .models import StudentUser, PasswordResetOTP
from .forms import (
    StudentRegistrationForm,
    StudentLoginForm,
    StudentProfileUpdateForm,
    ForgotPasswordRequestForm,
    VerifyOTPForm,
    ResetPasswordForm,
)
from .otp_service import send_otp_for_user, verify_otp_code


def register_view(request):
    """Student self-registration view."""
    if request.user.is_authenticated:
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Welcome to the Club, {user.name}! Your account has been created. Please sign in."
            )
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Student and Admin login with Email and Password."""
    if request.user.is_authenticated:
        if request.user.is_club_admin or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.name}!")
            
            # Check for redirect next param
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            if user.is_club_admin or user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('student_dashboard')
    else:
        form = StudentLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def student_dashboard_view(request):
    """
    Main dashboard for logged-in students.
    Shows attendance metrics, today's quiz widget, and recent club activities.
    """
    from attendance.models import AttendanceRecord, ClubActivity
    from quizzes.models import DailyQuiz, QuizSubmission

    student = request.user
    today = timezone.now().date()

    # Attendance statistics
    summary = student.get_attendance_summary()
    recent_attendance = AttendanceRecord.objects.filter(
        student=student
    ).select_related('activity').order_by('-date')[:5]

    # Daily Quiz status
    today_quiz = DailyQuiz.objects.filter(date=today).prefetch_related('options').first()
    quiz_submission = None
    if today_quiz:
        quiz_submission = QuizSubmission.objects.filter(
            student=student,
            quiz=today_quiz
        ).first()

    # Upcoming / Recent Club activities
    upcoming_activities = ClubActivity.objects.filter(
        date__gte=today
    ).order_by('date')[:3]

    context = {
        'student': student,
        'summary': summary,
        'recent_attendance': recent_attendance,
        'today_quiz': today_quiz,
        'quiz_submission': quiz_submission,
        'upcoming_activities': upcoming_activities,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def my_profile_view(request):
    """View personal profile with full attendance history and followers list."""
    from attendance.models import AttendanceRecord
    student = request.user
    summary = student.get_attendance_summary()
    attendance_records = AttendanceRecord.objects.filter(
        student=student
    ).select_related('activity').order_by('-date')

    return render(request, 'accounts/profile.html', {
        'profile_user': student,
        'is_self': True,
        'summary': summary,
        'attendance_records': attendance_records,
    })


@login_required
def edit_profile_view(request):
    """Update profile picture, bio, branch, semester, and mobile."""
    student = request.user
    if request.method == 'POST':
        form = StudentProfileUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('my_profile')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = StudentProfileUpdateForm(instance=student)

    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def public_profile_view(request, roll_number):
    """
    Public profile of any student.
    Allows peers to inspect profile details, attendance records, and toggle follow status.
    """
    from attendance.models import AttendanceRecord
    target_student = get_object_or_404(StudentUser, roll_number=roll_number)
    is_self = (request.user == target_student)

    summary = target_student.get_attendance_summary()
    attendance_records = AttendanceRecord.objects.filter(
        student=target_student
    ).select_related('activity').order_by('-date')

    is_following = request.user.is_following(target_student)

    return render(request, 'accounts/profile.html', {
        'profile_user': target_student,
        'is_self': is_self,
        'is_following': is_following,
        'summary': summary,
        'attendance_records': attendance_records,
    })


@login_required
def follow_toggle_view(request, roll_number):
    """Toggle following status for a peer student."""
    target_student = get_object_or_404(StudentUser, roll_number=roll_number)
    
    if request.user == target_student:
        messages.warning(request, "You cannot follow yourself.")
        return redirect('public_profile', roll_number=roll_number)

    if request.user.is_following(target_student):
        request.user.following.remove(target_student)
        messages.info(request, f"You have unfollowed {target_student.name}.")
    else:
        request.user.following.add(target_student)
        messages.success(request, f"You are now following {target_student.name}!")

    # Check if request is AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'is_following': request.user.is_following(target_student),
            'followers_count': target_student.followers.count(),
        })

    return redirect('public_profile', roll_number=roll_number)


@login_required
def students_directory_view(request):
    """Directory listing all registered club students with search & filter."""
    query = request.GET.get('q', '').strip()
    branch_filter = request.GET.get('branch', '').strip()
    semester_filter = request.GET.get('semester', '').strip()

    students = StudentUser.objects.filter(is_active=True).exclude(pk=request.user.pk)

    if query:
        students = students.filter(
            Q(name__icontains=query) |
            Q(roll_number__icontains=query) |
            Q(email__icontains=query)
        )
    if branch_filter:
        students = students.filter(branch=branch_filter)
    if semester_filter:
        students = students.filter(semester=semester_filter)

    students = students.order_by('-quiz_points', 'roll_number')

    return render(request, 'accounts/directory.html', {
        'students': students,
        'query': query,
        'branch_filter': branch_filter,
        'semester_filter': semester_filter,
        'branches': StudentUser.BRANCH_CHOICES,
        'semesters': StudentUser.SEMESTER_CHOICES,
    })


# --- OTP Password Reset Workflow ---

def forgot_password_view(request):
    """Step 1: Input Email/Mobile and request OTP."""
    if request.method == 'POST':
        form = ForgotPasswordRequestForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            method = form.cleaned_data['otp_method']
            success, msg, otp_obj = send_otp_for_user(user, method)
            if success:
                request.session['reset_user_id'] = user.pk
                request.session['reset_method'] = method
                # Save preview code in session for local development convenience if DEBUG
                from django.conf import settings
                if settings.DEBUG and otp_obj:
                    request.session['dev_otp_preview'] = otp_obj.otp_code

                messages.success(request, msg)
                return redirect('verify_otp')
            else:
                messages.error(request, msg)
    else:
        form = ForgotPasswordRequestForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


def verify_otp_view(request):
    """Step 2: Enter the 6-digit OTP."""
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.warning(request, "Please request an OTP first.")
        return redirect('forgot_password')

    user = get_object_or_404(StudentUser, pk=user_id)
    dev_otp = request.session.get('dev_otp_preview')

    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['otp_code']
            success, msg, token = verify_otp_code(user, code)
            if success:
                request.session['reset_verified_token'] = token
                messages.success(request, "OTP verified! Please set your new password.")
                return redirect('reset_password')
            else:
                messages.error(request, msg)
    else:
        form = VerifyOTPForm()

    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'user': user,
        'method': request.session.get('reset_method', 'email'),
        'dev_otp': dev_otp,
    })


def reset_password_view(request):
    """Step 3: Enter new password with valid token."""
    user_id = request.session.get('reset_user_id')
    token = request.session.get('reset_verified_token')

    if not user_id or not token:
        messages.warning(request, "Password reset session expired. Please start again.")
        return redirect('forgot_password')

    user = get_object_or_404(StudentUser, pk=user_id)
    # Check that this token is valid in database
    otp_record = PasswordResetOTP.objects.filter(user=user, reset_token=token).first()
    if not otp_record:
        messages.error(request, "Invalid or expired reset session.")
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()

            # Clean up token
            otp_record.reset_token = None
            otp_record.save()
            request.session.pop('reset_user_id', None)
            request.session.pop('reset_verified_token', None)
            request.session.pop('dev_otp_preview', None)

            messages.success(request, "Your password has been reset successfully! You can now log in.")
            return redirect('login')
    else:
        form = ResetPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form, 'user': user})
