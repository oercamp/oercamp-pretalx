import requests
from django.http import JsonResponse
from django.utils.functional import cached_property

import io
from collections import defaultdict
from urllib.parse import urlparse

import vobject
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import Storage
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect

from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView, TemplateView
from django_context_decorator import context

from pretalx.common.text.path import safe_filename
from pretalx.common.views.mixins import (
    EventPermissionRequired,
    Filterable,
    PermissionRequired,
    SocialMediaCardMixin,
)



class ParticipantsList(EventPermissionRequired, ListView):
    context_object_name = "attendees"
    template_name = "agenda/participants.html"
    permission_required = "agenda.view_schedule"

    @context
    def isPretixParticipantsApiConfigured(self):
        if self.request.event.pretix_api_key and self.request.event.pretix_api_organisator_slug and self.request.event.pretix_api_event_slug and self.request.event.pretix_identifier_question_participant_list:
            return True
        else:
            return False

    @cached_property
    def attendees(self):
        url = f"https://{self.request.event.pretix_api_domain}/api/v1/organizers/{self.request.event.pretix_api_organisator_slug}/events/{self.request.event.pretix_api_event_slug}/orders/"
        headers = {
            'Authorization': f"Token {self.request.event.pretix_api_key}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {'error': 'Failed to fetch data'}

        data = response.json()  # Parse the JSON response

        # Initialize an empty list to store attendee emails
        attendee_names = []

        # Iterate through each result in the results list
        for result in data['results']:
            # Check if the status is 'p' (= paid)
            if result['status'] == 'p':
                # Iterate through each position in the positions list
                for position in result['positions']:
                    # Check if attendee_email is set
                    if position['attendee_name']:
                        # Iterate through the answers list
                        for answer in position.get('answers', []):
                            # Check if question_identifier is 'allow_participant_list' and answer is 'True'
                            if answer.get('question_identifier') == event.pretix_identifier_question_participant_list and answer.get('answer') == 'True':
                                # Add attendee_email to the result array
                                attendee_names.append(position['attendee_name'])

        #return JsonResponse(data)  # Return the data as a response to the client
        return attendee_names

    def get_queryset(self):
        return self.attendees
