from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import UserForm, ProfileForm
from .models import Skill
from .forms import SkillForm
from .models import Profile
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Profile, Job, JobApplication, Notification

# =========================
#   MASTER LIST OF SKILLS
# =========================
IT_SKILLS = [
    "HTML",
    "CSS",
    "JavaScript",
    "Python",
    "Django",
    "SQL",
    "React",
    "Node.js",
    "Tailwind CSS",
    "Bootstrap",
    "Java",
    "C#",
    "C++",
    "PHP",
    "Laravel",
    "Figma",
    "UI/UX",
]

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

    # ---------- HANDLE REMOVE SINGLE SKILL (fallback) ----------
    if request.method == "POST" and request.POST.get("remove_skill"):
        skill_id = request.POST.get("remove_skill")
        Skill.objects.filter(id=skill_id, profile=profile).delete()
        messages.success(request, "Skill removed.")
        return redirect("edit_profile")

    # ---------- HANDLE GENERAL PROFILE INFO SAVE ----------
    if request.method == "POST" and request.POST.get("save_profile"):
        profile.full_name = request.POST.get("full_name", profile.full_name)
        profile.bio = request.POST.get("bio", profile.bio)
        profile.company_name = request.POST.get("company_name", profile.company_name)
        profile.role = request.POST.get("role", profile.role)

        # image handling
        if "image" in request.FILES:
            profile.image = request.FILES["image"]
        if request.POST.get("delete_image"):
            profile.image = None

        profile.save()
        messages.success(request, "Profile saved.")
        return redirect("edit_profile")

    # ---------- HANDLE CHANGE PASSWORD ----------
    if request.method == "POST" and request.POST.get("change_password"):
        old = request.POST.get("old_password")
        new = request.POST.get("new_password")
        if request.user.check_password(old) and len(new or "") >= 6:
            request.user.set_password(new)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password changed.")
            return redirect("edit_profile")
        else:
            messages.error(request, "Password change failed. Check your old password and new password length.")

    # render
    context = {
        "profile": profile,
        "skills": profile.skills.all().order_by("name"),
        "all_skills_list": IT_SKILLS,
    }
    return render(request, "main/edit_profile.html", context)
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
@login_required
def profile_page(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, "main/profile.html", {"profile": profile})

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
def job_applications_page(request, job_id):
    job = Job.objects.get(id=job_id)
    return render(request, "main/job_applications.html", {"job": job})


def location(request):
    return render(request, "main/add_location.html")
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile, Skill


@login_required
def edit_profile_page(request):
    profile = request.user.profile

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("profile")

    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, "main/edit_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "profile": profile,
    })