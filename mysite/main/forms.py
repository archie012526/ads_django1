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

SKILL_OPTIONS = [
    ("Communication", "Communication"),
    ("Teamwork", "Teamwork"),
    ("Leadership", "Leadership"),
    ("Problem Solving", "Problem Solving"),
    ("Time Management", "Time Management"),
    ("Critical Thinking", "Critical Thinking"),

    ("Customer Service", "Customer Service"),
    ("Sales", "Sales"),
    ("Marketing", "Marketing"),
    ("Negotiation", "Negotiation"),

    ("Project Management", "Project Management"),
    ("Data Entry", "Data Entry"),
    ("Typing", "Typing"),
    ("Computer Literacy", "Computer Literacy"),

    ("Creativity", "Creativity"),
    ("Public Speaking", "Public Speaking"),
    ("Writing", "Writing"),
    ("Research", "Research"),
    ("Organizational Skills", "Organizational Skills"),

    ("HTML", "HTML"),
    ("CSS", "CSS"),
    ("JavaScript", "JavaScript"),
    ("Python", "Python"),
    ("Django", "Django"),
    ("Database Management", "Database Management"),

    ("Patient Care", "Patient Care"),
    ("Medical Terminology", "Medical Terminology"),

    ("Food Preparation", "Food Preparation"),
    ("Housekeeping", "Housekeeping"),

    ("Welding", "Welding"),
    ("Carpentry", "Carpentry"),
    ("Electrical Work", "Electrical Work"),

    ("Budgeting", "Budgeting"),
    ("Bookkeeping", "Bookkeeping"),
]

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name", "level", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "input",
                "list": "skill-options",  # key for datalist autocomplete
                "placeholder": "Type a skill"
            }),
            "level": forms.Select(choices=Skill.LEVEL_CHOICES, attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "input"}),
        }