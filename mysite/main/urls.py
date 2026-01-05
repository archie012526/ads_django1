from django.urls import path
from django.contrib.auth import views as auth_views
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
    path("home/", views.homepage, name="homepage"),
    path("find-job/", views.find_job, name="find_job"),
    path("job-applications/", views.job_applications_page, name="job_applications"),
    path("interviews/", views.interviews_page, name="interviews"),
    path("applications/<int:app_id>/status/", views.update_application_status, name="update_application_status"),
    path("applications/<int:app_id>/schedule/", views.schedule_interview, name="schedule_interview"),
    path("applications/<int:app_id>/invite.ics", views.download_interview_invite, name="download_interview_invite"),
    path("jobs/<int:job_id>/apply/", views.apply_job, name="apply_job"),
    path("jobs/<int:job_id>/save/", views.toggle_save_job, name="toggle_save_job"),

    # Profile
    path("profile/", views.profile_page, name="profile"),
    path("profile/<int:user_id>/", views.view_user_profile, name="view_user_profile"),
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
    path("add-location/", views.add_location, name="add_location"),


    # ✅ CONTACT FORM EMAIL (THIS IS STEP 4)
    path("contact/email/", views.contact_email, name="contact_email"),

    path('settings/', views.settings_page, name='settings'),
    path('settings/account/', views.account_settings, name='settings_account'),
    path('settings/privacy/', views.privacy, name='settings_privacy'),
    path('settings/security/', views.security, name='settings_security'),
    path('settings/language/', views.language, name='settings_language'),
    path('settings/data-control/', views.data_control, name='settings_data_control'),
    path('settings/help/', views.help_page, name='settings_help'),
    path("jobs/post/", views.post_job, name="post_job"),
    path("jobs/create/", views.create_job, name="create_job"),
    path("jobs/<int:job_id>/edit/", views.edit_job, name="edit_job"),
    path("jobs/<int:job_id>/delete/", views.delete_job, name="delete_job"),

    path('data-control/', views.data_control, name='data_control'),
    path('help/', views.help_page, name='help'),
    path('language/', views.language, name='language'),
    path('privacy/', views.privacy, name='privacy'),
    path('security/', views.security, name='security'),

    path("search/", views.global_search, name="search"),
    path("job-search/", views.job_search, name="job_search"),  # Legacy redirect

    # Logout (custom view supporting GET and POST)
    path("logout/", views.logout_view, name="logout"),

    # ===============================
    # ADMIN PANEL (SUPERUSER ONLY)
    # ===============================
    path("admin-panel/login/", views.admin_login, name="admin_login"),
    path("admin-panel/logout/", views.logout_view, name="admin_logout"),
    path("admin-panel/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/users/", views.admin_users, name="admin_users"),
    path("admin-panel/users/<int:user_id>/toggle-ban/", views.toggle_user_ban, name="toggle_user_ban"),
    path("admin-panel/jobs/", views.admin_jobs, name="admin_jobs"),
    path("admin-panel/jobs/<int:job_id>/toggle-approval/", views.toggle_job_approval, name="toggle_job_approval"),
    path("admin-panel/jobs/<int:job_id>/delete/", views.delete_job, name="delete_job"),
    path('admin-panel/seed-skills/', views.seed_skills_view, name='seed_skills'),
    path("admin-panel/skills/", views.admin_skills, name="admin_skills"),
    path('admin-panel/skills/delete/<int:pk>/', views.admin_skill_delete, name='admin_skill_delete'),

    # Employer Section
    path("employers/dashboard/", views.employer_dashboard, name="employer_dashboard"),
    path("employers/jobs/", views.manage_jobs, name="manage_jobs"),
    path("employers/employerpost_job/", views.employerpost_job, name="employerpost_job"),
    path("employers/messages/", views.employer_messages_inbox, name="employer_messages"),
    path("employers/messages/<int:applicant_id>/", views.employer_message_conversation, name="employer_message_conversation"),
    path("employers/applicants/", views.employer_applicants, name="employer_applicants"),
]   

    
