from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Profile

SAMPLES = [
    {
        "username": "tech_innovations",
        "email": "hr@techinnovations.example.com",
        "full_name": "Tech Innovations HR",
        "company_name": "Tech Innovations",
        "bio": "Building next-gen SaaS platforms and cloud integrations.",
        "location": "San Francisco, CA",
    },
    {
        "username": "bluriver_careers",
        "email": "careers@bluriver.example.com",
        "full_name": "BlueRiver Careers",
        "company_name": "BlueRiver",
        "bio": "Data-driven fintech solutions for modern banking.",
        "location": "New York, NY",
    },
    {
        "username": "northwind_studio",
        "email": "jobs@northwindstudio.example.com",
        "full_name": "Northwind Studio",
        "company_name": "Northwind Studio",
        "bio": "Design and product studio crafting delightful experiences.",
        "location": "Austin, TX",
    },
    {
        "username": "pixel_creative",
        "email": "talent@pixelcreative.example.com",
        "full_name": "Pixel Creative",
        "company_name": "Pixel Creative",
        "bio": "Creative agency specializing in branding and web.",
        "location": "Remote",
    },
    {
        "username": "cloudforge_tech",
        "email": "hiring@cloudforge.example.com",
        "full_name": "CloudForge Tech",
        "company_name": "CloudForge Tech",
        "bio": "DevOps tooling and cloud automation at scale.",
        "location": "Seattle, WA",
    },
]

DEFAULT_PASSWORD = "SamplePass123!"

class Command(BaseCommand):
    help = "Seed sample employer accounts (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=len(SAMPLES), help="Number of employers to create (max {}).".format(len(SAMPLES)))
        parser.add_argument("--password", type=str, default=DEFAULT_PASSWORD, help="Password for created users")

    def handle(self, *args, **options):
        count = max(0, min(options["count"], len(SAMPLES)))
        password = options["password"]

        created = 0
        updated = 0

        for data in SAMPLES[:count]:
            username = data["username"]
            email = data["email"]
            user, was_created = User.objects.get_or_create(
                username=username,
                defaults={"email": email}
            )
            if was_created:
                user.set_password(password)
                user.is_staff = False
                user.is_superuser = False
                user.save()
                created += 1
            else:
                updated += 1

            # Ensure profile exists and set employer fields
            profile: Profile = user.profile  # created via signal
            profile.role = "employer"
            profile.full_name = data.get("full_name")
            profile.company_name = data.get("company_name")
            profile.bio = data.get("bio")
            profile.location = data.get("location")
            profile.save()

        self.stdout.write(self.style.SUCCESS(
            f"Seeded employers: created={created}, updated={updated}, password='{password}'"
        ))
