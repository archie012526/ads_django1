from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Skill, Job, Post


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "phone_number", "location", "bio", "profile_image"]


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "phone_number",
            "profile_image",
            "bio",
            "profile_visibility",
            "allow_contact",
            "email_notifications",
            "push_notifications",
            "preferred_job_titles",
            "job_categories",
            "employment_type",
            "preferred_location",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
        }


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
            "company_name",
            "description",
            "location",
            "employment_type",
            "working_schedule",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "company_name": forms.TextInput(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "textarea"}),
            "location": forms.TextInput(attrs={"class": "input"}),
            "employment_type": forms.Select(attrs={"class": "input"}),
            "working_schedule": forms.Select(attrs={"class": "input"}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3, "placeholder": "Start a post"}),
        }
    

class SignUpForm(UserCreationForm):
    phone_number = forms.CharField()

    class Meta:
        model = User
        fields = ("username", "email", "phone_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Enter username"
        })

        self.fields["email"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Enter email"
        })

        self.fields["phone_number"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Enter phone number"
        })

        self.fields["password1"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Enter password"
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Confirm password"
        })
