import requests
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import TemplateView
from django_context_decorator import context

from pretalx.common.views.mixins import PermissionRequired
from pretalx.event.models import Event

from django.utils.functional import cached_property
import logging

from django_scopes import scope

class EventPageMixin(PermissionRequired):
    permission_required = "cfp.view_event"

    def get_permission_object(self):
        return getattr(self.request, "event", None)


# check login first, then permission so users get redirected to /login, if they are missing one
class LoggedInEventPageMixin(LoginRequiredMixin, EventPageMixin):
    def get_login_url(self) -> str:
        return reverse("cfp:event.login", kwargs={"event": self.request.event.slug})


class EventStartpage(EventPageMixin, TemplateView):
    template_name = "cfp/event/index.html"

    @context
    def has_submissions(self):
        return (
            not self.request.user.is_anonymous
            and self.request.event.submissions.filter(
                speakers__in=[self.request.user]
            ).exists()
        )

    @context
    def has_featured(self):
        return self.request.event.submissions.filter(is_featured=True).exists()

    @context
    def submit_qs(self):
        params = [
            (key, self.request.GET.get(key))
            for key in ("track", "submission_type", "access_code")
            if self.request.GET.get(key) is not None
        ]
        #NOVA: adding param so login-mask redirects to submit page
        if (self.request.user.is_anonymous):
            params.append(("next", "submit"))

        return f"?{urlencode(params)}" if params else ""

    # We will redirect to login if user is anonymous.
    # The submit_qs function will contain "next=submit" to redirect back.
    @context
    def submit_url(self):
        if (self.request.user.is_anonymous):
            return self.request.event.urls.login
        return self.request.event.urls.submit

    @context
    def access_code(self):
        code = self.request.GET.get("access_code")
        if code:
            return self.request.event.submitter_access_codes.filter(
                code__iexact=code
            ).first()


class EventCfP(EventStartpage):
    template_name = "cfp/event/cfp.html"

    @context
    def has_featured(self):
        return self.request.event.submissions.filter(is_featured=True).exists()


class GeneralView(TemplateView):
    template_name = "cfp/index.html"

    def filter_events(self, events):
        if self.request.user.is_anonymous:
            events.filter(is_public=True)
        return [
            event
            for event in events
            if event.is_public or self.request.user.has_perm("cfp.view_event", event)
        ]

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        _now = now().date()
        qs = Event.objects.order_by("-date_to")

        # To improve performance, we could exclude past events.
        result["registered_events"] = [
            {
              "event": event,
              "current_schedule": None,
            }
            for event in self.get_pretix_ordered_events(self.filter_events(qs))
        ]
        for item in result["registered_events"]:
            event = item["event"]
            with scope(event=event):  # Use the appropriate scope context manager
                item["current_schedule"] = event.current_schedule  # Access current_schedule within scope


        result["current_events"] = [
            {
                "event": event,
                "current_schedule": None
            }
            for event in self.filter_events(qs.filter(date_from__lte=_now, date_to__gte=_now))
            if event not in result["registered_events"]
        ]
        for item in result["current_events"]:
            event = item["event"]
            with scope(event=event):  # Use the appropriate scope context manager
                item["current_schedule"] = event.current_schedule  # Access current_schedule within scope

        result["past_events"] = [
            {
                "event": event,
                "current_schedule": None
            }
            for event in self.filter_events(qs.filter(date_to__lt=_now))
        ]
        for item in result["past_events"]:
            event = item["event"]
            with scope(event=event):  # Use the appropriate scope context manager
                item["current_schedule"] = event.current_schedule  # Access current_schedule within scope

        result["future_events"] = [
            {
                "event": event,
                "current_schedule": None
            }
            for event in self.filter_events(qs.filter(date_from__gt=_now))
            if event not in result["registered_events"]
        ]
        for item in result["future_events"]:
            event = item["event"]
            with scope(event=event):  # Use the appropriate scope context manager
                item["current_schedule"] = event.current_schedule  # Access current_schedule within scope

        # We will use the first event with pretix data to load the widget javascript and css from.
        result["widget_event"] = next(
            (
                event for events in [
                    result["registered_events"],
                    result["current_events"],
                    result["future_events"],
                    result["past_events"]
                ] if events
                for event in events
                if event.pretix_ticket_shop_link and event.pretix_ticket_shop_base_url
            ),
            None
        )

        return result

    def get_pretix_ordered_events(self, events):

        if (
            self.request.user.is_anonymous or
            not self.request.user.email
        ):
            return []

        user_email = self.request.user.email

        registered_events = set()

        for event in events:
            if not event.is_pretix_api_configured:
                break

            ###
            # We have this call around three times now, we should make a helper function
            ###
            url = f"https://{event.pretix_api_domain}/api/v1/organizers/{event.pretix_api_organisator_slug}/events/{event.pretix_api_event_slug}/orders/"
            headers = {
                'Authorization': f"Token {event.pretix_api_key}"
            }

            ticket_found = False

            while url and not ticket_found:
                response = requests.get(url, headers=headers)

                if response.status_code != 200:
                    return []; #{'error': 'Failed to fetch data'}

                data = response.json()  # Parse the JSON response

                # For this particular event we will search by the order-email instead of attendee_email
                if (event.pretix_api_event_slug == '24essen'):

                    # Iterate through each result in the results list
                    for result in data['results']:
                        # Check if the status is 'p' (= paid)
                        if result['status'] == 'p' and result['email'] == user_email:
                            registered_events.add(event)
                            ticket_found = True
                            break

                else:

                    for result in data['results']:
                        # Check if the status is 'p' (= paid)
                        if result['status'] == 'p':
                            # Iterate through each position in the positions list
                            for position in result['positions']:
                                # Check if attendee_email is set
                                if position.get('attendee_email') == user_email:
                                    registered_events.add(event)
                                    ticket_found = True
                                    break

                # Get the URL for the next page, if any
                url = data.get('next')


        return registered_events
