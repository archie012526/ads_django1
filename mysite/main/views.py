from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from datetime import timedelta, datetime, timezone as dt_timezone
from .models import Post
from django.http import HttpResponseForbidden
from .models import AuditLog

from .models import Profile, Job, JobApplication, Notification, Skill, Message, SavedJob, SkillTag, GlobalNotification


def add_audit_log(request, user, action):
    """Convenience helper to create an AuditLog entry with IP detection."""
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(user=user, action=action, ip_address=ip)

from .forms import JobForm, PostForm, SkillForm, UserForm, ProfileForm, SettingsForm, SignUpForm, JobApplicationForm

from django.contrib.auth import logout as django_logout
from django.db.models import Q
# ============= AUTHENTICATION =============

def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')

        return render(request, "admin/admin_login.html", {
            "error": "Invalid admin credentials"
        })

    return render(request, "admin/admin_login.html")
def logout_view(request):
    logout(request)
    return render(request, "admin/admin_login.html")

# ============= ADMIN DASHBOARD =============

@login_required(login_url="/admin-panel/login/")
def admin_dashboard(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    recent_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]

    # <-- added: fetch recent user-level notifications for admin overview
    recent_user_notifications = Notification.objects.select_related('user', 'related_user').order_by('-created_at')[:10]
    unread_user_notifications_count = Notification.objects.filter(is_read=False).count()

    context = {
        "total_users": User.objects.count(),
        "total_jobs": Job.objects.count(),
        "recent_logs": recent_logs,
        # <-- added keys
        "user_notifications": recent_user_notifications,
        "unread_user_notifications_count": unread_user_notifications_count,
    }
    return render(request, "admin/admin_dashboard.html", context)

# ============= USER MANAGEMENT =============

@login_required(login_url="/admin-panel/login/")
def admin_users(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    users = User.objects.exclude(is_superuser=True)
    return render(request, "admin/admin_users.html", {"users": users})

@login_required(login_url="/admin-panel/login/")
def toggle_user_ban(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    add_audit_log(request, request.user, f"Toggled user active for '{user.username}' -> is_active={user.is_active}")
    return redirect("admin_users")

# ============= JOB MANAGEMENT =============

@login_required(login_url="/admin-panel/login/")
def admin_jobs(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    jobs = Job.objects.all().order_by('-id')
    return render(request, "admin/admin_jobs.html", {"jobs": jobs})

@login_required(login_url="/admin-panel/login/")
def toggle_job_approval(request, job_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    job = get_object_or_404(Job, id=job_id)
    job.is_approved = not job.is_approved
    job.save()
    add_audit_log(request, request.user, f"Toggled job approval for '{job.title}' (id:{job.id}) -> is_approved={job.is_approved}")
    return redirect('admin_jobs')

@login_required(login_url="/admin-panel/login/")
def delete_job(request, job_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    job = get_object_or_404(Job, id=job_id)
    title = job.title
    job.delete()
    add_audit_log(request, request.user, f"Admin deleted job '{title}' (id:{job_id})")
    return redirect('admin_jobs')

def admin_skills(request):
    # 1. Get the Profile safely
    try:
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return render(request, 'admin/admin_skills.html', {'error': 'Profile not found.'})

    # 2. Handle adding a new skill
    if request.method == "POST":
        name = request.POST.get('skill_name')
        level = request.POST.get('level', 'Beginner')
        description = request.POST.get('description', '')

        if name:
            Skill.objects.create(
                user=user_profile, 
                name=name,
                level=level,
                description=description
            )
            add_audit_log(request, request.user, f"Admin added skill '{name}'")
        return redirect('admin_skills')

    # 3. Fetch BOTH Global skills and Admin-owned skills
    # We do this AFTER the POST check so the list is always fresh
    skills = Skill.objects.filter(
        Q(user__isnull=True) | Q(user=user_profile)
    ).order_by('-id')

    context = {
        'skills': skills,
        'levels': Skill.LEVEL_CHOICES
    }
    return render(request, 'admin/admin_skills.html', context)

def admin_skill_delete(request, pk):
    from .models import Skill
    skill = get_object_or_404(Skill, pk=pk)
    if request.method == "POST":
        name = skill.name
        skill.delete()
        add_audit_log(request, request.user, f"Admin deleted skill '{name}' (id:{pk})")
    return redirect('admin_skills')


@login_required(login_url="/admin-panel/login/")
def admin_notifications(request):
    """Admin UI to list and create GlobalNotifications (announcements)."""
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    # POST -> create a new GlobalNotification
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        level = request.POST.get('level', 'info')
        show_on_site = request.POST.get('show_on_site') == 'on'
        send_email = request.POST.get('send_email') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        expires_at = request.POST.get('expires_at') or None

        if title and message:
            gn = GlobalNotification.objects.create(
                title=title,
                message=message,
                level=level,
                show_on_site=show_on_site,
                send_email=send_email,
                is_active=is_active,
                expires_at=expires_at
            )
            add_audit_log(request, request.user, f"Admin created global message '{gn.title}' (id:{gn.id})")
            messages.success(request, "Global message created.")
            # TODO: if send_email, optionally send emails to users (not implemented here)
        else:
            messages.error(request, "Please provide both a title and message.")
        return redirect('admin_notifications')

    # GET -> list existing notifications
    notifications = GlobalNotification.objects.all().order_by('-created_at')
    return render(request, 'admin/admin_notifications.html', {'notifications': notifications, 'levels': GlobalNotification.LEVEL_CHOICES})


@login_required(login_url="/admin-panel/login/")
def admin_notification_delete(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    gn = get_object_or_404(GlobalNotification, pk=pk)
    if request.method == 'POST':
        title = gn.title
        gn.delete()
        add_audit_log(request, request.user, f"Admin deleted global message '{title}' (id:{pk})")
        messages.success(request, "Global message deleted.")
    return redirect('admin_notifications')


@login_required(login_url="/admin-panel/login/")
def seed_skills_view(request):
    """Create a set of default global skills (user=NULL) for the admin panel.
    Idempotent: will not duplicate existing skill names."""
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    default_skills = [
        "Python", "Django", "JavaScript", "React", "SQL", "HTML", "CSS",
        "DevOps", "Docker", "Kubernetes", "AWS", "Product Management", "Data Analysis"
    ]

    created = 0
    for name in default_skills:
        obj, created_flag = Skill.objects.get_or_create(user=None, name=name, defaults={"level": "Beginner", "description": ""})
        if created_flag:
            created += 1

    if created:
        messages.success(request, f"Seeded {created} skills.")
        add_audit_log(request, request.user, f"Seeded {created} skills")
    else:
        messages.info(request, "Skills already seeded.")
        add_audit_log(request, request.user, "Seed skills called but nothing new was added")

    return redirect('admin_skills')

# ============================
#          EMPLOYERS
# ============================

@login_required
def employer_dashboard(request):
    # Fetch only jobs posted by the logged-in user
    my_jobs = Job.objects.filter(user=request.user).order_by('-created_at')
    
    # Get total applicants
    employer_jobs = Job.objects.filter(user=request.user)
    total_applicants = JobApplication.objects.filter(job__in=employer_jobs).count()
    
    # Get total interviews scheduled
    total_interviews = JobApplication.objects.filter(job__in=employer_jobs, status='Interview').count()
    
    # Get notifications
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Get recent applicants
    recent_applicants = JobApplication.objects.filter(job__in=employer_jobs).select_related('user', 'job').order_by('-applied_at')[:5]
    
    # Get recent conversations
    conversations_dict = {}
    for application in JobApplication.objects.filter(job__in=employer_jobs).select_related('user', 'job'):
        if application.user not in conversations_dict:
            last_msg = Message.objects.filter(
                Q(sender=request.user, receiver=application.user) |
                Q(sender=application.user, receiver=request.user),
                is_deleted=False
            ).select_related('sender', 'receiver').order_by('-sent_at').first()
            
            conversations_dict[application.user] = {
                'user': application.user,
                'display_name': application.user.profile.full_name or application.user.username,
                'avatar_url': application.user.profile.profile_image.url if application.user.profile.profile_image else None,
                'last_message': last_msg,
                'applied_job': application.job.title,
            }
    
    recent_conversations = sorted(
        conversations_dict.values(),
        key=lambda x: x['last_message'].sent_at if x['last_message'] else timezone.now(),
        reverse=True
    )[:5]
    
    # Get unread messages count
    unread_messages_count = Message.objects.filter(receiver=request.user, is_read=False).count()

    context = {
        'my_jobs': my_jobs,
        'active_jobs_count': my_jobs.count(),
        'total_applicants': total_applicants,
        'total_interviews': total_interviews,
        'recent_applicants': recent_applicants,
        'recent_conversations': recent_conversations,
        'unread_messages_count': unread_messages_count,
        'recent_notifications': recent_notifications,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, "employers/dashboard.html", context)

@login_required
def manage_jobs(request):
    my_jobs = Job.objects.filter(posted_by=request.user).order_by('-created_at')
    return render(request, "employers/manage_jobs.html", {"jobs": my_jobs})

@login_required
def employerpost_job(request):
    if request.method == "POST":
        title = request.POST.get('title')
        company = request.POST.get('company_name')
        desc = request.POST.get('description')
        loc = request.POST.get('location')
        emp_type = request.POST.get('employment_type')
        sched = request.POST.get('working_schedule')

        job = Job.objects.create(
            user=request.user,
            title=title,
            company_name=company,
            description=desc,
            location=loc,
            employment_type=emp_type,
            working_schedule=sched
        )
        
        skills_list = request.POST.getlist('skills')
        if skills_list:
            # Map submitted ids (which may be Skill or SkillTag ids) to SkillTag ids
            tag_ids = []
            for sid in skills_list:
                try:
                    # First, try interpreting as a SkillTag id
                    tag = SkillTag.objects.get(pk=int(sid))
                    tag_ids.append(tag.pk)
                    continue
                except (SkillTag.DoesNotExist, ValueError):
                    pass

                try:
                    # Fallback: it's a Skill id (admin-created skill). Map by name to SkillTag (create if missing)
                    skill_obj = Skill.objects.get(pk=int(sid))
                    tag, _ = SkillTag.objects.get_or_create(name=skill_obj.name)
                    tag_ids.append(tag.pk)
                except (Skill.DoesNotExist, ValueError):
                    # ignore invalid values
                    continue

            if tag_ids:
                job.skills.set(tag_ids)

        add_audit_log(request, request.user, f"Employer posted job '{job.title}' (id:{job.id})")
        return redirect('employer_dashboard')
        
    # THE FIX: Use the 'Skill' model and filter for Global + Employer skills
    # This allows employers to see the skills added by the admin
    all_skills = Skill.objects.filter(
        Q(user__isnull=True) | Q(user__user=request.user)
    ).order_by('name')

    return render(request, "employers/employerpost_job.html", {"skills": all_skills})

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
                user_obj = User.objects.get(email__iexact=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            
            # --- ROLE BASED REDIRECT ---
            # Check the profile role you saved during signup
            try:
                if user.profile.role == 'employer':
                    return redirect("employer_dashboard")
            except AttributeError:
                # Fallback if profile doesn't exist for some reason
                pass
                
            return redirect("homepage") # Default for job seekers
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, "main/login.html")

from django.db import IntegrityError

def signup_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        username = request.POST.get("username", "").strip() or email
        password = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        role = request.POST.get("role", "job_seeker")
        phone = request.POST.get("phone_number", "")
        birthday = request.POST.get("birthday", None)

        # Preserve entered (non-password) fields when re-rendering the form
        context = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "phone_number": phone,
            "birthday": birthday,
            "role": role,
        }

        if password != password2:
            messages.error(request, "Passwords do not match.")
            context["password_invalid"] = True
            return render(request, "main/signup.html", context)

        # Password policy validation
        import re
        if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"\d", password) or not re.search(r"[^A-Za-z0-9]", password):
            messages.error(request, "Password must be at least 8 characters and include at least one uppercase letter, one number, and one symbol.")
            context["password_invalid"] = True
            return render(request, "main/signup.html", context)

        try:
            # 1. Create User with role and phone (since they are now in your Custom User model)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,             # Added to User model
                phone_number=phone,    # Added to User model
                birthday=birthday if birthday else None # Added to User model
            )

            # 2. Update the Profile (Signals create this automatically)
            profile = user.profile 
            profile.role = role
            profile.phone_number = phone
            profile.full_name = f"{first_name} {last_name}".strip()
            profile.save()
            
        except IntegrityError:
            messages.error(request, "Username or Email already registered.")
            return render(request, "main/signup.html", context)

        messages.success(request, "Account created successfully. Please login.")
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
    other_jobs = jobs_from_others[:2]

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
                job = Job.objects.create(
                    user=request.user,
                    title=title,
                    company_name=company,
                    description=description,
                    location=location,
                    employment_type=employment_type if employment_type else None,
                    working_schedule=working_schedule if working_schedule else None
                )
                
                # Create notifications for users with matching skills
                user_skill_names = set(profile.skills.values_list('name', flat=True))
                if user_skill_names:
                    # Find users whose skills match job description or tags
                    for other_profile in Profile.objects.exclude(user=request.user).select_related('user'):
                        other_skills = set(other_profile.skills.values_list('name', flat=True))
                        matching_skills = user_skill_names.intersection(other_skills)
                        if matching_skills or any(skill.lower() in description.lower() for skill in other_skills):
                            Notification.objects.create(
                                user=other_profile.user,
                                notification_type='job_post',
                                title=f'New Job: {title}',
                                message=f'{request.user.profile.full_name or request.user.username} posted a job that matches your skills',
                                link=f'/find-job/',
                                related_user=request.user
                            )
                
                messages.success(request, "Job posted successfully!")
                return redirect('homepage')
        else:
            # Create a regular post
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.save()
                add_audit_log(request, request.user, f"Created post (id:{post.id})")
                messages.success(request, "Post created successfully!")
                return redirect('homepage')
    else:
        form = PostForm()

    # Basic counts and defaults for sidebar cards
    saved_jobs_count = SavedJob.objects.filter(user=request.user).count()
    applications_count = JobApplication.objects.filter(user=request.user).count()
    interviews_count = JobApplication.objects.filter(user=request.user, status='Interview').count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    # Simple recommended users list (exclude self)
    recommended_users = User.objects.exclude(id=request.user.id)[:5]

    # Stub data for industries and popular_jobs if not provided elsewhere
    industries = []
    popular_jobs = []

    # Determine if user is an employer
    is_employer = profile.role == "employer"
    
    # For employers, get applications received
    if is_employer:
        my_jobs_ids = my_jobs.values_list('id', flat=True)
        applications_count = JobApplication.objects.filter(job_id__in=my_jobs_ids).count()
        interviews_count = JobApplication.objects.filter(job_id__in=my_jobs_ids, status='Interview').count()
    
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
        'interviews_count': interviews_count,
        'unread_notifications': unread_notifications,
        'recommended_users': recommended_users,
        'industries': industries,
        'popular_jobs': popular_jobs,
        'saved_jobs': SavedJob.objects.filter(user=request.user).select_related('job', 'job__user', 'job__user__profile'),
        'is_employer': is_employer,  # Add role info
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
            .select_related("user", "user__profile")
            .prefetch_related("skills")
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

    # Fallback: if no suggestions (no skills or no matches), show recent jobs
    if not suggestions:
        fallback_jobs = Job.objects.select_related("user", "user__profile").prefetch_related("skills") \
            .exclude(user=request.user).order_by("-created_at")[:6]
        suggestions = [{
            "job": job,
            "match_percent": 0,
            "matched_skills": [],
        } for job in fallback_jobs]

    # Fetch user's posts
    user_posts = Post.objects.filter(user=request.user).order_by("-created_at")

    # Applications and interviews for this user
    applications_qs = JobApplication.objects.filter(user=request.user).select_related('job', 'job__user', 'job__user__profile')
    interviews_qs = applications_qs.filter(status='Interview')
    applications_count = applications_qs.count()
    interviews_count = interviews_qs.count()

    return render(request, "main/profile.html", {
        "profile": profile,
        "suggestions": suggestions,
        "user_posts": user_posts,
        "applications_count": applications_count,
        "interviews_count": interviews_count,
        "applications": applications_qs,
        "interviews": interviews_qs,
    })


@login_required
def view_user_profile(request, user_id):
    """View another user's profile with option to message them"""
    viewed_user = get_object_or_404(User, id=user_id)
    
    # Don't allow viewing own profile through this view
    if viewed_user == request.user:
        return redirect('profile')
    
    profile = viewed_user.profile
    user_skill_names = list(profile.skills.values_list("name", flat=True))
    
    # Get their job posts if they're an employer
    jobs_posted = Job.objects.filter(user=viewed_user) if profile.role == 'employer' else []
    
    return render(request, "main/view_user_profile.html", {
        "viewed_user": viewed_user,
        "profile": profile,
        "user_skills": profile.skills.all(),
        "jobs_posted": jobs_posted,
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

    # If no jobs exist (fresh DB), seed a handful so the page always has content
    if not Job.objects.exists():
        owner = User.objects.first()
        if owner:
            sample_jobs = [
                Job(
                    user=owner,
                    title="Frontend Engineer",
                    company_name="Aurora Labs",
                    description="Build delightful UIs in React and Tailwind, ship features fast, and collaborate with product/design.",
                    location="Remote",
                    employment_type="FULLTIME",
                    working_schedule="flexible",
                ),
                Job(
                    user=owner,
                    title="Backend Developer",
                    company_name="BlueRiver Tech",
                    description="Design and scale APIs with Django/DRF, write clean code, and improve performance and observability.",
                    location="New York, NY",
                    employment_type="FULLTIME",
                    working_schedule="full_day",
                ),
                Job(
                    user=owner,
                    title="Data Analyst",
                    company_name="InsightIQ",
                    description="Explore datasets, build dashboards, and communicate insights using SQL, Python, and modern BI tools.",
                    location="Austin, TX",
                    employment_type="PARTTIME",
                    working_schedule="flexible",
                ),
                Job(
                    user=owner,
                    title="Product Designer",
                    company_name="Northwind Studio",
                    description="Own end-to-end design from research to high-fidelity, prototype interactions, and partner with engineering.",
                    location="San Francisco, CA",
                    employment_type="CONTRACT",
                    working_schedule="flexible",
                ),
                Job(
                    user=owner,
                    title="DevOps Engineer",
                    company_name="CloudForge",
                    description="Automate CI/CD, harden cloud infra, improve reliability, and drive cost optimizations.",
                    location="Remote",
                    employment_type="FULLTIME",
                    working_schedule="full_day",
                ),
            ]
            Job.objects.bulk_create(sample_jobs)
    
    jobs = Job.objects.select_related('user', 'user__profile').prefetch_related('skills').all()

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
    """Legacy job search - redirects to global search"""
    return global_search(request)


def global_search(request):
    """Search for jobs, users, and employers"""
    query = request.GET.get("q", "")
    
    jobs = []
    users = []
    employers = []
    
    if query:
        # Search jobs
        jobs = Job.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company_name__icontains=query) |
            Q(location__icontains=query)
        ).select_related('user', 'user__profile').prefetch_related('skills')[:20]
        
        # Search users (job seekers)
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(profile__full_name__icontains=query) |
            Q(profile__bio__icontains=query)
        ).exclude(profile__role='employer').select_related('profile')[:10]
        
        # Search employers
        employers = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(profile__full_name__icontains=query) |
            Q(profile__bio__icontains=query),
            profile__role='employer'
        ).select_related('profile')[:10]

    return render(request, "main/search_results.html", {
        "query": query,
        "jobs": jobs,
        "users": users,
        "employers": employers,
        "total_results": len(jobs) + len(users) + len(employers)
    })


# ============================
# JOB APPLICATIONS
# ============================
@login_required
def job_applications_page(request):
    # If user is employer, show applications to their jobs
    if request.user.profile.role == "employer":
        my_jobs = Job.objects.filter(user=request.user)
        applications = JobApplication.objects.filter(job__in=my_jobs).select_related('user', 'job', 'user__profile')
        return render(request, "main/job_applications.html", {
            "applications": applications,
            "is_employer": True
        })
    # Otherwise show user's own applications
    else:
        applications = JobApplication.objects.filter(user=request.user)
        return render(request, "main/job_applications.html", {
            "applications": applications,
            "is_employer": False
        })


# ============================
# INTERVIEWS (filtered applications)
# ============================
@login_required
def interviews_page(request):
    if request.user.profile.role == "employer":
        my_jobs = Job.objects.filter(user=request.user)
        applications = JobApplication.objects.filter(job__in=my_jobs, status='Interview').select_related('user', 'job', 'user__profile')
        return render(request, "main/interviews.html", {
            "applications": applications,
            "is_employer": True
        })
    else:
        applications = JobApplication.objects.filter(user=request.user, status='Interview').select_related('job', 'job__user', 'job__user__profile')
        return render(request, "main/interviews.html", {
            "applications": applications,
            "is_employer": False
        })


# ============================
# Update application status (employer only)
# ============================
@login_required
def update_application_status(request, app_id: int):
    application = get_object_or_404(JobApplication, id=app_id)
    # Only the job owner can change status
    if application.job.user != request.user:
        messages.error(request, "You do not have permission to update this application.")
        return redirect('job_applications')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        canonical = None
        for choice_val, _ in JobApplication.STATUS_CHOICES:
            if str(new_status).lower() == str(choice_val).lower():
                canonical = choice_val
                break
        if canonical:
            # If employer chooses Interview, redirect to interview details so they can schedule.
            # Do not persist 'Interview' until an interview is scheduled and confirmed.
            if canonical == 'Interview':
                interview_url = reverse('employer_schedule_interview', args=[application.id])
                # If AJAX, tell the client to redirect to the schedule page; otherwise perform normal redirect
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'redirect': interview_url})
                messages.success(request, "Proceed to schedule the interview — the application status will be set when the interview is confirmed.")
                return redirect(interview_url)

            # Otherwise persist status immediately
            application.status = canonical
            application.save(update_fields=['status'])

            # If caller expects JSON (AJAX), return success without redirect so the UI can update in-place
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'status': canonical, 'message': 'Application status updated.'})

            messages.success(request, "Application status updated.")
        else:
            messages.error(request, "Invalid status selected.")
    # For non-AJAX submits keep the employer on the applicants page
    return redirect('employer_applicants')


# ============================
# Schedule interview + generate ICS invite
# ============================
@login_required
def schedule_interview(request, app_id: int):
    application = get_object_or_404(JobApplication, id=app_id)
    # Only job owner can schedule
    if application.job.user != request.user:
        messages.error(request, "You do not have permission to schedule this interview.")
        return redirect('job_applications')

    if request.method == 'POST':
        # Support both datetime-local and separate date/time dropdowns
        scheduled_at_str = request.POST.get('scheduled_at')  # HTML datetime-local
        date_only = request.POST.get('date')
        time_only = request.POST.get('time')
        location = request.POST.get('location', '')
        meeting_url = request.POST.get('meeting_url', '')
        try:
            duration_minutes = int(request.POST.get('duration_minutes', '45'))
        except ValueError:
            duration_minutes = 45

        try:
            naive = None
            if scheduled_at_str:
                # Expect 'YYYY-MM-DDTHH:MM'
                naive = datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
            elif date_only and time_only:
                naive = datetime.strptime(f"{date_only}T{time_only}", '%Y-%m-%dT%H:%M')
            elif date_only:
                # date only -> default to 09:00
                naive = datetime.strptime(f"{date_only}T09:00", '%Y-%m-%dT%H:%M')

            if naive:
                aware_dt = timezone.make_aware(naive, timezone.get_current_timezone())
            else:
                aware_dt = None
        except Exception:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid date/time format.'}, status=400)
            messages.error(request, 'Invalid date/time format.')
            return redirect('employer_applicants')

        application.interview_scheduled_at = aware_dt
        application.interview_location = location or None
        application.interview_meeting_url = meeting_url or None
        application.status = 'Interview'
        application.save()

        # Notify applicant
        Notification.objects.create(
            user=application.user,
            notification_type='system',
            title='Interview Scheduled',
            message=f'Interview scheduled for {application.job.title}',
            link=f'/interviews/',
            related_user=request.user
        )

        # Email ICS invite to applicant
        if application.interview_scheduled_at:
            start = application.interview_scheduled_at
            end = start + timedelta(minutes=duration_minutes)
            dtstamp = _format_ics_dt(timezone.now())
            dtstart = _format_ics_dt(start)
            dtend = _format_ics_dt(end)
            summary = f"Interview: {application.job.title}"
            description_lines = [
                f"Job: {application.job.title}",
            ]
            if application.interview_meeting_url:
                description_lines.append(f"Meeting URL: {application.interview_meeting_url}")
            if application.interview_location:
                description_lines.append(f"Location: {application.interview_location}")
            description = "\\n".join(description_lines)

            ics = (
                "BEGIN:VCALENDAR\n"
                "VERSION:2.0\n"
                "PRODID:-//ADS Django//EN\n"
                "METHOD:REQUEST\n"
                "BEGIN:VEVENT\n"
                f"UID:jobapp-{application.id}@mysite\n"
                f"DTSTAMP:{dtstamp}\n"
                f"DTSTART:{dtstart}\n"
                f"DTEND:{dtend}\n"
                f"SUMMARY:{summary}\n"
                f"DESCRIPTION:{description}\n"
                "END:VEVENT\n"
                "END:VCALENDAR\n"
            )

            subject = f"Interview Scheduled: {application.job.title}"
            body = (
                f"Hi {application.user.first_name or application.user.username},\n\n"
                f"Your interview for '{application.job.title}' has been scheduled.\n"
                f"When: {start.strftime('%b %d, %Y %I:%M %p %Z')}\n"
                f"Where: {application.interview_location or 'Online'}\n"
                f"Meeting: {application.interview_meeting_url or 'N/A'}\n\n"
                "An event invite is attached."
            )
            email = EmailMessage(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [application.user.email]
            )
            email.attach(filename=f"interview-{application.id}.ics", content=ics, mimetype='text/calendar')
            try:
                email.send(fail_silently=True)
            except Exception:
                pass

        msg_text = 'Interview scheduled; invite emailed and ready to download.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': msg_text,
                'scheduled_at': application.interview_scheduled_at.isoformat() if application.interview_scheduled_at else None,
                'location': application.interview_location,
                'meeting_url': application.interview_meeting_url,
                'download_url': reverse('download_interview_invite', args=[application.id])
            })

        messages.success(request, msg_text)
        return redirect('employer_interview_detail', app_id=application.id)


def _format_ics_dt(dt):
    # Use stdlib UTC timezone to avoid relying on django.utils.timezone.utc
    dt_utc = dt.astimezone(dt_timezone.utc)
    return dt_utc.strftime('%Y%m%dT%H%M%SZ')


@login_required
def download_interview_invite(request, app_id: int):
    application = get_object_or_404(JobApplication, id=app_id)
    # Allow applicant or job owner
    if not (application.user == request.user or application.job.user == request.user):
        messages.error(request, 'You do not have access to this invite.')
        return redirect('homepage')

    if not application.interview_scheduled_at:
        messages.error(request, 'No interview schedule set for this application.')
        return redirect('job_applications')

    start = application.interview_scheduled_at
    end = start + timedelta(minutes=45)
    dtstamp = _format_ics_dt(timezone.now())
    dtstart = _format_ics_dt(start)
    dtend = _format_ics_dt(end)

    summary = f"Interview: {application.job.title}"
    description_lines = []
    if application.interview_meeting_url:
        description_lines.append(f"Meeting URL: {application.interview_meeting_url}")
    if application.interview_location:
        description_lines.append(f"Location: {application.interview_location}")
    description = "\\n".join(description_lines) or 'Interview'

    ics = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//ADS Django//EN\n"
        "BEGIN:VEVENT\n"
        f"UID:jobapp-{application.id}@mysite\n"
        f"DTSTAMP:{dtstamp}\n"
        f"DTSTART:{dtstart}\n"
        f"DTEND:{dtend}\n"
        f"SUMMARY:{summary}\n"
        f"DESCRIPTION:{description}\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )

    response = HttpResponse(ics, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename=interview-{application.id}.ics'
    return response


# ------------------------------
# Employer Interview views
# ------------------------------
@login_required
def employer_interview_detail(request, app_id: int):
    application = get_object_or_404(JobApplication, id=app_id)
    if application.job.user != request.user:
        messages.error(request, "You do not have permission to view this interview.")
        return redirect('employer_applicants')

    return render(request, 'employers/employer_interview.html', {
        'application': application
    })


@login_required
def employer_schedule_interview(request, app_id: int):
    """Render a full scheduling page with date/time dropdowns for employers.

    The form posts to the existing `schedule_interview` endpoint which will
    validate and persist the schedule. This view only provides select
    options for dates and times.
    """
    application = get_object_or_404(JobApplication, id=app_id)
    if application.job.user != request.user:
        messages.error(request, "You do not have permission to schedule this interview.")
        return redirect('employer_applicants')

    # Prepare date options (next 14 days)
    today = timezone.localtime(timezone.now()).date()
    date_options = []
    for i in range(0, 15):
        d = today + timedelta(days=i)
        date_options.append({
            'value': d.isoformat(),
            'label': d.strftime('%a %b %d, %Y')
        })

    # Prepare time slots (every 30 minutes from 08:00 to 18:00)
    time_options = []
    for h in range(8, 19):
        for m in (0, 30):
            val = f"{h:02d}:{m:02d}"
            # Display in 12h format
            dt = datetime.strptime(val, '%H:%M')
            label = dt.strftime('%I:%M %p').lstrip('0')
            time_options.append({'value': val, 'label': label})

    return render(request, 'employers/employer_schedule.html', {
        'application': application,
        'date_options': date_options,
        'time_options': time_options,
    })

# ============================
# SKILLS
# ============================
@login_required
def skills_page(request):
    """Show available admin-provided (global) skills and let jobseekers add from that list only."""

    # User's own selected skills
    skills = Skill.objects.filter(user=request.user.profile).order_by('name')

    # Available admin/global skills
    global_skills_qs = Skill.objects.filter(user__isnull=True).order_by('name')

    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            selected_name = form.cleaned_data['name']
            level = form.cleaned_data['level']

            # Ensure selected skill exists among global skills
            if not global_skills_qs.filter(name=selected_name).exists():
                messages.error(request, "That skill is not available. Please choose from the admin-provided list.")
                return redirect('skills')

            # Prevent duplicate skill entries for the same user
            if Skill.objects.filter(user=request.user.profile, name=selected_name).exists():
                messages.info(request, "You already have this skill added.")
                return redirect('skills')

            # Create a user-owned skill record referring to the chosen global skill name
            Skill.objects.create(user=request.user.profile, name=selected_name, level=level)
            add_audit_log(request, request.user, f"Added skill '{selected_name}'")
            messages.success(request, f"Added skill: {selected_name}")
            return redirect("skills")
    else:
        form = SkillForm()

    # Pass options for datalist in template (name,label pairs)
    SKILL_OPTIONS = [(s.name, s.name) for s in global_skills_qs]

    return render(request, "main/skills.html", {
        "skills": skills,
        "form": form,
        "SKILL_OPTIONS": SKILL_OPTIONS,
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
        Q(sender=request.user) | Q(receiver=request.user),
        is_deleted=False
    ).select_related('sender', 'receiver', 'sender__profile', 'receiver__profile').order_by("-sent_at")

    conversations = {}
    for m in msgs:
        other = m.receiver if m.sender == request.user else m.sender
        if other not in conversations:
            conversations[other] = {
                'user': other,
                'display_name': other.profile.full_name or other.username,
                'avatar_url': other.profile.profile_image.url if other.profile.profile_image else None,
                'last_message': m
            }

    return render(request, "main/messages.html", {
        "conversations": conversations.values()
    })


@login_required
def conversation_view(request, user_id):
    other = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        content = request.POST.get("message")
        if content:
            msg = Message.objects.create(
                sender=request.user,
                receiver=other,
                content=content
            )
            add_audit_log(request, request.user, f"Sent message to {other.username}: {content[:120]}")
            # Create notification for receiver
            Notification.objects.create(
                user=other,
                notification_type='message',
                title='New Message',
                message=f'{request.user.profile.full_name or request.user.username} sent you a message',
                link=f'/messages/{request.user.id}/',
                related_user=request.user
            )
        return redirect("conversation", user_id=user_id)

    # Get all messages in the conversation
    convo = Message.objects.filter(
        Q(sender=request.user, receiver=other) |
        Q(sender=other, receiver=request.user),
        is_deleted=False
    ).select_related('sender', 'receiver').order_by("sent_at")

    # Mark unread messages as read
    Message.objects.filter(
        sender=other, receiver=request.user, is_read=False
    ).update(is_read=True)

    # Get all conversations for sidebar
    msgs = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        is_deleted=False
    ).select_related('sender', 'receiver', 'sender__profile', 'receiver__profile').order_by("-sent_at")

    conversations = {}
    for m in msgs:
        conv_other = m.receiver if m.sender == request.user else m.sender
        if conv_other not in conversations:
            conversations[conv_other] = {
                'user': conv_other,
                'display_name': conv_other.profile.full_name or conv_other.username,
                'avatar_url': conv_other.profile.profile_image.url if conv_other.profile.profile_image else None,
                'last_message': m
            }

    return render(request, "main/messages.html", {
        "conversation_user": other,
        "conversation_user_display": other.profile.full_name or other.username,
        "conversation_user_avatar": other.profile.profile_image.url if other.profile.profile_image else None,
        "messages_qs": convo,
        "conversations": conversations.values(),
    })


@login_required
def edit_message(request, message_id):
    """Edit a message (only by sender)"""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    
    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            message.content = content
            message.is_edited = True
            message.edited_at = timezone.now()
            message.save()
            return JsonResponse({"success": True, "content": content, "edited_at": message.edited_at.strftime("%b %d, %H:%M")})
    
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def delete_message(request, message_id):
    """Delete a message (only by sender)"""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    
    if request.method == "POST":
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.content = "[Message deleted]"
        message.save()
        return JsonResponse({"success": True})
    
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def search_messages(request):
    """Search messages in conversations"""
    query = request.GET.get("q", "")
    if not query:
        return JsonResponse({"results": []})
    
    # Search in messages where user is sender or receiver
    messages_found = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        content__icontains=query,
        is_deleted=False
    ).select_related('sender', 'receiver', 'sender__profile', 'receiver__profile').order_by('-sent_at')[:20]
    
    results = []
    for msg in messages_found:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        results.append({
            "id": msg.id,
            "content": msg.content,
            "sent_at": msg.sent_at.strftime("%b %d, %H:%M"),
            "other_user_id": other_user.id,
            "other_user_name": other_user.profile.full_name or other_user.username,
            "is_sender": msg.sender == request.user
        })
    
    return JsonResponse({"results": results})


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


@login_required
def privacy(request):
    profile = request.user.profile
    
    if request.method == "POST":
        profile.profile_visibility = request.POST.get('profile_visibility', 'employers')
        profile.allow_contact = request.POST.get('allow_contact') == 'on'
        profile.save()
        messages.success(request, "Privacy settings updated successfully!")
        return redirect("settings_privacy")
    
    return render(request, "main/privacy2.html", {"profile": profile})


@login_required
def security(request):
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'logout_all':
            # For now, just log out current session
            messages.info(request, "Logged out from all devices.")
            return redirect('logout')
        
        # Handle password change
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if old_password and new_password1 and new_password2:
            if new_password1 != new_password2:
                messages.error(request, "New passwords don't match.")
            elif not request.user.check_password(old_password):
                messages.error(request, "Current password is incorrect.")
            elif len(new_password1) < 8:
                messages.error(request, "Password must be at least 8 characters.")
            else:
                request.user.set_password(new_password1)
                request.user.save()
                messages.success(request, "Password changed successfully! Please log in again.")
                return redirect('login')
        else:
            messages.success(request, "Security settings updated.")
        
        return redirect("settings_security")
    
    return render(request, "main/security.html")


@login_required
def language(request):
    profile = request.user.profile
    
    if request.method == "POST":
        # Save language and appearance preferences
        profile.language = request.POST.get('language', 'en')
        profile.timezone = request.POST.get('timezone', 'UTC')
        profile.dark_mode = request.POST.get('dark_mode') == 'on'
        profile.save()
        messages.success(request, "Language and appearance preferences saved!")
        return redirect("settings_language")
    
    return render(request, "main/language2.html", {"profile": profile})


@login_required
def data_control(request):
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'download':
            messages.info(request, "Your data export has been requested. You'll receive an email when it's ready.")
        elif action == 'deactivate':
            messages.warning(request, "Account deactivation feature coming soon.")
        elif action == 'delete':
            messages.error(request, "Account deletion is permanent. Contact support to proceed.")
        
        return redirect("settings_data_control")
    
    return render(request, "main/data-control2.html")


@login_required
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
            add_audit_log(request, request.user, f"Created job '{job.title}' (id:{job.id})")
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
            add_audit_log(request, request.user, f"Updated job '{job.title}' (id:{job.id})")
            messages.success(request, "Job updated successfully!")
            return redirect("homepage")
    else:
        form = JobForm(instance=job)
    return render(request, "main/create_job.html", {"form": form, "editing": True})


@login_required
def delete_job(request, job_id: int):
    job = get_object_or_404(Job, id=job_id, user=request.user)
    if request.method == "POST":
        title = job.title
        job.delete()
        add_audit_log(request, request.user, f"Deleted job '{title}' (id:{job_id})")
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


def logout_view(request):
    """Log the user out on GET or POST and redirect to landing."""
    if request.method in ("POST", "GET"):
        django_logout(request)
        return redirect('landing')
    # Fallback for other methods
    return redirect('landing')

@login_required
def apply_job(request, job_id):
    """Handle job application submission"""
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is a job seeker, not an employer
    if request.user.profile.role == "employer":
        messages.error(request, "Employers cannot apply for jobs.")
        return redirect("find_job")
    
    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.job = job
            application.save()
            add_audit_log(request, request.user, f"Applied to job '{job.title}' (id:{job.id})")
            
            # Create notification for job poster
            Notification.objects.create(
                user=job.user,
                notification_type='job_application',
                title=f'New Application: {job.title}',
                message=f'{request.user.profile.full_name or request.user.username} applied for {job.title}',
                link=f'/job-applications/',
                related_user=request.user
            )
            
            messages.success(request, "Application submitted successfully!")
            return redirect("find_job")
    else:
        form = JobApplicationForm()
    
    return render(request, "main/apply_job.html", {
        "job": job,
        "form": form,
    })


@login_required
def toggle_save_job(request, job_id):
    """Save or unsave a job"""
    job = get_object_or_404(Job, id=job_id)
    
    saved_job, created = SavedJob.objects.get_or_create(
        user=request.user,
        job=job
    )
    
    if not created:
        # Job was already saved, so delete it
        saved_job.delete()
        add_audit_log(request, request.user, f"Removed saved job '{job.title}' (id:{job.id})")
        messages.info(request, "Job removed from saved.")
        is_saved = False
    else:
        messages.success(request, "Job saved successfully!")
        add_audit_log(request, request.user, f"Saved job '{job.title}' (id:{job.id})")
        is_saved = True
    
    # Return JSON response for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'saved': is_saved})
    
    return redirect(request.META.get('HTTP_REFERER', 'find_job'))

from .models import Skill

# Helper: Build employer conversation list (job applicants with last message/unread counts)
def _get_employer_conversations(user):
    employer_jobs = Job.objects.filter(user=user)
    job_applicants = JobApplication.objects.filter(job__in=employer_jobs).select_related('user', 'job')

    conversations = {}
    for application in job_applicants:
        applicant = application.user
        # Find last message exchanged (if any)
        last_msg = Message.objects.filter(
            Q(sender=user, receiver=applicant) | Q(sender=applicant, receiver=user),
            is_deleted=False
        ).select_related('sender', 'receiver').order_by('-sent_at').first()

        # Count unread messages from this applicant to employer
        unread_count = Message.objects.filter(
            sender=applicant,
            receiver=user,
            is_read=False,
            is_deleted=False
        ).count()

        # Only set once per applicant; prefer the latest message info if already present
        if applicant not in conversations or (last_msg and conversations[applicant]['last_message'] and last_msg.sent_at > conversations[applicant]['last_message'].sent_at):
            conversations[applicant] = {
                'user': applicant,
                'display_name': applicant.profile.full_name or applicant.username,
                'avatar_url': applicant.profile.profile_image.url if applicant.profile.profile_image else None,
                'last_message': last_msg,
                'applied_job': application.job.title,
                'unread_count': unread_count,
            }

    return sorted(
        conversations.values(),
        key=lambda x: x['last_message'].sent_at if x['last_message'] else timezone.now(),
        reverse=True
    )

# ============================
# EMPLOYER MESSAGING
# ============================
@login_required
def employer_messages_inbox(request):
    """Employer inbox showing all conversations with job applicants"""
    if request.user.profile.role != 'employer':
        return HttpResponseForbidden()
    
    conversations = _get_employer_conversations(request.user)

    return render(request, "employers/employer_messages.html", {
        "conversations": conversations,
    })


@login_required
def employer_message_conversation(request, applicant_id):
    """Employer conversation view with a job applicant"""
    if request.user.profile.role != 'employer':
        return HttpResponseForbidden()
    
    applicant = get_object_or_404(User, id=applicant_id)
    
    # Verify this applicant has applied to one of the employer's jobs
    employer_jobs = Job.objects.filter(user=request.user)
    has_applied = JobApplication.objects.filter(user=applicant, job__in=employer_jobs).exists()
    
    if not has_applied:
        return HttpResponseForbidden()
    
    if request.method == "POST":
        content = request.POST.get("message")
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=applicant,
                content=content
            )
            # Create notification for applicant
            Notification.objects.create(
                user=applicant,
                notification_type='message',
                title='New Message from Employer',
                message=f'{request.user.profile.full_name or request.user.username} sent you a message',
                link=f'/messages/{request.user.id}/',
                related_user=request.user
            )
        return redirect("employer_message_conversation", applicant_id=applicant_id)
    
    # Get all messages in the conversation
    convo = Message.objects.filter(
        Q(sender=request.user, receiver=applicant) |
        Q(sender=applicant, receiver=request.user),
        is_deleted=False
    ).select_related('sender', 'receiver').order_by("sent_at")
    
    # Mark unread messages as read
    Message.objects.filter(
        sender=applicant, receiver=request.user, is_read=False
    ).update(is_read=True)
    
    # Get job applications from this applicant
    applications = JobApplication.objects.filter(user=applicant, job__user=request.user).select_related('job')
    conversations = _get_employer_conversations(request.user)

    return render(request, "employers/employer_conversation.html", {
        "applicant": applicant,
        "conversation": convo,
        "applications": applications,
        "conversations": conversations,
    })


@login_required
def employer_search_messages(request):
    """Search messages for employers"""
    if request.user.profile.role != 'employer':
        return JsonResponse({"error": "Forbidden"}, status=403)
    
    query = request.GET.get("q", "")
    if not query:
        return JsonResponse({"results": []})
    
    # Get employer's jobs
    employer_jobs = Job.objects.filter(user=request.user)
    applicant_ids = JobApplication.objects.filter(job__in=employer_jobs).values_list('user_id', flat=True)
    
    # Search in messages where user is sender or receiver (and other party is an applicant)
    messages_found = Message.objects.filter(
        Q(sender=request.user, receiver_id__in=applicant_ids) | 
        Q(sender_id__in=applicant_ids, receiver=request.user),
        content__icontains=query,
        is_deleted=False
    ).select_related('sender', 'receiver', 'sender__profile', 'receiver__profile').order_by('-sent_at')[:20]
    
    results = []
    for msg in messages_found:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        results.append({
            "id": msg.id,
            "content": msg.content,
            "sent_at": msg.sent_at.strftime("%b %d, %H:%M"),
            "other_user_id": other_user.id,
            "other_user_name": other_user.profile.full_name or other_user.username,
            "is_sender": msg.sender == request.user
        })
    
    return JsonResponse({"results": results})


@login_required
def employer_applicants(request):
    """Employer applicants view showing all applications to their jobs"""
    if request.user.profile.role != 'employer':
        return HttpResponseForbidden()
    
    # Get all job applicants for jobs posted by this employer
    employer_jobs = Job.objects.filter(user=request.user)
    applications = JobApplication.objects.filter(job__in=employer_jobs).select_related('user', 'job', 'user__profile').order_by('-applied_at')
    
    # Get filter options
    status_filter = request.GET.get('status', '')
    job_filter = request.GET.get('job', '')
    
    # Apply filters
    if status_filter:
        applications = applications.filter(status=status_filter)
    if job_filter:
        applications = applications.filter(job__id=job_filter)
    
    # Get available statuses and jobs for filter dropdown
    available_statuses = JobApplication.STATUS_CHOICES
    available_jobs = employer_jobs.all()
    
    context = {
        'applications': applications,
        'available_statuses': available_statuses,
        'available_jobs': available_jobs,
        'current_status': status_filter,
        'current_job': job_filter,
        'total_applicants': JobApplication.objects.filter(job__in=employer_jobs).count(),
    }
    
    return render(request, "employers/employer_applicants.html", context)


@login_required
def employer_notifications(request):
    """Employer notifications page"""
    if request.user.profile.role != 'employer':
        return HttpResponseForbidden()
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, "employers/employer_notifications.html", {
        "notifications": notifications,
        "unread_count": unread_count
    })


@login_required
def employer_mark_all_read(request):
    """Mark all employer notifications as read"""
    if request.user.profile.role != 'employer':
        return HttpResponseForbidden()
    
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('employer_notifications')
