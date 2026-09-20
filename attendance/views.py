import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from accounts.models import StudentUser
from .models import AttendanceRecord, ClubActivity


@login_required
def my_attendance_view(request):
    """
    Detailed attendance report for the authenticated student.
    Filterable by month, activity type, and status.
    """
    student = request.user
    status_filter = request.GET.get('status', '').strip()
    activity_filter = request.GET.get('activity', '').strip()

    records = AttendanceRecord.objects.filter(student=student).select_related('activity').order_by('-date')

    if status_filter:
        records = records.filter(status=status_filter)
    if activity_filter:
        records = records.filter(activity_id=activity_filter)

    summary = student.get_attendance_summary()
    activities = ClubActivity.objects.all().order_by('-date')

    return render(request, 'attendance/my_attendance.html', {
        'records': records,
        'summary': summary,
        'activities': activities,
        'status_filter': status_filter,
        'activity_filter': activity_filter,
    })


@login_required
def peer_attendance_view(request, roll_number):
    """
    Check another student's attendance records as part of peer transparency.
    """
    peer = get_object_or_404(StudentUser, roll_number=roll_number)
    records = AttendanceRecord.objects.filter(student=peer).select_related('activity').order_by('-date')
    summary = peer.get_attendance_summary()

    return render(request, 'attendance/peer_attendance.html', {
        'peer': peer,
        'records': records,
        'summary': summary,
    })


@login_required
def activities_list_view(request):
    """List of all club activities with attendee counts."""
    activities = ClubActivity.objects.all().order_by('-date')
    return render(request, 'attendance/activities_list.html', {
        'activities': activities,
    })


@login_required
def activity_detail_view(request, activity_id):
    """Details of a single club activity and who attended."""
    activity = get_object_or_404(ClubActivity, pk=activity_id)
    attendees = AttendanceRecord.objects.filter(activity=activity).select_related('student').order_by('student__roll_number')
    
    # Check if current user attended
    user_attendance = AttendanceRecord.objects.filter(activity=activity, student=request.user).first()

    return render(request, 'attendance/activity_detail.html', {
        'activity': activity,
        'attendees': attendees,
        'user_attendance': user_attendance,
    })


@login_required
def export_my_attendance_csv(request):
    """Export the student's attendance records to CSV."""
    student = request.user
    records = AttendanceRecord.objects.filter(student=student).select_related('activity').order_by('-date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{student.roll_number}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Activity Title', 'Type', 'Status', 'Remarks'])

    for r in records:
        writer.writerow([
            r.date.strftime('%Y-%m-%d'),
            r.activity.title if r.activity else 'General Meeting',
            r.activity.get_activity_type_display() if r.activity else 'General',
            r.get_status_display(),
            r.remarks
        ])

    return response
