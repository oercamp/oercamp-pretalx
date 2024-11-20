from django.db import models
from django.utils.translation import gettext_lazy as _


class YouTubeLink(models.Model):
    submission = models.OneToOneField(
        to="submission.Submission",
        on_delete=models.CASCADE,
        related_name="youtube_link",
    )
    video_id = models.CharField(max_length=20)

    @property
    def player_link(self):
        return f"https://www.youtube-nocookie.com/embed/{self.video_id}"

    @property
    def youtube_link(self):
        return f"https://youtube.com/watch?v={self.video_id}"

    @property
    def iframe(self):
        alternate_text = _('Please <a href="javascript:Cookiebot.renew()">accept marketing-cookies</a> to watch this video.')
        return f'<div class="embed-responsive embed-responsive-16by9 d-flex align-items-center justify-content-center"><iframe src="{self.player_link}" frameborder="0" allowfullscreen></iframe><p class="cookieconsent-optout-marketing">{alternate_text}<p></div>'
