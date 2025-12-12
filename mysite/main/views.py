from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from django.contrib.auth import update_session_auth_hash

from .forms import JobForm, SkillForm, UserForm, ProfileForm
from .models import Profile, Job, JobApplication, Notification, Skill

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ============================
# HOME PAGE
# ============================
@login_required
def home_page(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={"full_name": request.user.username}
    )

    # ======= REAL-TIME POPULAR JOBS =======
    url = "https://jsearch.p.rapidapi.com/search"
    params = {
        "query": "popular jobs",
        "page": "1",
        "num_pages": "1"
    }

    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "jsearch-api.p.rapidapi.com"   # FIXED
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        popular_jobs = data.get("data", [])
    except:
        popular_jobs = []  # fail-safe

    # ======= OTHER DATA =======
    recommended_users = User.objects.exclude(id=request.user.id)[:5]
    applications_count = JobApplication.objects.filter(user=request.user).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    industries = ["Hotel Jobs", "Fast Food", "Management", "Retail"]

    context = {
        "profile": profile,
        "popular_jobs": popular_jobs,
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


# ============================
# LOGIN
# ============================
def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not User.objects.filter(username=email).exists():
            messages.error(request, "Account does not exist. Please register first.")
            return render(request, "main/login.html")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("homepage")
        else:
            messages.error(request, "Incorrect password.")

    return render(request, "main/login.html")


# ============================
# SIGNUP
# ============================
def signup_page(request):
    if request.method == "POST":
        first = request.POST.get("first_name")
        last = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Account already exists.")
            return render(request, "main/signup.html")

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first,
            last_name=last,
            password=password
        )
        login(request, user)
        return redirect("login")

    return render(request, "main/signup.html")


# ============================
# PROFILE PAGE
# ============================
@login_required
def profile_page(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, "main/profile.html", {"profile": profile})


# ============================
# MESSAGES PAGE
# ============================
def _messages(request):
    return render(request, "main/messages.html")


# ============================
# NOTIFICATIONS
# ============================
@login_required
def notifications_page(request):
    sample_notifications = {
        request.user.username: [
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
        ]
    }

    notifications = sample_notifications.get(request.user.username, [])

    return render(request, "main/notifications.html", {
        "notifications": notifications
    })


def mark_all_as_read(request):
    return redirect("notifications")


# ============================
# FIND JOBS (API SEARCH)
# ============================
def find_jobs(request):
    query = request.GET.get("q", "developer")

    url = "https://jsearch.p.rapidapi.com/search"
    params = {
        "query": query,
        "page": "1",
        "num_pages": "1"
    }

    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "jsearch-api.p.rapidapi.com"  # FIXED
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        jobs = data.get("data", [])
    except:
        jobs = []

    return render(request, "main/find_jobs.html", {
        "jobs": jobs,
        "query": query,
    })


# ============================
# EDIT PROFILE PAGE
# ============================
@login_required
def edit_profile_page(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("profile")
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(request, "main/edit_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })


# ============================
# SKILLS PAGE
# ============================
@login_required
def skills_page(request):
    profile = request.user.profile
    skills = Skill.objects.filter(user=profile)
    form = SkillForm()

    return render(request, "main/skills.html", {
        "skills": skills,
        "form": form,
    })


@login_required
def edit_skill(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id, user=request.user.profile)
    form = SkillForm(instance=skill)

    if request.method == "POST":
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            return redirect("skills")

    return render(request, "main/edit_skill.html", {"form": form})


@login_required
def delete_skill(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id, user=request.user.profile)
    skill.delete()
    return redirect("skills")


# ============================
# LOCATION PAGE
# ============================
def location(request):
    return render(request, "main/add_location.html")



def job_applications_page(request):
    return render(request, "main/job_applications.html")
