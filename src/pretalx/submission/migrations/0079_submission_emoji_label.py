# Generated by Django 4.2.16 on 2024-10-09 10:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submission", "0078_submission_etherpad_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="emoji_label",
            field=models.CharField(default="", max_length=255),
        ),
    ]
