# removed accidental mailbox.Message import which shadowed our model
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.mail import send_mail
import requests
from django.conf import settings
from django.shortcuts import render
from django.core.cache import cache
import logging
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q


from django.contrib.auth import update_session_auth_hash

from .forms import JobForm, SkillForm, UserForm, ProfileForm
from .models import Profile, Job, JobApplication, Notification, Skill, Message

import requests
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

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
@login_required
def messages_inbox(request):
    # find recent conversations (ordered by last message)
    msgs = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by('-sent_at')

    partners = []
    seen = set()
    for m in msgs:
        other = m.receiver if m.sender == request.user else m.sender
        if other.id in seen:
            continue
        seen.add(other.id)
        # unread count for this conversation
        unread_count = Message.objects.filter(sender=other, receiver=request.user, is_read=False).count()
        # safe avatar and display name
        profile = getattr(other, 'profile', None)
        avatar = None
        if profile and getattr(profile, 'profile_image'):
            avatar = profile.profile_image.url

        display_name = other.get_full_name() or other.username

        partners.append({
            'user': other,
            'last_message': m,
            'unread_count': unread_count,
            'avatar_url': avatar,
            'display_name': display_name,
        })

    return render(request, "main/messages.html", {
        'conversations': partners,
    })


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
    profile = request.user

    skills = Skill.objects.filter(user=request.user)

    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.user = request.user
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

def broadcast_popular_jobs(jobs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "popular_jobs",
        {
            "type": "jobs.update",
            "jobs": jobs
        }
    )

def fetch_popular_jobs_from_rapidapi(query="popular jobs", num_pages=1):
    """
    Calls JSearch (RapidAPI) and returns a list of normalized job dicts.
    Caches results at the view level (see caller).
    """
    if not settings.RAPIDAPI_KEY:
        logger.warning("RAPIDAPI_KEY not set in settings")
        return []

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": settings.RAPIDAPI_HOST,
    }
    params = {
        "query": query,
        "num_pages": num_pages
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.exception("Error fetching jobs from RapidAPI: %s", e)
        return []

    results = []
    for item in data.get("data", []):
        # Map fields from the API to the structure your template expects
        results.append({
            "job_title": item.get("job_title") or item.get("title") or "",
            "employer_name": item.get("employer_name") or item.get("company_name") or "",
            "job_city": item.get("job_city") or item.get("location") or "",
            "job_country": item.get("job_country") or "",
            "job_min_salary": item.get("min_salary") or item.get("salary") or "",
            "job_max_salary": item.get("max_salary") or "",
            "job_apply_link": item.get("job_apply_link") or item.get("url") or "#",
        })

    return results

def find_job(request):
    """
    Main view that serves your popular jobs page.
    - Accepts optional ?q= search query from your template search input.
    - Caches the API response for POPULAR_JOBS_CACHE_TIMEOUT seconds.
    """
    query = request.GET.get("q") or "popular jobs"
    cache_key = f"popular_jobs::{query}"

    jobs = cache.get(cache_key)
    if jobs is None:
        # fetch from RapidAPI
        jobs = fetch_popular_jobs_from_rapidapi(query=query, num_pages=1)
        # cache results (avoid exceeding RapidAPI rate limits)
        cache.set(cache_key, jobs, getattr(settings, "POPULAR_JOBS_CACHE_TIMEOUT", 300))

    # Render your existing template (adjust template name if different)
    return render(request, "main/find_job.html", {"jobs": jobs, "query": query})

def contact_email(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        full_message = f"""
From: {name}
Email: {email}

Message:
{message}
"""

        send_mail(
            subject,
            full_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )

        messages.success(request, "Your message has been sent successfully!")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    return redirect("/")
