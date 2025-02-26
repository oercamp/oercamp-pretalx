from django.utils.translation import gettext_lazy as _
from pretalx.common.exporter import BaseExporter, CSVExporterMixin

from .models import PublicVote


class PublicVotingCSVExporter(CSVExporterMixin, BaseExporter):
    public = False
    icon = "fa-list"
    identifier = "public_votes.csv"
    cors = "*"

    @property
    def verbose_name(self):
        return _("Public Voting CSV")

    @property
    def filename(self):
        return f"{self.event.slug}-public-votes.csv"

    def get_data(self, **kwargs):
        fieldnames = ["code", "voter", "timestamp", "score", "comment"]
        data = []
        votes = (
            PublicVote.objects.filter(submission__event=self.event)
            .order_by("submission__code")
            .select_related("submission")
        )
        for vote in votes:

            csvScore = vote.score or "NULL"

            data.append(
                {
                    "code": vote.submission.code,
                    "voter": vote.email_hash,
                    "timestamp": vote.timestamp.isoformat(),
                    "score": csvScore,
                    "comment": vote.comment
                }
            )

        return fieldnames, data
