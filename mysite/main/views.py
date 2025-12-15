from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail

from .models import Profile, Job, JobApplication, Notification, Skill, Message
from .forms import JobForm, SkillForm, UserForm, ProfileForm, SettingsForm


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

        messages.success(request, "Account created successfully.")
        return redirect("login")

    return render(request, "main/signup.html")


# ============================
# HOME
# ============================
@login_required
def homepage(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    popular_jobs = Job.objects.order_by("-id")[:5]

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
    profile = request.user.profile
    skills = profile.skills.all()

    suggested_jobs = Job.objects.none()

    if skills.exists():
        q = Q()
        for skill in skills:
            q |= Q(description__icontains=skill.name)
        suggested_jobs = Job.objects.filter(q).distinct()

    return render(request, "main/profile.html", {
        "profile": profile,
        "suggested_jobs": suggested_jobs,
    })


@login_required
def edit_profile_page(request):
    profile = request.user.profile

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")

    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, "main/edit_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "profile": profile,
    })


# ============================
# FIND JOBS / SEARCH
# ============================
def find_job(request):
    query = request.GET.get("q", "")
    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )

    return render(request, "main/find_job.html", {
        "jobs": jobs,
        "query": query,
    })


def job_search(request):
    query = request.GET.get("q", "")
    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company__icontains=query) |
            Q(location__icontains=query)
        )

    return render(request, "main/job_search.html", {
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

    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.user = request.user.profile
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
        Skill, id=skill_id, user=request.user.profile
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
        Skill, id=skill_id, user=request.user.profile
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
    Notification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True)
    return redirect("notifications")


# ============================
# CONTACT EMAIL
# ============================
def contact_email(request):
    if request.method == "POST":
        send_mail(
            request.POST.get("subject"),
            request.POST.get("message"),
            settings.EMAIL_HOST_USER,
            [settings.EMAIL_HOST_USER],
        )
        messages.success(request, "Message sent!")
    return redirect("landing")


# ============================
# SETTINGS
# ============================
@login_required
def settings_page(request):
    profile = request.user.profile
    form = SettingsForm(instance=profile)
    return render(request, "main/settings.html", {"form": form})


@login_required
def account_settings(request):
    profile = request.user.profile

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        settings_form = SettingsForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and settings_form.is_valid():
            user_form.save()
            settings_form.save()
            messages.success(request, "Account updated.")
            return redirect("settings_account")

    else:
        user_form = UserForm(instance=request.user)
        settings_form = SettingsForm(instance=profile)

    return render(request, "main/account.html", {
        "user_form": user_form,
        "form": settings_form,
    })


def privacy(request):
    return render(request, "main/privacy2.html")


def security(request):
    return render(request, "main/security.html")


def language(request):
    return render(request, "main/language2.html")


def data_control(request):
    return render(request, "main/data-control2.html")


def help_page(request):
    return render(request, "main/help2.html")


# ============================
# POST JOB
# ============================
@login_required
def post_job(request):
    if request.user.profile.role != "employer":
        return redirect("homepage")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            job.save()
            return redirect("homepage")
    else:
        form = JobForm()

    return render(request, "main/post_job.html", {"form": form})

@login_required
def add_location(request):
    profile = request.user.profile
    
    if request.method == "POST":
        location = request.POST.get("location", "")
        profile.location = location
        profile.save()
        messages.success(request, "Location updated successfully!")
        return redirect("homepage")
    
    return render(request, "main/add_location.html", {
        "profile": profile,
    })

