from django.urls import path
from . import views

urlpatterns = [
    # Landing / Static
    path("", views.landingpage, name="landing"),
    path("about/", views.about_page, name="about"),
    path("contact-us/", views.contact_us_page, name="contact_us"),

    # Auth
    path("login/", views.login_page, name="login"),
    path("register/", views.signup_page, name="signup"),

    # Home & Jobs
    path("home/", views.home_page, name="homepage"),
    path("find-job/", views.find_job, name="find_job"),
    path("job-applications/", views.job_applications_page, name="job_applications"),

    # Profile
    path("profile/", views.profile_page, name="profile"),
    path("profile/edit/", views.edit_profile_page, name="edit_profile"),

    # Skills
    path("skills/", views.skills_page, name="skills"),
    path("skills/<int:skill_id>/edit/", views.edit_skill, name="edit_skill"),
    path("skills/<int:skill_id>/delete/", views.delete_skill, name="delete_skill"),

    # Messages
    path("messages/", views.messages_inbox, name="messages"),
    path("messages/<int:user_id>/", views.conversation_view, name="conversation"),

    # Notifications
    path("notifications/", views.notifications_page, name="notifications"),
    path("mark-read/", views.mark_all_as_read, name="mark_all_as_read"),

    # Location
    path("add-location/", views.location, name="add_location"),

    # ✅ CONTACT FORM EMAIL (THIS IS STEP 4)
    path("contact/email/", views.contact_email, name="contact_email"),
]
