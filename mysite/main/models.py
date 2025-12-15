from django.db import models
from django.contrib.auth.models import User


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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


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
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    def __str__(self):
        return f"{self.user.username} → {self.job.title}"


# =========================
#      NOTIFICATIONS
# =========================
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"


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
