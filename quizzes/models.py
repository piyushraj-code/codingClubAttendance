from django.db import models
from django.conf import settings
from django.utils import timezone


class DailyQuiz(models.Model):
    """
    Daily Quiz / Poll model with questions, options, and explanations.
    """
    date = models.DateField(default=timezone.now, db_index=True)
    title = models.CharField(max_length=200, blank=True, help_text="Optional topic or title (e.g. Python Challenge #12)")
    question = models.TextField(help_text="The daily quiz question or poll prompt")
    explanation = models.TextField(help_text="Detailed explanation of the correct answer, shown after student votes")
    points = models.PositiveIntegerField(default=10, help_text="Points awarded for a correct answer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_quizzes'
    )

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Daily Quiz'
        verbose_name_plural = 'Daily Quizzes'

    def __str__(self):
        title_str = self.title or self.question[:40]
        return f"{self.date}: {title_str}"

    def total_votes(self):
        return self.submissions.count()

    def get_options_stats(self):
        """Returns each option annotated with vote count and vote percentage."""
        total = self.total_votes()
        stats = []
        for opt in self.options.all():
            votes = opt.submissions.count()
            percentage = round((votes / total) * 100, 1) if total > 0 else 0
            stats.append({
                'option': opt,
                'votes': votes,
                'percentage': percentage,
                'is_correct': opt.is_correct,
            })
        return stats


class QuizOption(models.Model):
    """
    Choice / option for a daily quiz.
    """
    quiz = models.ForeignKey(DailyQuiz, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False, help_text="Check if this is the correct answer")

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.option_text} ({'Correct' if self.is_correct else 'Incorrect'})"

    def vote_count(self):
        return self.submissions.count()


class QuizSubmission(models.Model):
    """
    Represents a student's answer/vote to a daily quiz.
    Enforces exactly one submission per student per quiz.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_submissions'
    )
    quiz = models.ForeignKey(DailyQuiz, on_delete=models.CASCADE, related_name='submissions')
    selected_option = models.ForeignKey(QuizOption, on_delete=models.CASCADE, related_name='submissions')
    is_correct = models.BooleanField(default=False)
    points_awarded = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'quiz'],
                name='unique_student_daily_quiz_submission'
            )
        ]
        verbose_name = 'Quiz Submission'
        verbose_name_plural = 'Quiz Submissions'

    def __str__(self):
        return f"{self.student.roll_number} - {self.quiz} ({'Correct' if self.is_correct else 'Incorrect'})"
