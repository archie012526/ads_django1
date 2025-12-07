from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User


def homepage(request):
    return render(request, "main/home.html")

def landingpage(request):
    return render(request, "main/landing.html")

def jobs_page(request):
    return render(request, "main/jobs.html")

def about_page(request):
    return render(request, "main/about.html")

def login_page(request):
    return render(request, "main/login.html")

def find_job_page(request):
    return render(request, "main/find_job.html")

def contact_us_page(request):
    return render(request, "main/contact_us.html")

def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if email exists
        if not User.objects.filter(username=email).exists():
            messages.error(request, "Account does not exist. Please register first.")
            return render(request, "main/login.html")

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")  # change to your home page
        else:
            messages.error(request, "Incorrect password.")
            return render(request, "main/login.html")

    return render(request, "main/login.html")

def register_page(request):
    return render(request, "main/register.html")