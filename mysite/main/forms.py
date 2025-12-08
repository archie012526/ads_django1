from django import forms
from django.contrib.auth.models import User
from .models import Profile
from .models import Skill

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
class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input-field", "placeholder": "Enter a skill"}),   }
