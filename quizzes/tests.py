from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import StudentUser
from quizzes.models import DailyQuiz, QuizOption, QuizSubmission


class DailyQuizTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = StudentUser.objects.create_user(
            name="Quiz Tester",
            email="quiztester@example.com",
            password="Password123!",
            roll_number="22AI100",
            branch="AIML",
            semester=3,
            mobile_number="9800000010",
        )

        today = timezone.now().date()
        self.quiz = DailyQuiz.objects.create(
            date=today,
            title="Test Quiz",
            question="Is Python an interpreted language?",
            explanation="Python is generally classified as an interpreted language as its bytecode is executed by the CPython interpreter.",
            points=10,
        )
        self.opt_yes = QuizOption.objects.create(quiz=self.quiz, option_text="Yes", is_correct=True)
        self.opt_no = QuizOption.objects.create(quiz=self.quiz, option_text="No", is_correct=False)

    def test_quiz_submission_correct_answer(self):
        self.client.login(username='quiztester@example.com', password='Password123!')
        
        # Initial points
        self.assertEqual(self.student.quiz_points, 0)

        # Submit correct answer
        response = self.client.post(reverse('submit_quiz', kwargs={'quiz_id': self.quiz.id}), {
            'selected_option': self.opt_yes.id
        })
        self.assertEqual(response.status_code, 302)

        # Refresh student and check points
        self.student.refresh_from_db()
        self.assertEqual(self.student.quiz_points, 10)

        # Verify submission record
        sub = QuizSubmission.objects.filter(student=self.student, quiz=self.quiz).first()
        self.assertIsNotNone(sub)
        self.assertTrue(sub.is_correct)
        self.assertEqual(sub.points_awarded, 10)

    def test_quiz_prevent_duplicate_submission(self):
        self.client.login(username='quiztester@example.com', password='Password123!')

        # First submit
        self.client.post(reverse('submit_quiz', kwargs={'quiz_id': self.quiz.id}), {
            'selected_option': self.opt_yes.id
        })

        # Second submit attempt
        response = self.client.post(reverse('submit_quiz', kwargs={'quiz_id': self.quiz.id}), {
            'selected_option': self.opt_no.id
        })
        self.assertEqual(response.status_code, 302)

        # Ensure only 1 submission exists
        self.assertEqual(QuizSubmission.objects.filter(student=self.student, quiz=self.quiz).count(), 1)
        # Ensure points not awarded twice
        self.student.refresh_from_db()
        self.assertEqual(self.student.quiz_points, 10)

    def test_poll_options_stats_and_explanation(self):
        self.client.login(username='quiztester@example.com', password='Password123!')
        
        self.client.post(reverse('submit_quiz', kwargs={'quiz_id': self.quiz.id}), {
            'selected_option': self.opt_yes.id
        })

        response = self.client.get(reverse('daily_quiz'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "100.0%")
        self.assertContains(response, "Detailed Explanation")
        self.assertContains(response, self.quiz.explanation)
