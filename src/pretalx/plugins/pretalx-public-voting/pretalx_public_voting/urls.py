from django.urls import re_path
from pretalx.event.models.event import SLUG_REGEX

from . import views

urlpatterns = [
    re_path(
        rf"^orga/event/(?P<event>{SLUG_REGEX})/settings/p/public_voting/$",
        views.PublicVotingSettingsView.as_view(),
        name="settings",
    ),
    re_path(
        f"^(?P<event>{SLUG_REGEX})/p/voting/signup/$",
        views.SignupView.as_view(),
        name="signup",
    ),
    re_path(
        f"^(?P<event>{SLUG_REGEX})/p/voting/thanks/$",
        views.ThanksView.as_view(),
        name="thanks",
    ),
    re_path(
        f"^(?P<event>{SLUG_REGEX})/p/voting/talks/(?P<signed_user>[^/]+)/$",
        views.SubmissionListView.as_view(),
        name="talks",
    ),
    re_path(
        f"^(?P<event>{SLUG_REGEX})/p/voting/public/talks/$",
        views.PublicSubmissionListView.as_view(),
        name="public_talks",
    ),
    re_path(
        f"^(?P<event>{SLUG_REGEX})/p/voting/wishes/(?P<signed_user>[^/]+)/$",
        views.SubmissionWishListView.as_view(),
        name="wishes",
    ),
    re_path(
        f"^(?P<event>{SLUG_REGEX})/p/voting/public/wishes/$",
        views.PublicSubmissionWishListView.as_view(),
        name="public_wishes",
    ),
    re_path(
        f"^(?P<event>{SLUG_REGEX})/p/voting/talks/delete/(?P<submission_key>[0-9]+)/$",
        views.PublicSubmissionDelete.as_view(),
        name="submission_comment_delete",
    ),
    re_path(
        f"^(?P<event>{SLUG_REGEX})/p/voting/wishes/delete/(?P<submission_key>[0-9]+)/$",
        views.PublicSubmissionWishDelete.as_view(),
        name="submissionwish_comment_delete",
    )
]
