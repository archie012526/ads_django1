from django import forms
from django.contrib.auth.models import User
from .models import Profile, Skill

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "input"}),
            "first_name": forms.TextInput(attrs={"class": "input"}),
            "last_name": forms.TextInput(attrs={"class": "input"}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "phone_number", "location", "bio"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "input-field"}),
            "phone_number": forms.TextInput(attrs={"class": "input-field"}),
            "location": forms.TextInput(attrs={"class": "input-field"}),
            "bio": forms.Textarea(attrs={"class": "input-field h-24 resize-none"}),
        }

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name", "level", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "level": forms.TextInput(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "input"}),
        }