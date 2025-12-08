from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User


def homepage(request):
    return render(request, "main/home.html")

def landingpage(request):
    return render(request, "main/landing.html")

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
            return redirect("homepage")  # change to your home page
        else:
            messages.error(request, "Incorrect password.")
            return render(request, "main/login.html")

    return render(request, "main/login.html")

def signup_page(request):
    if request.method == "POST":
        first = request.POST.get("first_name")
        last = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if account already exists
        if User.objects.filter(username=email).exists():
            messages.error(request, "Account already exists. Please log in instead.")
            return render(request, "main/signup.html")

        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first,
            last_name=last,
            password=password
        )
        user.save()

        # Auto login after registration
        login(request, user)

        return redirect("login") # change this to your home/dashboard

    return render(request, "main/signup.html")

def edit_profile_page(request):
    return render(request, "main/edit_profile.html")

def profile_page(request):
    skills = ["Python", "Django", "HTML", "CSS"]

    job_database = [
        {"title": "Junior Django Developer", "skill": "Django"},
        {"title": "Frontend Intern", "skill": "HTML"},
        {"title": "Backend Developer", "skill": "Python"},
        {"title": "Web Designer", "skill": "CSS"},
        {"title": "Full Stack Developer", "skill": "Python"},
    ]

    suggestions = [job for job in job_database if job["skill"] in skills]

    return render(request, "main/profile.html", {
        "skills": skills,
        "job_suggestions": suggestions,
    })

def _messages(request):
    return render(request, "main/messages.html")

