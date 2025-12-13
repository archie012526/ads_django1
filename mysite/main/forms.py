from django import forms
from django.contrib.auth.models import User
from .models import Profile, Skill, Job


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "phone_number", "location", "bio"]


SKILL_CHOICES = [
    ("Communication", "Communication"),
    ("Teamwork", "Teamwork"),
    ("Leadership", "Leadership"),
    ("Problem Solving", "Problem Solving"),
    ("Time Management", "Time Management"),
    ("Critical Thinking", "Critical Thinking"),
    ("HTML", "HTML"),
    ("CSS", "CSS"),
    ("JavaScript", "JavaScript"),
    ("Python", "Python"),
    ("Django", "Django"),
]


class SkillForm(forms.ModelForm):
    name = forms.ChoiceField(
        choices=SKILL_CHOICES,
        widget=forms.Select(attrs={"class": "w-full p-2 border rounded"})
    )

    level = forms.ChoiceField(
        choices=Skill.LEVEL_CHOICES,
        widget=forms.Select(attrs={"class": "w-full p-2 border rounded"})
    )

    class Meta:
        model = Skill
        fields = ["name", "level"]


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "title",
            "company",
            "location",
            "job_type",
            "employment_type",
            "skills",
            "salary",
            "description",
        ]
