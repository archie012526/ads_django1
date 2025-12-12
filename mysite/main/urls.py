from django.urls import path
from . import views

urlpatterns = [
    path("", views.landingpage, name="landing"),
    path("home/", views.home_page, name="homepage"),
    path("about/", views.about_page, name="about"),
    path("login/", views.login_page, name="login"),
    path("find-job/", views.find_job_page, name="find_job"),
    path("contact-us/", views.contact_us_page, name="contact_us"),
    path("register/", views.signup_page, name="signup"),
    path("profile/", views.profile_page, name="profile"),

    path("messages/", views.messages_inbox, name="messages"),
    path("messages/<int:user_id>/", views.conversation_view, name="conversation"),
    path("notifications/", views.notifications_page, name="notifications"),
    path("mark-read/", views.mark_all_as_read, name="mark_all_as_read"),

    path("job-applications/", views.job_applications_page, name="job_applications"),
    path("findjobs/", views.find_jobs, name="findjobs"),

    path("add-location/", views.location, name="add_location"),
    path("location/", views.location, name="location"),

    path("profile/edit/", views.edit_profile_page, name="edit_profile"),
    path("skills/", views.skills_page, name="skills"),
    path("skills/<int:skill_id>/edit/", views.edit_skill, name="edit_skill"),
    path("skills/<int:skill_id>/delete/", views.delete_skill, name="delete_skill"),

]
