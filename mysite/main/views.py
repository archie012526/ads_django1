from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Post

from .models import Profile, Job, JobApplication, Notification, Skill, Message
from .forms import JobForm, PostForm, SkillForm, UserForm, ProfileForm, SettingsForm, SignUpForm


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
        username_or_email = request.POST.get("username_or_email", "").strip()
        password = request.POST.get("password", "")

        user = None
        
        # Try to authenticate with username first
        user = authenticate(request, username=username_or_email, password=password)
        
        # If that fails and input looks like email, try email lookup
        if user is None and "@" in username_or_email:
            try:
                # Case-insensitive email lookup
                user_obj = User.objects.get(email__iexact=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            return redirect("homepage")
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, "main/login.html")


def signup_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        username = request.POST.get("username", "").strip() or email
        password = request.POST.get("password", "") or request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")

        # Validate passwords match
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "main/signup.html")

        # Validate password is not empty
        if not password:
            messages.error(request, "Password is required.")
            return render(request, "main/signup.html")

        try:
            User.objects.create_user(
                username=username,
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

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.userprofile.phone_number = form.cleaned_data["phone_number"]
            user.userprofile.save()
            return redirect("login")
    else:
        form = SignUpForm()

    return render(request, "main/signup.html", {"form": form})

# ============================
# HOME
# ============================
@login_required
def homepage(request):
    import random
    
    profile = request.user.profile
    my_jobs = Job.objects.filter(user=request.user).order_by('-created_at')
    
    # Combine posts and job posts from others (non-admin, non-self) for mixed feed
    posts_from_others = list(Post.objects.exclude(user=request.user).select_related('user', 'user__profile').order_by('-created_at')[:20])
    jobs_from_others = list(
        Job.objects
        .exclude(user=request.user)
        .filter(user__is_staff=False)
        .order_by('-created_at')[:20]
    )
    
    # Tag each with a type for template rendering
    for p in posts_from_others:
        p.item_type = 'post'
    for j in jobs_from_others:
        j.item_type = 'job'
    
    # Combine and shuffle for natural mixed feed
    mixed_feed = posts_from_others + jobs_from_others
    random.shuffle(mixed_feed)
    
    # Keep separate references for backward compatibility
    posts = Post.objects.select_related('user', 'user__profile').order_by('-created_at')
    other_jobs = jobs_from_others[:10]

    # ========= Personalized Recommendations =========
    base_jobs = Job.objects.filter(user__is_staff=False).exclude(user=request.user)

    # Skills-based
    user_skills = list(profile.skills.values_list('name', flat=True))
    rec_by_skills = []
    if user_skills:
        for job in base_jobs[:200]:
            text = f"{job.title} {job.description}"
            match_count = sum(1 for s in user_skills if s.lower() in text.lower())
            if match_count > 0:
                rec_by_skills.append({"job": job, "match_count": match_count})
        rec_by_skills.sort(key=lambda x: x["match_count"], reverse=True)
        rec_by_skills = rec_by_skills[:5]

    # Titles/roles based on preferred_job_titles
    rec_by_titles = []
    if profile.preferred_job_titles:
        titles = [t.strip() for t in profile.preferred_job_titles.split(',') if t.strip()]
        if titles:
            q = Q()
            for t in titles:
                q |= Q(title__icontains=t)
            rec_by_titles = list(base_jobs.filter(q)[:5])

    # Location-based (remote/hybrid/nearby approximation)
    rec_by_location = []
    pref_loc = profile.preferred_location or profile.location
    if pref_loc:
        rec_by_location = list(base_jobs.filter(Q(location__icontains=pref_loc) | Q(location__icontains="remote"))[:5])

    # Recently posted (last 3 days)
    recent_cutoff = timezone.now() - timedelta(days=3)
    rec_recent = list(base_jobs.filter(created_at__gte=recent_cutoff)[:5])

    # Similar to applied
    applied_ids = list(JobApplication.objects.filter(user=request.user).values_list('job_id', flat=True).distinct())
    rec_similar_applied = []
    if applied_ids:
        applied_titles = list(Job.objects.filter(id__in=applied_ids).values_list('title', flat=True))
        if applied_titles:
            q = Q()
            for t in applied_titles:
                # Use first keyword chunk to broaden match
                key = t.split()[0] if t.split() else t
                if key:
                    q |= Q(title__icontains=key)
            rec_similar_applied = list(base_jobs.exclude(id__in=applied_ids).filter(q)[:5])

    # Company-based (companies user applied to)
    rec_companies = []
    if applied_ids:
        companies = list(Job.objects.filter(id__in=applied_ids).values_list('company_name', flat=True))
        companies = [c for c in companies if c]
        if companies:
            rec_companies = list(base_jobs.filter(company_name__in=companies)[:5])

    if request.method == "POST":
        post_type = request.POST.get("post_type", "post")
        
        if post_type == "job":
            # Create a job post
            title = request.POST.get("job_title")
            company = request.POST.get("job_company")
            description = request.POST.get("job_description")
            location = request.POST.get("job_location")
            employment_type = request.POST.get("job_employment_type")
            working_schedule = request.POST.get("job_working_schedule")
            
            if title and description and location:
                Job.objects.create(
                    user=request.user,
                    title=title,
                    company_name=company,
                    description=description,
                    location=location,
                    employment_type=employment_type if employment_type else None,
                    working_schedule=working_schedule if working_schedule else None
                )
                messages.success(request, "Job posted successfully!")
                return redirect('homepage')
        else:
            # Create a regular post
            form = PostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.save()
                messages.success(request, "Post created successfully!")
                return redirect('homepage')
    else:
        form = PostForm()

    # Basic counts and defaults for sidebar cards
    saved_jobs_count = 0
    applications_count = JobApplication.objects.filter(user=request.user).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    # Simple recommended users list (exclude self)
    recommended_users = User.objects.exclude(id=request.user.id)[:5]

    # Stub data for industries and popular_jobs if not provided elsewhere
    industries = []
    popular_jobs = []

    context = {
        'form': form,
        'posts': posts,
        'profile': profile,
        'my_jobs': my_jobs,
        'other_jobs': other_jobs,
        'mixed_feed': mixed_feed,  # New mixed feed for natural ordering
        # Personalized recs
        'rec_by_skills': rec_by_skills,
        'rec_by_titles': rec_by_titles,
        'rec_by_location': rec_by_location,
        'rec_recent': rec_recent,
        'rec_similar_applied': rec_similar_applied,
        'rec_companies': rec_companies,
        'saved_jobs_count': saved_jobs_count,
        'applications_count': applications_count,
        'unread_notifications': unread_notifications,
        'recommended_users': recommended_users,
        'industries': industries,
        'popular_jobs': popular_jobs,
    }
    return render(request, 'main/home.html', context)

# ============================
# PROFILE
# ============================
@login_required
def profile_page(request):
    profile = request.user.profile
    user_skill_names = list(profile.skills.values_list("name", flat=True))

    suggestions = []

    if user_skill_names:
        base = [s.lower() for s in user_skill_names]

        q = Q()
        for s in user_skill_names:
            q |= Q(title__icontains=s) | Q(description__icontains=s) | Q(skills__name__iexact=s)

        jobs_qs = (
            Job.objects
            .filter(q)
            .exclude(user=request.user)
            .distinct()
        )

        for job in jobs_qs:
            text = f"{job.title} {(job.description or '')}"
            matched_from_text = {s for s in base if s in text.lower()}
            matched_from_tags = set(
                name.lower() for name in job.skills.filter(name__in=user_skill_names).values_list("name", flat=True)
            )
            matched = matched_from_text.union(matched_from_tags)
            match_percent = int(round((len(matched) / max(1, len(base))) * 100))

            suggestions.append({
                "job": job,
                "match_percent": match_percent,
                "matched_skills": sorted(list(matched)),
            })

        # Sort by highest match
        suggestions.sort(key=lambda x: x["match_percent"], reverse=True)
        suggestions = suggestions[:10]

    return render(request, "main/profile.html", {
        "profile": profile,
        "suggestions": suggestions,
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
    employment_type = request.GET.get("employment_type", "")
    working_schedule = request.GET.get("job_requirements", "")
    skill = request.GET.get("skill", "")
    
    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(company_name__icontains=query)
        )
    
    if employment_type:
        jobs = jobs.filter(employment_type=employment_type)
    
    if working_schedule:
        jobs = jobs.filter(working_schedule=working_schedule)

    if skill:
        jobs = jobs.filter(skills__name__iexact=skill).distinct()

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
# CREATE/POST JOB
# ============================
@login_required
def create_job(request):
    # Only admins and employers can create jobs
    if not (request.user.is_staff or request.user.profile.role == "employer"):
        messages.error(request, "You don't have permission to create jobs.")
        return redirect("homepage")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            messages.success(request, "Job created successfully!")
            return redirect("find_job")
    else:
        form = JobForm()

    return render(request, "main/create_job.html", {"form": form})


@login_required
def edit_job(request, job_id: int):
    job = get_object_or_404(Job, id=job_id, user=request.user)
    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            messages.success(request, "Job updated successfully!")
            return redirect("homepage")
    else:
        form = JobForm(instance=job)
    return render(request, "main/create_job.html", {"form": form, "editing": True})


@login_required
def delete_job(request, job_id: int):
    job = get_object_or_404(Job, id=job_id, user=request.user)
    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted.")
        return redirect("homepage")
    return redirect("homepage")


@login_required
def post_job(request):
    # Redirect to create_job view
    return create_job(request)


# Legacy view kept for compatibility
@login_required
def post_job_old(request):
    if request.user.profile.role != "employer":
        return redirect("homepage")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
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

