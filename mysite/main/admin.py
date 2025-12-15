from django.contrib import admin
from .models import (
    Profile,
    Job,
    JobApplication,
    Notification,
    Message,
    ContactSubmission,
    Skill,
    SkillTag,
    Post
)

# ---------------------------
# PROFILE
# ---------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'role', 'location', 'updated_at')
    list_filter = ('role', 'profile_visibility')
    search_fields = ('user__username', 'full_name', 'company_name')
    ordering = ('-updated_at',)


# ---------------------------
# JOBS
# ---------------------------
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)

    list_display = (
        'title',
        'company_name',
        'user',
        'location',
        'skills_list',
        'employment_type',
        'working_schedule',
        'created_at',
    )

    list_filter = (
        'location',
        'employment_type',
        'working_schedule',
        'created_at',
    )

    search_fields = (
        'title',
        'company_name',
        'description',
    )

    # Allow admins to easily create jobs
    fields = ('user', 'title', 'company_name', 'description', 'location', 'employment_type', 'working_schedule', 'skills')
    filter_horizontal = ('skills',)

    def skills_list(self, obj):
        return ", ".join(obj.skills.values_list('name', flat=True)) or "—"
    skills_list.short_description = 'Skills'


# ---------------------------
# JOB APPLICATIONS
# ---------------------------
@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('user__username', 'job__title')
    ordering = ('-applied_at',)


# ---------------------------
# SKILLS
# ---------------------------
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'level')
    list_filter = ('level',)
    search_fields = ('name', 'user__user__username')
    ordering = ('name',)


# ---------------------------
# SKILL TAGS (Job skills)
# ---------------------------
@admin.register(SkillTag)
class SkillTagAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)


# ---------------------------
# NOTIFICATIONS
# ---------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    list_filter = ('is_read',)
    ordering = ('-created_at',)


# ---------------------------
# MESSAGES
# ---------------------------
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'sent_at', 'is_read')
    search_fields = ('sender__username', 'receiver__username', 'content')
    list_filter = ('is_read', 'sent_at')
    ordering = ('-sent_at',)


# ---------------------------
# CONTACT FORM
# ---------------------------
@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'submitted_at')
    search_fields = ('name', 'email')
    ordering = ('-submitted_at',)


# ---------------------------
# POSTS
# ---------------------------
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post_type', 'content_preview', 'has_media', 'created_at')
    list_filter = ('post_type', 'created_at')
    search_fields = ('user__username', 'content', 'article_title')
    ordering = ('-created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def has_media(self, obj):
        return '✓' if (obj.image or obj.video) else '—'
    has_media.short_description = 'Media'
