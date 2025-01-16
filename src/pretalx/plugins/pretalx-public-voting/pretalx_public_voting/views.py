import random

from django.contrib import messages
from django.db.models import Case, OuterRef, Subquery, When
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from django.views.generic import DeleteView
from django_context_decorator import context
from pretalx.common.views.mixins import PermissionRequired
from pretalx.submission.models import Submission, SubmissionStates

from .exporters import PublicVotingCSVExporter
from .forms import PublicVotingSettingsForm, SignupForm, VoteForm, SubmissionWishVoteForm
from .models import PublicVote, PublicVotingSettings, SubmissionWish, SubmissionWishVote
from .utils import event_unsign


class PublicVotingRequired:
    def dispatch(self, request, *args, **kwargs):
        start = request.event.public_vote_settings.start
        end = request.event.public_vote_settings.end
        _now = now()
        start_valid = (not start) or _now > start
        end_valid = (not end) or _now < end
        if not start_valid or not end_valid:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)


class SignupView(PublicVotingRequired, FormView):
    template_name = "pretalx_public_voting/signup.html"
    form_class = SignupForm

    def get_success_url(self):
        return reverse("plugins:pretalx_public_voting:thanks", kwargs=self.kwargs)

    def get_form_kwargs(self):
        result = super().get_form_kwargs()
        result["event"] = self.request.event
        return result

    def form_valid(self, form):
        form.send_email()
        return super().form_valid(form)


class ThanksView(PublicVotingRequired, TemplateView):
    template_name = "pretalx_public_voting/thanks.html"


class SubmissionListView(PublicVotingRequired, ListView):
    model = Submission
    template_name = "pretalx_public_voting/submission_list.html"
    paginate_by = 20
    context_object_name = "submissions"

    @context
    @cached_property
    def hashed_email(self):
        return event_unsign(self.kwargs["signed_user"], self.request.event)

    def get_queryset(self):
        if not self.hashed_email:
            # If the use wasn't valid, there is no point of returning a
            # QuerySet with the talks
            return None

        votes = PublicVote.objects.filter(
            email_hash=self.hashed_email, submission_id=OuterRef("pk")
        ).values("score")

        #TODO: do we need this? get_context_data is fetching the comments later on
        comments = PublicVote.objects.filter(
            email_hash=self.hashed_email, submission_id=OuterRef("pk")
        ).values("comment")

        # Idea is from https://stackoverflow.com/questions/4916851/django-get-a-queryset-from-array-of-ids-in-specific-order/37648265#37648265
        base_qs = self.request.event.submissions.all().filter(
            state=SubmissionStates.SUBMITTED
        )
        tracks = self.request.event.public_vote_settings.limit_tracks.all()
        if tracks:
            base_qs = base_qs.filter(track__in=tracks)
        submission_pks = list(base_qs.values_list("pk", flat=True))
        random.seed(self.hashed_email)
        random.shuffle(submission_pks)
        user_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(submission_pks)]
        )

        return (
            base_qs.annotate(
                score=Subquery(votes),
                comment=Subquery(comments)
            )
            .prefetch_related("speakers")
            .order_by(user_order)
        )

    def get_form_for_submission(self, submission):
        if self.request.method == "POST":
            return VoteForm(
                data=self.request.POST,
                submission=submission,
                hashed_email=self.hashed_email,
                require_score=False, #was True originally
                initial={"score": submission.score, "comment": submission.comment},
                event=self.request.event,
                prefix=submission.code,
            )
        return VoteForm(
            initial={"score": submission.score, "comment": submission.comment},
            event=self.request.event,
            prefix=submission.code,
        )

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        for submission in result["submissions"]:
            submission.vote_form = self.get_form_for_submission(submission)
            submission.comments = (
                submission.public_votes
                .exclude(comment='')
                .exclude(comment__isnull=True)
                .exclude(comment__regex=r'^\s*$')
                .exclude(email_hash=self.hashed_email)
                .order_by('timestamp')
                .values_list("comment", flat=True)
            )
        return result

    def post(self, request, *args, **kwargs):
        submissions = {
            submission.code: submission for submission in self.get_queryset()
        }
        for key in self.request.POST.keys():
            if "score" not in key and "comment" not in key:
                continue
            prefix, __ = key.split("-", maxsplit=1)
            submission = submissions.get(prefix)
            if not submission:
                continue
            form = self.get_form_for_submission(submission)
            if form.is_valid():
                # Only save the form if the score has changed
                # if form.initial["score"] != form.cleaned_data["score"]:
                form.save()
        if request.POST.get("action") == "manual":
            messages.success(self.request, _("Thank you for your vote!"))
            return redirect(self.request.path)
        return JsonResponse({})


class PublicVotingSettingsView(PermissionRequired, FormView):
    form_class = PublicVotingSettingsForm
    permission_required = "orga.change_settings"
    template_name = "pretalx_public_voting/settings.html"

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_object(self):
        return self.request.event

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        settings, _ = PublicVotingSettings.objects.get_or_create(
            event=self.request.event
        )
        return {
            "instance": settings,
            "locales": self.request.event.locales,
            **kwargs,
        }

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result["export_url"] = PublicVotingCSVExporter(
            self.request.event
        ).urls.base.full()
        return result

class PublicSubmissionListView(ListView):
    model = Submission
    template_name = "pretalx_public_voting/public_submission_list.html"
    paginate_by = 20
    context_object_name = "submissions"

    def get_queryset(self):
        # NOVA: Check if Plugin activated
        if not hasattr(self.request.event, "public_vote_settings") or not self.request.event.public_vote_settings:
            return [] #raise Http404()

        # Idea is from https://stackoverflow.com/questions/4916851/django-get-a-queryset-from-array-of-ids-in-specific-order/37648265#37648265
        base_qs = self.request.event.submissions.all().filter(
            state=SubmissionStates.SUBMITTED
        )

        tracks = self.request.event.public_vote_settings.limit_tracks.all()
        if tracks:
            base_qs = base_qs.filter(track__in=tracks)
        submission_pks = list(base_qs.values_list("pk", flat=True))
        user_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(submission_pks)]
        )

        return (
            base_qs
            .prefetch_related("speakers")
            .order_by(user_order)
        )

    def get_context_data(self, **kwargs):
         # NOVA: Check if Plugin activated
         # This is a temp solution. Better hide lnks to this page and raise a 404 if accessed (See line 202)
        if not hasattr(self.request.event, "public_vote_settings") or not self.request.event.public_vote_settings:
            result = {}
            result["plugin_deactivated"] = True
            return result


        result = super().get_context_data(**kwargs)
        for submission in result["submissions"]:
            submission.comments = (
                submission.public_votes
                .exclude(comment='')
                .exclude(comment__isnull=True)
                .exclude(comment__regex=r'^\s*$')
                .order_by('timestamp')
                .values('id', 'comment')
            )
        return result


class SubmissionWishListView(PublicVotingRequired, ListView):
    model = SubmissionWish
    template_name = "pretalx_public_voting/submission_wish_list.html"
    paginate_by = 20
    context_object_name = "submission_wishes"

    @context
    @cached_property
    def hashed_email(self):
        return event_unsign(self.kwargs["signed_user"], self.request.event)

    def get_queryset(self):
        if not self.hashed_email:
            # If the use wasn't valid, there is no point of returning a
            # QuerySet with the talks
            return None

        votes = SubmissionWishVote.objects.filter(
            email_hash=self.hashed_email, submission_wish_id=OuterRef("pk")
        ).values("score")

        #TODO: do we need this? get_context_data is fetching the comments later on
        comments = SubmissionWishVote.objects.filter(
            email_hash=self.hashed_email, submission_wish_id=OuterRef("pk")
        ).values("comment")

        # Idea is from https://stackoverflow.com/questions/4916851/django-get-a-queryset-from-array-of-ids-in-specific-order/37648265#37648265
        base_qs = self.request.event.submission_wishes.all()

        return (
            base_qs.annotate(
                score=Subquery(votes),
                comment=Subquery(comments)
            )
        )

    def get_form_for_submission_wish(self, submissionwish):
        if self.request.method == "POST":
            return SubmissionWishVoteForm(
                data=self.request.POST,
                submission_wish=submissionwish,
                hashed_email=self.hashed_email,
                require_score=False, #was True originally
                initial={"score": submissionwish.score, "comment": submissionwish.comment},
                event=self.request.event,
                prefix=submissionwish.name,
            )
        return SubmissionWishVoteForm(
            initial={"score": submissionwish.score, "comment": submissionwish.comment},
            event=self.request.event,
            prefix=submissionwish.name,
        )

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        for submissionwish in result["submission_wishes"]:
            submissionwish.vote_form = self.get_form_for_submission_wish(submissionwish)
            submissionwish.comments = (
                submissionwish.submissionwish_public_votes
                .exclude(comment='')
                .exclude(comment__isnull=True)
                .exclude(comment__regex=r'^\s*$')
                .exclude(email_hash=self.hashed_email)
                .order_by('timestamp')
                .values_list("comment", flat=True)
            )
        return result

    def post(self, request, *args, **kwargs):
        submission_wishes = {
            submissionwish.name: submissionwish for submissionwish in self.get_queryset()
        }
        for key in self.request.POST.keys():
            if "score" not in key and "comment" not in key:
                continue
            prefix, __ = key.split("-", maxsplit=1)
            submissionwish = submission_wishes.get(prefix)
            if not submissionwish:
                continue
            form = self.get_form_for_submission_wish(submissionwish)
            if form.is_valid():
                # Only save the form if the score has changed
                # if form.initial["score"] != form.cleaned_data["score"]:
                form.save()
        if request.POST.get("action") == "manual":
            messages.success(self.request, _("Thank you for your vote!"))
            return redirect(self.request.path)
        return JsonResponse({})


class PublicSubmissionWishListView(ListView):
    model = SubmissionWish
    template_name = "pretalx_public_voting/public_submissionwish_list.html"
    paginate_by = 20
    context_object_name = "submission_wishes"

    def get_queryset(self):
        # NOVA: Check if Plugin activated
        if not hasattr(self.request.event, "public_vote_settings") or not self.request.event.public_vote_settings:
            return [] #raise Http404()
        return self.request.event.submission_wishes.all()

    def get_context_data(self, **kwargs):
        # NOVA: Check if Plugin activated
        # This is a temp solution. Better hide links to this page and raise a 404 if accessed (See line 343)
        if not hasattr(self.request.event, "public_vote_settings") or not self.request.event.public_vote_settings:
            result = {}
            result["plugin_deactivated"] = True
            return result

        result = super().get_context_data(**kwargs)
        for submissionwish in result["submission_wishes"]:
            submissionwish.comments = (
                submissionwish.submissionwish_public_votes
                .exclude(comment='')
                .exclude(comment__isnull=True)
                .exclude(comment__regex=r'^\s*$')
                .order_by('timestamp')
                .values('id', 'comment')
            )
        return result

###
# This function will delete the whole database vote entry, including the score/voting.
# This is not the right way. Better would be to delete only the comment, i.e. make the comment= ''.
# But because the score voting is not used anyway right-now, we will keep this as it is.
###
class PublicSubmissionDelete(DeleteView):
    model = PublicVote
    pk_url_kwarg = 'submission_key'
    permission_required = "person.is_administrator"

    def get(self, request, *args, **kwargs):
        # Instead of rendering a confirmation page, immediately redirect to success URL
        return self.post(request, *args, **kwargs)

    def get_success_url(self):
        #return self.request.path
        # Use the HTTP_REFERER to redirect back to the previous page
        referer_url = self.request.META.get('HTTP_REFERER', '/')
        return referer_url

###
# This function will delete the whole database vote entry, including the score/voting.
# This is not the right way. Better would be to delete only the comment, i.e. make the comment= ''.
# But because the score-voting is not used anyway right now, we will keep this as it is.
###
class PublicSubmissionWishDelete(DeleteView):
    model = SubmissionWishVote
    pk_url_kwarg = 'submission_key'
    permission_required = "person.is_administrator"

    def get(self, request, *args, **kwargs):
        # Instead of rendering a confirmation page, immediately redirect to success URL
        return self.post(request, *args, **kwargs)

    def get_success_url(self):
        #return self.request.path
        # Use the HTTP_REFERER to redirect back to the previous page
        referer_url = self.request.META.get('HTTP_REFERER', '/')
        return referer_url
