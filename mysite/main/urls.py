from django.urls import path
from . import views

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path('landingpage/', views.landingPage, name='landingpage'),
    path('jobs/', views.jobs_page, name='jobs'),
    path('about/', views.about_page, name='about'),
    path('login/', views.login_page, name='login'),
]
