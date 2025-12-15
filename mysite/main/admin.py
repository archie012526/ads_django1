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
# JOBS
# ---------------------------
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)

    list_display = (
        'title',
        'user',        # ✅ FIXED (was employer)
        'location',
        'created_at',
    )

    list_filter = (
        'location',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
    )


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
