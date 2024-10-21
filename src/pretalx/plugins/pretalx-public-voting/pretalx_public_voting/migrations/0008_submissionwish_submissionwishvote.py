# Generated by Django 4.2.16 on 2024-10-21 15:24

from django.db import migrations, models
import django.db.models.deletion
import pretalx.common.models.mixins


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0037_event_pretix_api_domain_event_pretix_api_event_slug_and_more"),
        (
            "pretalx_public_voting",
            "0007_publicvote_comment_publicvotingsettings_hide_score_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="SubmissionWish",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated", models.DateTimeField(auto_now=True, null=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submission_wishes",
                        to="event.event",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(
                pretalx.common.models.mixins.LogMixin,
                pretalx.common.models.mixins.FileCleanupMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="SubmissionWishVote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("score", models.IntegerField(default=None, null=True)),
                ("comment", models.TextField(null=True)),
                ("email_hash", models.CharField(max_length=32)),
                ("timestamp", models.DateTimeField(auto_now=True)),
                (
                    "submission_wish",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submissionwish_public_votes",
                        to="pretalx_public_voting.submissionwish",
                    ),
                ),
            ],
            options={
                "unique_together": {("submission_wish", "email_hash")},
            },
        ),
    ]
