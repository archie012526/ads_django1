from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .forms import JobForm, SkillForm, UserForm, ProfileForm, SettingsForm
from .models import Profile, Job, JobApplication, Notification, Skill, Message

import requests
import logging
import os
from dotenv import load_dotenv

from django.db import models
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

        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect("homepage")

        messages.error(request, "Invalid email or password.")

    return render(request, "main/login.html")


def signup_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")

        try:
            User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
        except IntegrityError:
            messages.error(request, "Email already registered.")
            return render(request, "main/signup.html")

        messages.success(request, "Account created successfully. Please log in.")
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
def conversation_view(request, user_id):
    other = get_object_or_404(User, id=user_id)

    # POST -> send message
    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            Message.objects.create(sender=request.user, receiver=other, content=content)
        return redirect('conversation', user_id=other.id)

    # fetch conversation messages
    convo = Message.objects.filter(
        Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user)
    ).order_by('sent_at')

    # mark incoming messages as read
    Message.objects.filter(sender=other, receiver=request.user, is_read=False).update(is_read=True)

    # conversation user safe fields
    conv_profile = getattr(other, 'profile', None)
    conv_avatar = None
    if conv_profile and getattr(conv_profile, 'profile_image'):
        conv_avatar = conv_profile.profile_image.url

    return render(request, "main/messages.html", {
        'conversation_user': other,
        'conversation_user_avatar': conv_avatar,
        'conversation_user_display': other.get_full_name() or other.username,
        'messages_qs': convo,
        'conversations': [],
    })

@login_required
def profile_page(request):
    profile = request.user.profile
    skills = profile.skills.all()

    suggested_jobs = []

    if skills.exists():
        skill_names = [s.name.lower() for s in skills]

        # Use FIRST skill for search (more reliable)
        query = skill_names[0]

        jobs = fetch_popular_jobs_from_rapidapi(query)

        for job in jobs:
            text_blob = " ".join([
                job.get("job_title", ""),
                job.get("employer_name", ""),
                str(job.get("job_highlights", "")),
                str(job.get("job_description", "")),
            ]).lower()

            matched_skills = [
                skill for skill in skill_names if skill in text_blob
            ]

            match_percent = int(
                (len(matched_skills) / len(skill_names)) * 100
            )

            job["match_percent"] = match_percent
            job["matched_skills"] = matched_skills

            suggested_jobs.append(job)

    return render(request, "main/profile.html", {
        "profile": profile,
        "suggested_jobs": suggested_jobs,
    })




def fetch_jobs_by_skills(skill_names):
    if not os.getenv("RAPIDAPI_KEY"):
        return []

    query = " ".join(skill_names[:3])  # use top skills
    url = "https://jsearch.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    params = {
        "query": query,
        "page": "1",
        "num_pages": "1",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        logger.error("Job fetch error: %s", e)
        return []


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
# FIND JOBS (SEARCH + CACHE)
# ============================
def find_job(request):
    query = request.GET.get("q") or "developer"
    cache_key = f"jobs::{query}"

    jobs = cache.get(cache_key)
    if jobs is None:
        url = "https://jsearch.p.rapidapi.com/search"

        headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

        params = {
            "query": query,
            "page": "1",
            "num_pages": "1",
        }

        jobs = []

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for job in data.get("data", []):
                highlights = (
                    job.get("job_highlights")
                    or job.get("job_skills")
                    or []
                )

                if isinstance(highlights, str):
                    highlights = [highlights]

                jobs.append({
                    "job_title": job.get("job_title"),
                    "employer_name": job.get("employer_name"),
                    "job_city": job.get("job_city"),
                    "job_country": job.get("job_country"),
                    "job_apply_link": job.get("job_apply_link"),
                    "job_min_salary": job.get("job_min_salary"),
                    "job_max_salary": job.get("job_max_salary"),
                    "job_highlights": highlights,
                    "job_employment_type": job.get("job_employment_type"),
                })

        except Exception as e:
            print("Job API error:", e)

        cache.set(cache_key, jobs, 300)

    return render(request, "main/find_job.html", {
        "jobs": jobs,
        "query": query,
    })

# ============================
# EDIT PROFILE PAGE
# ============================
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
def job_search(request):
    query = request.GET.get("q", "")

    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(
            title__icontains=query
            | models.Q(company__icontains=query)
            | models.Q(location__icontains=query)
        )

    context = {
        "jobs": jobs,
        "query": query,
    }

    return render(request, "main/job_search.html", context)


# ============================
# SKILLS
# ============================
@login_required
def skills_page(request):
    skills = Skill.objects.filter(user=request.user.profile)

    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.user = request.user.profile   # ✅ PROFILE
            skill.save()
            return redirect("skills")
    else:
        form = SkillForm()

    return render(request, "main/skills.html", {
        "skills": skills,
        "form": form,
    })


@login_required
def edit_skill(request, skill_id):
    skill = get_object_or_404(
        Skill,
        id=skill_id,
        user=request.user.profile   # ✅ PROFILE
    )

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
    skill = get_object_or_404(
        Skill,
        id=skill_id,
        user=request.user.profile   # ✅ PROFILE INSTANCE
    )

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

@login_required
def settings_page(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = SettingsForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated.')
            return redirect('settings')
    else:
        form = SettingsForm(instance=profile)

    return render(request, 'main/settings.html', {
        'form': form,
    })

@login_required
def post_job(request):
    # Allow ONLY employers
    if request.user.profile.role != "employer":
        return redirect("home")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            job.save()
            return redirect("dashboard")
    else:
        form = JobForm()

    return render(request, "main/post_job.html", {
        "form": form
    })


def data_control(request):
    return render(request, 'main/data-control2.html')

def help_page(request):
    return render(request, 'main/help2.html')

def language(request):
    return render(request, 'main/language2.html')

@login_required
def privacy(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = SettingsForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Privacy settings updated.')
            return redirect('settings_privacy')
    else:
        form = SettingsForm(instance=profile)

    return render(request, 'main/privacy2.html', {
        'form': form,
    })

def security(request):
    # Keep simple rendering for now; security actions (logout all etc.) can be handled here
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'logout_all':
            # Implement logout-all logic if desired (requires session tracking)
            messages.success(request, 'All sessions logged out (simulated).')
            return redirect('settings_security')
    return render(request, 'main/security.html')


@login_required
def account_settings(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        settings_form = SettingsForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and settings_form.is_valid():
            user_form.save()
            settings_form.save()
            messages.success(request, 'Account settings updated.')
            return redirect('settings_account')
    else:
        user_form = UserForm(instance=user)
        settings_form = SettingsForm(instance=profile)

    return render(request, 'main/account.html', {
        'user_form': user_form,
        'form': settings_form,
    })