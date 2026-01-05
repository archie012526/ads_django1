from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_merge_0004_job_status_0004_merge_20260105_1513"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="desired_skills",
            field=models.ManyToManyField(blank=True, related_name="desired_by_profiles", to="main.skilltag"),
        ),
    ]
