import requests
from django.http import JsonResponse


import io
from collections import defaultdict
from urllib.parse import urlparse

import vobject
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import Storage
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect
from django.utils.functional import cached_property
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
from pretalx.person.models import SpeakerProfile, User
from pretalx.submission.models import QuestionTarget



class ParticipantsList(EventPermissionRequired, Filterable, ListView):
    context_object_name = "participants"
    template_name = "agenda/participants.html"
    permission_required = "agenda.view_schedule"

    @context
    def isPretixParticipantsApiConfigured(self):
        if self.request.event.pretix_api_key and self.request.event.pretix_identifier_question_participant_list:
            return True
        else:
            return False

    @context
    def participantsApiResponse(self):
        url = 'https://pretix.oercamp.de/api/v1/organizers/nova-origanisator/events/nova-test-event/orders/'
        headers = {
            'Authorization': f"Token {self.request.event.pretix_api_key}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()  # Parse the JSON response
            #return JsonResponse(data)  # Return the data as a response to the client
        else:
            return {'error': 'Failed to fetch data'}


    def get_queryset(self):
        return ['eins', 'zwei']
