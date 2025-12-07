from django.urls import path
from . import views

urlpatterns = [
    path("", views.landingpage, name="landing"),   # FIRST PAGE
    path("home/", views.homepage, name="homepage"),
    path("jobs/", views.jobs_page, name="jobs"),
    path("about/", views.about_page, name="about"),
    path("login/", views.login_page, name="login"),
    path("find-job/", views.find_job_page, name="find_job"),
    path("contact-us/", views.contact_us_page, name="contact_us"),
    path("login/", views.login_page, name="login"),
    path("register/", views.signup_page, name="signup"),
]


