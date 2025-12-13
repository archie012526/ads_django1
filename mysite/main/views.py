from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .forms import JobForm, SkillForm, UserForm, ProfileForm
from .models import Profile, Job, JobApplication, Notification, Skill, Message

import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# ============================
# LANDING / STATIC
# ============================
def landingpage(request):
    return render(request, "main/landing.html")


def about_page(request):
    return render(request, "main/about.html")


def contact_us_page(request):
    return render(request, "main/contact_us.html")


# ============================
# AUTH
# ============================
def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not User.objects.filter(username=email).exists():
            messages.error(request, "Account does not exist.")
            return render(request, "main/login.html")

        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect("homepage")

        messages.error(request, "Incorrect password.")

    return render(request, "main/login.html")


def signup_page(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Account already exists.")
            return render(request, "main/signup.html")

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            password=request.POST.get("password"),
        )
        login(request, user)
        return redirect("login")

    return render(request, "main/signup.html")


# ============================
# HOME
# ============================
@login_required
def home_page(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={"full_name": request.user.username}
    )

    url = "https://jsearch.p.rapidapi.com/search"
    params = {"query": "popular jobs", "page": "1", "num_pages": "1"}
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        popular_jobs = response.json().get("data", [])
    except Exception as e:
        logger.error("RapidAPI error: %s", e)
        popular_jobs = []

    return render(request, "main/home.html", {
        "profile": profile,
        "popular_jobs": popular_jobs,
        "applications_count": JobApplication.objects.filter(user=request.user).count(),
        "unread_notifications": Notification.objects.filter(
            user=request.user, is_read=False
        ).count(),
    })


# ============================
# PROFILE
# ============================
@login_required
def profile_page(request):
    return render(request, "main/profile.html", {
        "profile": request.user.profile
    })


@login_required
def edit_profile_page(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(request, "main/edit_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })


# ============================
# FIND JOBS
# ============================
def fetch_popular_jobs_from_rapidapi(query="popular jobs"):
    if not os.getenv("RAPIDAPI_KEY"):
        return []

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    try:
        resp = requests.get(url, headers=headers, params={"query": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception as e:
        logger.error("RapidAPI error: %s", e)
        return []

    return data


def find_job(request):
    query = request.GET.get("q") or "popular jobs"
    cache_key = f"jobs::{query}"

    jobs = cache.get(cache_key)
    if jobs is None:
        jobs = fetch_popular_jobs_from_rapidapi(query)
        cache.set(cache_key, jobs, 300)

    return render(request, "main/find_job.html", {
        "jobs": jobs,
        "query": query,
    })


# ============================
# JOB APPLICATIONS
# ============================
@login_required
def job_applications_page(request):
    applications = JobApplication.objects.filter(user=request.user)
    return render(request, "main/job_applications.html", {
        "applications": applications
    })


# ============================
# SKILLS
# ============================
@login_required
def skills_page(request):
    skills = Skill.objects.filter(user=request.user.profile)
    form = SkillForm()
    return render(request, "main/skills.html", {
        "skills": skills,
        "form": form,
    })


@login_required
def edit_skill(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id, user=request.user.profile)

    if request.method == "POST":
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            return redirect("skills")
    else:
        form = SkillForm(instance=skill)

    return render(request, "main/edit_skill.html", {"form": form})


@login_required
def delete_skill(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id, user=request.user.profile)
    skill.delete()
    return redirect("skills")


# ============================
# MESSAGES
# ============================
@login_required
def messages_inbox(request):
    msgs = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by("-sent_at")

    conversations = {}
    for m in msgs:
        other = m.receiver if m.sender == request.user else m.sender
        conversations.setdefault(other, m)

    return render(request, "main/messages.html", {
        "conversations": conversations.values()
    })


@login_required
def conversation_view(request, user_id):
    other = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        content = request.POST.get("message")
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other,
                content=content
            )
        return redirect("conversation", user_id=user_id)

    convo = Message.objects.filter(
        Q(sender=request.user, receiver=other) |
        Q(sender=other, receiver=request.user)
    ).order_by("sent_at")

    Message.objects.filter(
        sender=other, receiver=request.user, is_read=False
    ).update(is_read=True)

    return render(request, "main/messages.html", {
        "conversation_user": other,
        "messages_qs": convo,
    })


# ============================
# NOTIFICATIONS
# ============================
@login_required
def notifications_page(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-id")
    return render(request, "main/notifications.html", {
        "notifications": notifications
    })


@login_required
def mark_all_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("notifications")


# ============================
# LOCATION
# ============================
@login_required
def location(request):
    return render(request, "main/add_location.html")


# ============================
# CONTACT EMAIL
# ============================
def contact_email(request):
    if request.method == "POST":
        send_mail(
            request.POST.get("subject"),
            request.POST.get("message"),
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],
        )
        messages.success(request, "Message sent!")
    return redirect("/")

def settings_page(request):
    # Replace 'settings.html' with the template you want to use
    return render(request, 'main/settings.html')