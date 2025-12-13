from django.db import models
from django.contrib.auth.models import User


# =========================
#        PROFILE
# =========================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.ImageField(upload_to="profile_images/", blank=True, null=True)

    def __str__(self):
        return self.user.username

# =========================
#         JOBS
# =========================
class Job(models.Model):
    JOB_TYPES = [
        ("Full time", "Full time"),
        ("Part-time", "Part-time"),
        ("Internship", "Internship"),
        ("Project work", "Project work"),
        ("Volunteering", "Volunteering"),
    ]

    EMPLOYMENT_TYPES = [
        ("Full day", "Full day"),
        ("Flexible schedule", "Flexible schedule"),
        ("Shift work", "Shift work"),
    ]

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    job_type = models.CharField(
        max_length=50, 
        choices=JOB_TYPES,
        default="Full time"
    )

    employment_type = models.CharField(
        max_length=50, 
        choices=EMPLOYMENT_TYPES,
        default="Full day"
    )

    skills = models.CharField(
        max_length=255,
        default=""  # prevents migration errors
    )

    salary = models.CharField(max_length=50, default="Not specified")
    description = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# =========================
#     JOB APPLICATIONS
# =========================
class JobApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('Pending', 'Pending'),
            ('Reviewed', 'Reviewed'),
            ('Accepted', 'Accepted'),
            ('Rejected', 'Rejected'),
        ],
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
    sender = models.ForeignKey(User, related_name="sender", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="receiver", on_delete=models.CASCADE)
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

class Skill(models.Model):
    LEVEL_CHOICES = [
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    description = models.TextField(blank=True, null=True)  # ✅ FIX

    def __str__(self):
        return f"{self.name} attaching a level"
