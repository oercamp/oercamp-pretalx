# Generated by Django 4.2.16 on 2024-11-13 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0041_event_pretix_qid_country"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="venueless_domain",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="venueless_embed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="event",
            name="venueless_secret",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
