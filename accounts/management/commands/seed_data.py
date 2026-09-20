from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import StudentUser
from attendance.models import ClubActivity, AttendanceRecord
from quizzes.models import DailyQuiz, QuizOption, QuizSubmission


class Command(BaseCommand):
    help = 'Seeds initial master admin, students, club activities, attendance records, and daily quizzes.'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        # 1. Master Admin
        admin_email = "admin@club.edu"
        admin, created = StudentUser.objects.get_or_create(
            email=admin_email,
            defaults={
                'name': 'Club Master Admin',
                'username': admin_email,
                'roll_number': 'ADMIN001',
                'branch': 'CSE',
                'semester': 8,
                'mobile_number': '9876543210',
                'is_staff': True,
                'is_superuser': True,
                'is_club_admin': True,
                'bio': 'Chief Club Administrator & Coordinator.',
            }
        )
        if created:
            admin.set_password('Admin@123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Created Master Admin: {admin_email} (Password: Admin@123)"))
        else:
            admin.is_staff = True
            admin.is_superuser = True
            admin.is_club_admin = True
            admin.set_password('Admin@123')
            admin.save()
            self.stdout.write(f"Updated Master Admin: {admin_email}")

        # 2. Sample Students
        sample_students_data = [
            {
                'name': 'Arun Sharma',
                'email': 'arun.sharma@example.com',
                'roll_number': '22CSE001',
                'branch': 'CSE',
                'semester': 5,
                'mobile_number': '9811111111',
                'quiz_points': 50,
                'bio': 'Passionate about Python backend and open source contribution.'
            },
            {
                'name': 'Priya Verma',
                'email': 'priya.verma@example.com',
                'roll_number': '22CSE002',
                'branch': 'CSE',
                'semester': 5,
                'mobile_number': '9822222222',
                'quiz_points': 60,
                'bio': 'Club lead designer and web enthusiast.'
            },
            {
                'name': 'Rahul Kumar',
                'email': 'rahul.kumar@example.com',
                'roll_number': '22IT015',
                'branch': 'IT',
                'semester': 4,
                'mobile_number': '9833333333',
                'quiz_points': 30,
                'bio': 'Competitive programmer and cloud computing explorer.'
            },
            {
                'name': 'Sneha Patel',
                'email': 'sneha.patel@example.com',
                'roll_number': '23AIML008',
                'branch': 'AIML',
                'semester': 3,
                'mobile_number': '9844444444',
                'quiz_points': 70,
                'bio': 'Machine learning researcher and robotics club member.'
            },
            {
                'name': 'Rohan Singh',
                'email': 'rohan.singh@example.com',
                'roll_number': '21ECE044',
                'branch': 'ECE',
                'semester': 6,
                'mobile_number': '9855555555',
                'quiz_points': 40,
                'bio': 'IoT hardware builder and drone enthusiast.'
            },
        ]

        created_students = []
        for s_data in sample_students_data:
            s_email = s_data['email']
            points = s_data.pop('quiz_points', 0)
            student, s_created = StudentUser.objects.get_or_create(
                email=s_email,
                defaults={
                    **s_data,
                    'username': s_email,
                    'is_club_admin': False,
                    'quiz_points': points,
                }
            )
            if s_created:
                student.set_password('Student@123')
                student.save()
            created_students.append(student)

        self.stdout.write(self.style.SUCCESS(f"Created/Verified {len(created_students)} student accounts (Password: Student@123)."))

        # Social follow connections
        if len(created_students) >= 3:
            created_students[0].following.add(created_students[1], created_students[2])
            created_students[1].following.add(created_students[0], created_students[3])
            created_students[2].following.add(created_students[0])

        # 3. Sample Club Activities
        today = timezone.now().date()
        activities_data = [
            {
                'title': 'Full-Stack Web Dev with Django & Cloud Workshop',
                'activity_type': 'WORKSHOP',
                'date': today - timedelta(days=7),
                'venue': 'Tech Lab 201',
                'description': 'Hands-on session on building web applications with Django and preparing for cloud hosting.',
            },
            {
                'title': 'AI & Machine Learning Hands-On Sprint',
                'activity_type': 'HACKATHON',
                'date': today - timedelta(days=3),
                'venue': 'Auditorium Hall B',
                'description': 'Team problem-solving sprint applying machine learning models on real datasets.',
            },
            {
                'title': 'Club General Sync & Project Presentations',
                'activity_type': 'MEETING',
                'date': today,
                'venue': 'Seminar Hall 102',
                'description': 'Weekly project progress review and attendance verification session.',
            },
            {
                'title': 'Azure Cloud Architecture & DevOps Seminar',
                'activity_type': 'LECTURE',
                'date': today + timedelta(days=5),
                'venue': 'Main Auditorium',
                'description': 'Guest lecture on microservices, MySQL databases, and cloud deployments on Azure.',
            },
        ]

        created_activities = []
        for a_data in activities_data:
            act, _ = ClubActivity.objects.get_or_create(
                title=a_data['title'],
                date=a_data['date'],
                defaults=a_data
            )
            created_activities.append(act)

        # 4. Attendance Records
        statuses = ['PRESENT', 'PRESENT', 'PRESENT', 'LATE', 'ABSENT']
        for act in created_activities[:3]:
            for i, student in enumerate(created_students):
                status = statuses[(i + act.id) % len(statuses)]
                AttendanceRecord.objects.get_or_create(
                    student=student,
                    activity=act,
                    date=act.date,
                    defaults={
                        'status': status,
                        'remarks': 'Attended and participated actively' if status == 'PRESENT' else '',
                        'marked_by': admin,
                    }
                )

        self.stdout.write(self.style.SUCCESS("Created sample attendance records."))

        # 5. Daily Quizzes (Poll format with explanation)
        quiz_data_1 = {
            'date': today,
            'title': 'Python & Cloud Architecture Challenge',
            'question': 'What is the primary role of WhiteNoise in a Python Django production web application?',
            'explanation': 'WhiteNoise allows a Python web application to serve its own static files (CSS, JS, fonts) directly with compression and caching headers, eliminating the complex requirement of setting up a separate web server or reverse proxy just for static assets in containerized environments like Azure.',
            'points': 10,
            'options': [
                ('A database query caching mechanism', False),
                ('Serves static files directly from the Python web application with gzip/brotli compression', True),
                ('A background worker queue for celery tasks', False),
                ('A DNS load balancing service', False),
            ]
        }

        quiz1, q1_created = DailyQuiz.objects.get_or_create(
            date=quiz_data_1['date'],
            defaults={
                'title': quiz_data_1['title'],
                'question': quiz_data_1['question'],
                'explanation': quiz_data_1['explanation'],
                'points': quiz_data_1['points'],
                'created_by': admin,
            }
        )
        if q1_created:
            for text, is_corr in quiz_data_1['options']:
                QuizOption.objects.create(quiz=quiz1, option_text=text, is_correct=is_corr)

        # Sample submission for student 0
        if q1_created and len(created_students) > 0:
            correct_opt = quiz1.options.filter(is_correct=True).first()
            if correct_opt:
                QuizSubmission.objects.get_or_create(
                    student=created_students[0],
                    quiz=quiz1,
                    defaults={
                        'selected_option': correct_opt,
                        'is_correct': True,
                        'points_awarded': 10,
                    }
                )

        quiz_data_2 = {
            'date': today - timedelta(days=1),
            'title': 'Python Fundamentals Poll',
            'question': 'Which of the following built-in Python data types is immutable?',
            'explanation': 'In Python, tuples are immutable sequences. Once created, elements cannot be modified, appended, or deleted in place. Lists, dictionaries, and sets are all mutable.',
            'points': 10,
            'options': [
                ('List', False),
                ('Dictionary', False),
                ('Tuple', True),
                ('Set', False),
            ]
        }

        quiz2, q2_created = DailyQuiz.objects.get_or_create(
            date=quiz_data_2['date'],
            defaults={
                'title': quiz_data_2['title'],
                'question': quiz_data_2['question'],
                'explanation': quiz_data_2['explanation'],
                'points': quiz_data_2['points'],
                'created_by': admin,
            }
        )
        if q2_created:
            for text, is_corr in quiz_data_2['options']:
                QuizOption.objects.create(quiz=quiz2, option_text=text, is_correct=is_corr)

        self.stdout.write(self.style.SUCCESS("Created sample daily quizzes and poll submissions."))
        self.stdout.write(self.style.SUCCESS("\n==> Database Seeding Completed Successfully!"))
