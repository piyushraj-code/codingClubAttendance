from django.db import models
from django.conf import settings
from django.utils import timezone


class ClubActivity(models.Model):
    """
    Represents a scheduled club activity or session (workshop, meeting, hackathon, etc.)
    """
    ACTIVITY_TYPE_CHOICES = [
        ('WORKSHOP', 'Technical Workshop'),
        ('MEETING', 'Club General Meeting'),
        ('HACKATHON', 'Hackathon / Coding Sprint'),
        ('PROJECT', 'Project Collaboration Session'),
        ('LECTURE', 'Guest Speaker Lecture'),
        ('COMPETITION', 'Club Competition'),
        ('OTHER', 'General Club Activity'),
    ]

    title = models.CharField(max_length=200)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, default='WORKSHOP')
    date = models.DateField(default=timezone.now, db_index=True)
    time = models.TimeField(blank=True, null=True)
    venue = models.CharField(max_length=200, default='Main Club Room / Lab 101')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Club Activity'
        verbose_name_plural = 'Club Activities'

    def __str__(self):
        return f"{self.title} ({self.date})"

    @property
    def total_attendees_count(self):
        return self.attendees.filter(status__in=['PRESENT', 'LATE']).count()


class AttendanceRecord(models.Model):
    """
    Represents an attendance entry for a student on a specific date / activity.
    """
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    activity = models.ForeignKey(
        ClubActivity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendees'
    )
    date = models.DateField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PRESENT')
    remarks = models.CharField(max_length=255, blank=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'student__roll_number']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'activity', 'date'],
                name='unique_student_activity_attendance'
            )
        ]
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        activity_name = self.activity.title if self.activity else "General"
        return f"{self.student.roll_number} - {activity_name} ({self.date}): {self.status}"
