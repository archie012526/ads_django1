from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import re
from .models import Profile, Skill, Job, Post, JobApplication, SkillTag


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
            "skills",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "company_name": forms.TextInput(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "textarea"}),
            "location": forms.TextInput(attrs={"class": "input"}),
            "employment_type": forms.Select(attrs={"class": "input"}),
            "working_schedule": forms.Select(attrs={"class": "input"}),
            "skills": forms.SelectMultiple(attrs={"class": "input"}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("content", "post_type", "image", "video", "article_title")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3, "placeholder": "Start a post", "class": "post-input"}),
            "post_type": forms.HiddenInput(),
            "image": forms.FileInput(attrs={"accept": "image/*", "style": "display:none;", "id": "imageInput"}),
            "video": forms.FileInput(attrs={"accept": "video/*", "style": "display:none;", "id": "videoInput"}),
            "article_title": forms.TextInput(attrs={"placeholder": "Article title", "style": "display:none;", "id": "articleTitleInput", "class": "post-input"}),
        }


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ["resume"]
        widgets = {
            "resume": forms.FileInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg",
                "accept": ".pdf,.doc,.docx",
            }),
        }
    

class SignUpForm(UserCreationForm):
    phone_number = forms.CharField()
    role = forms.ChoiceField(
        choices=[
            ('job_seeker', 'Job Seeker (Looking for a job)'),
            ('employer', 'Employer (Hiring employees)')
        ],
        widget=forms.RadioSelect,
        initial='job_seeker'
    )

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

    def clean_password1(self):
        """Enforce password policy: min 8 chars, at least one uppercase, one digit, and one symbol."""
        password = self.cleaned_data.get("password1") or ""
        if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"\d", password) or not re.search(r"[^A-Za-z0-9]", password):
            raise forms.ValidationError("Password must be at least 8 characters and include at least one uppercase letter, one number, and one symbol.")
        return password


class JobPostForm(forms.ModelForm):
    # This allows employers to select multiple skills
    skills = forms.ModelMultipleChoiceField(
        queryset=SkillTag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Job
        fields = ['title', 'company_name', 'description', 'location', 'employment_type', 'working_schedule', 'skills']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe the role...'}),
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Senior Python Developer'}),
        }