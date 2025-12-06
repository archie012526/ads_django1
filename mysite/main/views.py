from django.shortcuts import render

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
