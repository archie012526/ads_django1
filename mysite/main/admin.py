from django.contrib import admin
from .models import (
    Profile,
    Job,
    JobApplication,
    Notification,
    Message,
    ContactSubmission
)

# ---------------------------
# PROFILE
# ---------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone_number', 'location')
    search_fields = ('user__username', 'full_name', 'phone_number')
    list_filter = ('location',)


# ---------------------------
# JOBS
# ---------------------------
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'posted_at')
    search_fields = ('title', 'company', 'location')
    list_filter = ('location', 'company')
    ordering = ('-posted_at',)


# ---------------------------
# JOB APPLICATIONS
# ---------------------------
@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'applied_at')
    search_fields = ('user__username', 'job__title')
    list_filter = ('status', 'applied_at')
    ordering = ('-applied_at',)


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
# MESSAGES (User-to-user)
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
