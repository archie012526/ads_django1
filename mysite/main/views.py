from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import UserForm, ProfileForm
from .models import Profile
from django.contrib import messages

from django.contrib.auth.models import User

from .models import Profile, Job, JobApplication, Notification



# ============================
# HOME PAGE
# ============================
@login_required
def home_page(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={"full_name": request.user.username}
    )

    jobs = Job.objects.all().order_by('-posted_at')[:10]
    recommended_users = User.objects.exclude(id=request.user.id)[:5]

    applications_count = JobApplication.objects.filter(user=request.user).count()
    unread_notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).count()

    industries = ["Hotel Jobs", "Fast Food", "Management", "Retail"]

    context = {
        "profile": profile,
        "jobs": jobs,
        "recommended_users": recommended_users,
        "applications_count": applications_count,
        "unread_notifications": unread_notifications,
        "saved_jobs_count": 0,
        "industries": industries,
    }

    return render(request, "main/home.html", context)



# ============================
# STATIC PAGES
# ============================
def landingpage(request):
    return render(request, "main/landing.html")

def about_page(request):
    return render(request, "main/about.html")

def find_job_page(request):
    return render(request, "main/find_job.html")

def contact_us_page(request):
    return render(request, "main/contact_us.html")

@login_required
def edit_profile_page(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("profile")   # redirect to profile page
        
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, "main/edit_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "profile": profile,
    })

# ============================
# AUTH: LOGIN
# ============================
def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if email exists
        if not User.objects.filter(username=email).exists():
            messages.error(request, "Account does not exist. Please register first.")
            return render(request, "main/login.html")

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("homepage")  
        else:
            messages.error(request, "Incorrect password.")

    return render(request, "main/login.html")


# ============================
# AUTH: SIGNUP
# ============================
def signup_page(request):
    if request.method == "POST":
        first = request.POST.get("first_name")
        last = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if user exists
        if User.objects.filter(username=email).exists():
            messages.error(request, "Account already exists. Please log in instead.")
            return render(request, "main/signup.html")

        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first,
            last_name=last,
            password=password
        )
        user.save()

        login(request, user)
        return redirect("login")

    return render(request, "main/signup.html")


# ============================
# PROFILE
# ============================
def profile_page(request):
    skills = ["Python", "Django", "HTML", "CSS"]

    job_database = [
        {"title": "Junior Django Developer", "skill": "Django"},
        {"title": "Frontend Intern", "skill": "HTML"},
        {"title": "Backend Developer", "skill": "Python"},
        {"title": "Web Designer", "skill": "CSS"},
        {"title": "Full Stack Developer", "skill": "Python"},
    ]

    suggestions = [job for job in job_database if job["skill"] in skills]

    return render(request, "main/profile.html", {
        "skills": skills,
        "job_suggestions": suggestions,
    })


# ============================
# MESSAGES
# ============================
def _messages(request):
    return render(request, "main/messages.html")


# ============================
# NOTIFICATIONS
# ============================
@login_required
def notifications_page(request):
    sample_notifications = {
        "user1": [
            {
                "title": "New Job Recommendation",
                "description": "3 new jobs match your skills.",
                "type": "Job",
                "time": "10 minutes ago",
                "status": "unread",
                "color": "blue",
            },
            {
                "title": "Profile View",
                "description": "An employer viewed your profile.",
                "type": "Profile",
                "time": "1 hour ago",
                "status": "read",
                "color": "green",
            },
        ],
        "user2": [
            {
                "title": "New Message",
                "description": "You received a new message.",
                "type": "Message",
                "time": "5 minutes ago",
                "status": "unread",
                "color": "purple",
            }
        ]
    }

    username = request.user.username
    notifications = sample_notifications.get(username, [])

    return render(request, "main/notifications.html", {
        "notifications": notifications
    })


def mark_all_as_read(request):
    return redirect("notifications")


# ============================
# JOB APPLICATION PAGE
# ============================
def job_applications_page(request):
    return render(request, "main/job_applications.html")
