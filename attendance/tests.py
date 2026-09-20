from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import StudentUser
from attendance.models import ClubActivity, AttendanceRecord


class AttendanceAndAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = StudentUser.objects.create_superuser(
            email="admin@test.com",
            password="AdminPassword123!",
            name="Test Admin",
            roll_number="ADMIN099",
            branch="CSE",
            semester=8,
            mobile_number="9800000020",
        )
        self.student = StudentUser.objects.create_user(
            email="student@test.com",
            password="StudentPassword123!",
            name="Test Student",
            roll_number="22CS100",
            branch="CSE",
            semester=4,
            mobile_number="9800000021",
        )
        self.activity = ClubActivity.objects.create(
            title="Django Azure Workshop",
            activity_type="WORKSHOP",
            date=timezone.now().date(),
            venue="Lab 404"
        )

    def test_batch_mark_attendance_as_admin(self):
        self.client.login(username='admin@test.com', password='AdminPassword123!')
        
        # Batch mark attendance
        date_str = timezone.now().date().strftime('%Y-%m-%d')
        post_data = {
            f"status_{self.student.id}": "PRESENT",
            f"remarks_{self.student.id}": "Active participation",
        }
        response = self.client.post(
            f"{reverse('admin_batch_mark')}?date={date_str}&activity={self.activity.id}",
            post_data
        )
        self.assertEqual(response.status_code, 302)

        # Check record created
        record = AttendanceRecord.objects.filter(student=self.student, date=timezone.now().date()).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.status, "PRESENT")
        self.assertEqual(record.remarks, "Active participation")

        # Check student attendance percentage calculation
        self.assertEqual(self.student.get_attendance_percentage(), 100.0)

    def test_export_attendance_csv(self):
        # Create a sample attendance record
        AttendanceRecord.objects.create(
            student=self.student,
            activity=self.activity,
            date=timezone.now().date(),
            status="PRESENT",
            marked_by=self.admin
        )

        # Student CSV export
        self.client.login(username='student@test.com', password='StudentPassword123!')
        response = self.client.get(reverse('export_my_attendance'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn("Django Azure Workshop", response.content.decode('utf-8'))
