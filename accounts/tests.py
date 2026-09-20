from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import StudentUser, PasswordResetOTP
from accounts.otp_service import send_otp_for_user, verify_otp_code


class StudentAuthAndOTPTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = StudentUser.objects.create_user(
            name="Test Student",
            email="teststudent@example.com",
            password="Password123!",
            roll_number="22CS999",
            branch="CSE",
            semester=4,
            mobile_number="9800000001",
        )
        self.peer = StudentUser.objects.create_user(
            name="Peer Student",
            email="peer@example.com",
            password="Password123!",
            roll_number="22CS998",
            branch="CSE",
            semester=4,
            mobile_number="9800000002",
        )

    def test_student_login(self):
        response = self.client.post(reverse('login'), {
            'email': 'teststudent@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_student_registration(self):
        response = self.client.post(reverse('register'), {
            'name': 'New Member',
            'email': 'newmember@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'roll_number': '22IT888',
            'branch': 'IT',
            'semester': 3,
            'mobile_number': '9800000003',
            'bio': 'Test bio'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(StudentUser.objects.filter(email='newmember@example.com').exists())

    def test_otp_generation_and_verification(self):
        # Generate OTP
        success, msg, otp_obj = send_otp_for_user(self.student, 'email')
        self.assertTrue(success)
        self.assertIsNotNone(otp_obj)
        self.assertEqual(len(otp_obj.otp_code), 6)

        # Verify invalid OTP
        valid, err, _ = verify_otp_code(self.student, '000000')
        self.assertFalse(valid)

        # Verify correct OTP
        valid, ok_msg, token = verify_otp_code(self.student, otp_obj.otp_code)
        self.assertTrue(valid)
        self.assertIsNotNone(token)

        # Ensure OTP cannot be reused
        re_valid, _, _ = verify_otp_code(self.student, otp_obj.otp_code)
        self.assertFalse(re_valid)

    def test_peer_follow_system(self):
        self.client.login(username='teststudent@example.com', password='Password123!')
        
        # Follow peer
        response = self.client.post(reverse('follow_toggle', kwargs={'roll_number': self.peer.roll_number}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.student.is_following(self.peer))

        # Unfollow peer
        response = self.client.post(reverse('follow_toggle', kwargs={'roll_number': self.peer.roll_number}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.student.is_following(self.peer))
