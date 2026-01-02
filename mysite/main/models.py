from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


# =========================
#        PROFILE
# =========================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    ROLE_CHOICES = (
        ("job_seeker", "Job Seeker"),
        ("employer", "Employer"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="job_seeker"
    )

    # Personal info
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.ImageField(
        upload_to="profile_images/",
        blank=True,
        null=True
    )

    # Job preferences
    preferred_job_titles = models.CharField(max_length=255, blank=True)
    job_categories = models.CharField(max_length=255, blank=True)
    employment_type = models.CharField(max_length=50, blank=True)
    preferred_location = models.CharField(max_length=255, blank=True)

    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('employers', 'Employers Only'),
            ('private', 'Private')
        ],
        default='employers'
    )
    allow_contact = models.BooleanField(default=True)

    # Notifications
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)

    # Appearance preferences
    dark_mode = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='en', blank=True)
    timezone = models.CharField(max_length=50, default='UTC', blank=True)

    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


# =========================
#         SKILLS
# =========================
class Skill(models.Model):
    LEVEL_CHOICES = [
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
        ("Expert", "Expert"),
    ]

    user = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="skills"
    )
    name = models.CharField(max_length=255)
    level = models.CharField(
        max_length=50,
        choices=LEVEL_CHOICES,
        default="Beginner"
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.level})"


# =========================
#         JOBS
# =========================
class Job(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ('FULLTIME', 'Full time'),
        ('PARTTIME', 'Part-time'),
        ('INTERN', 'Internship'),
        ('CONTRACT', 'Project / Contract'),
    ]
    
    WORKING_SCHEDULE_CHOICES = [
        ('full_day', 'Full day'),
        ('flexible', 'Flexible schedule'),
        ('shift', 'Shift work'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField()
    location = models.CharField(max_length=100)
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        blank=True,
        null=True
    )
    working_schedule = models.CharField(
        max_length=20,
        choices=WORKING_SCHEDULE_CHOICES,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    skills = models.ManyToManyField('SkillTag', blank=True, related_name='jobs')
    
    # Tags/skills required for the job
    # Defined below; declared here for type reference
    # skills = models.ManyToManyField('SkillTag', blank=True, related_name='jobs')

    def __str__(self):
        return self.title


class SkillTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# =========================
#     JOB APPLICATIONS
# =========================
class JobApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    resume = models.FileField(upload_to="resumes/")
    cover_letter = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Interview', 'Interview'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    # Interview scheduling details (optional)
    interview_scheduled_at = models.DateTimeField(blank=True, null=True)
    interview_location = models.CharField(max_length=255, blank=True, null=True)
    interview_meeting_url = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} → {self.job.title}"


# =========================
#      NOTIFICATIONS
# =========================
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('job_application', 'Job Application'),
        ('job_post', 'New Job Post'),
        ('message', 'New Message'),
        ('profile_view', 'Profile View'),
        ('post_like', 'Post Like'),
        ('connection', 'New Connection'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='system')
    title = models.CharField(max_length=255, default='Notification')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=500, blank=True, null=True)
    related_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_from', blank=True, null=True)

    def __str__(self):
        return f"Notification for {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']


# =========================
#         MESSAGES
# =========================
class Message(models.Model):
    sender = models.ForeignKey(
        User,
        related_name="sent_messages",
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User,
        related_name="received_messages",
        on_delete=models.CASCADE
    )
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} → {self.receiver}"


# =========================
#   CONTACT SUBMISSION
# =========================
class ContactSubmission(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"


class Post(models.Model):
    POST_TYPE_CHOICES = [
        ('text', 'Text Post'),
        ('photo', 'Photo Post'),
        ('video', 'Video Post'),
        ('article', 'Article'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='text')
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    video = models.FileField(upload_to='post_videos/', blank=True, null=True)
    article_title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

# =========================
#      SAVED JOBS
# =========================
class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"