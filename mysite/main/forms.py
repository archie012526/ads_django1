from django import forms
from django.contrib.auth.models import User
from .models import Profile

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'full_name',
            'phone_number',
            'location',
            'bio',
            'company_name',
            'role',
            'image',   # <-- correct name (NOT profile_picture)
        ]

