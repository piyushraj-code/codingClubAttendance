from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import secrets


class StudentUserManager(BaseUserManager):
    """Custom user manager for StudentUser with email as the unique identifier."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        # Ensure username equals email if not specified
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_club_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class StudentUser(AbstractUser):
    """
    Custom user model representing a club student or club admin.
    """
    BRANCH_CHOICES = [
        ('CSE', 'Computer Science & Engineering'),
        ('IT', 'Information Technology'),
        ('ECE', 'Electronics & Communication Engineering'),
        ('EE', 'Electrical Engineering'),
        ('ME', 'Mechanical Engineering'),
        ('CE', 'Civil Engineering'),
        ('AIML', 'AI & Machine Learning'),
        ('DS', 'Data Science'),
        ('OTHER', 'Other Department'),
    ]

    SEMESTER_CHOICES = [(i, f'Semester {i}') for i in range(1, 9)]

    name = models.CharField(max_length=150, help_text="Full name of student")
    email = models.EmailField(unique=True, db_index=True)
    roll_number = models.CharField(max_length=50, unique=True, db_index=True)
    branch = models.CharField(max_length=50, choices=BRANCH_CHOICES, default='CSE')
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_CHOICES, default=1)
    mobile_number = models.CharField(max_length=20, unique=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, default="Passionate club member eager to learn and collaborate.")
    quiz_points = models.PositiveIntegerField(default=0)
    
    # Social follow system: student can follow other students
    followers = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='following',
        blank=True
    )

    is_club_admin = models.BooleanField(
        default=False,
        help_text="Designates whether this student has master club admin privileges."
    )

    objects = StudentUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'roll_number', 'branch', 'semester', 'mobile_number']

    class Meta:
        ordering = ['roll_number']
        verbose_name = 'Student User'
        verbose_name_plural = 'Student Users'

    def __str__(self):
        return f"{self.name} ({self.roll_number})"

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    @property
    def avatar_url(self):
        """Returns the profile picture URL or a standard UI avatar fallback."""
        if self.profile_pic and hasattr(self.profile_pic, 'url'):
            return self.profile_pic.url
        # Fallback to UI-Avatars for clean visual display
        clean_name = self.name.replace(' ', '+') if self.name else 'Student'
        return f"https://ui-avatars.com/api/?name={clean_name}&background=4f46e5&color=fff&size=150"

    def is_following(self, user):
        """Check if this student is following another user."""
        return self.following.filter(pk=user.pk).exists()

    def get_attendance_percentage(self):
        """Calculate overall attendance percentage for this student."""
        from attendance.models import AttendanceRecord
        total = AttendanceRecord.objects.filter(student=self).count()
        if total == 0:
            return 0.0
        present_count = AttendanceRecord.objects.filter(
            student=self,
            status__in=['PRESENT', 'LATE']
        ).count()
        return round((present_count / total) * 100, 1)

    def get_attendance_summary(self):
        """Returns dictionary of attendance statistics."""
        from attendance.models import AttendanceRecord
        records = AttendanceRecord.objects.filter(student=self)
        total = records.count()
        present = records.filter(status='PRESENT').count()
        absent = records.filter(status='ABSENT').count()
        late = records.filter(status='LATE').count()
        excused = records.filter(status='EXCUSED').count()
        effective_present = present + late
        percentage = round((effective_present / total) * 100, 1) if total > 0 else 0.0
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'percentage': percentage,
        }


class PasswordResetOTP(models.Model):
    """
    Model storing OTPs for password reset via Email or Mobile.
    Valid for 10 minutes.
    """
    OTP_TYPE_CHOICES = [
        ('email', 'Email OTP'),
        ('mobile', 'Mobile OTP'),
    ]

    user = models.ForeignKey(StudentUser, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPE_CHOICES)
    target_destination = models.CharField(max_length=100)
    reset_token = models.CharField(max_length=64, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    @classmethod
    def generate_otp(cls, user, otp_type, target):
        # Invalidate old unused OTPs for this user
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        # Generate 6-digit random code
        code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = timezone.now() + timedelta(minutes=10)
        return cls.objects.create(
            user=user,
            otp_code=code,
            otp_type=otp_type,
            target_destination=target,
            expires_at=expires_at
        )
