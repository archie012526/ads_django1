from django.shortcuts import render

def homepage(request):
    return render(request, 'main/home.html')

def landingPage(request):
    return render(request, 'main/landing.html')

def jobs_page(request):
    return render(request, 'main/jobs.html')

def about_page(request):
    return render(request, 'main/about.html')

def login_page(request):
    return render(request, 'main/login.html')
