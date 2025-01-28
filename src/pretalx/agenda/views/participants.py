import requests
import logging
from django.core.cache import cache
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
    def is_pretix_participants_api_configured(self):
        return self.request.event.is_pretix_api_participants_configured

    @cached_property
    def attendees(self):

        cache_key = f"attendees_{self.request.event.id}"
        cached_sorted_attendee_data_list = cache.get(cache_key)
        if cached_sorted_attendee_data_list is not None:
            return cached_sorted_attendee_data_list

        url = f"https://{self.request.event.pretix_api_domain}/api/v1/organizers/{self.request.event.pretix_api_organisator_slug}/events/{self.request.event.pretix_api_event_slug}/orders/"
        headers = {
            'Authorization': f"Token {self.request.event.pretix_api_key}"
        }

        attendee_data_list = []

        while url:  # Continue looping as long as there's a next URL
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return {'error': 'Failed to fetch data'}

            data = response.json()  # Parse the JSON response

            # Iterate through each result in the results list
            for result in data['results']:
                # Check if the status is 'p' (= paid)
                if result['status'] == 'p':
                    # Iterate through each position in the positions list
                    for position in result['positions']:

                        # First loop: Check if participant is allowed to be added
                        participant_list_answer = 'Nein'
                        for answer in position.get('answers', []):
                            if answer.get('question_identifier') == self.request.event.pretix_identifier_question_participant_list:
                                participant_list_answer = answer.get('answer')
                                break

                        if participant_list_answer == 'Nein':
                            continue

                        attendee_data = {
                            'given_name': None,
                            'last_name': None,
                            'email': position['attendee_email'],
                            'organisation': None,
                            'postcode': None,
                            'city': None,
                            'country': None
                        }

                        if participant_list_answer == 'Ja': # Take original Data
                            if position.get('attendee_name_parts'):
                                attendee_data['given_name'] = position['attendee_name_parts'].get('given_name')
                                attendee_data['last_name'] = position['attendee_name_parts'].get('family_name')
                            # Second loop: get participant data
                            for answer in position.get('answers', []):
                                if answer.get('answer'): # we overwrite only existing fields if there is actual data in the answer field
                                    if answer.get('question_identifier') == self.request.event.pretix_qid_organisation:
                                        attendee_data['organisation'] = answer.get('answer')
                                    elif answer.get('question_identifier') == self.request.event.pretix_qid_postcode:
                                        attendee_data['postcode'] = answer.get('answer')
                                    elif answer.get('question_identifier') == self.request.event.pretix_qid_city:
                                        attendee_data['city'] = answer.get('answer')
                                    elif answer.get('question_identifier') == self.request.event.pretix_qid_country:
                                        attendee_data['country'] = answer.get('answer')
                        else: # This is for answer = "Ja, aber mit abweichenden Daten...."
                            for answer in position.get('answers', []):
                                if answer.get('answer'): # we overwrite only existing fields if there is actual data in the answer field
                                    if answer.get('question_identifier') == self.request.event.pretix_qid_participant_list_firstname:
                                        attendee_data['given_name'] = answer.get('answer')
                                    elif answer.get('question_identifier') == self.request.event.pretix_qid_participant_list_lastname:
                                        attendee_data['last_name'] = answer.get('answer')
                                    elif answer.get('question_identifier') == self.request.event.pretix_qid_participant_list_email:
                                        attendee_data['email'] = answer.get('answer')
                                    elif answer.get('question_identifier') == self.request.event.pretix_qid_participant_list_postcode:
                                        attendee_data['postcode'] = answer.get('answer')
                                    elif answer.get('question_identifier') == self.request.event.pretix_qid_participant_list_city:
                                        attendee_data['city'] = answer.get('answer')
                                    elif answer.get('question_identifier') == self.request.event.pretix_qid_country:
                                        attendee_data['country'] = answer.get('answer')


                        # Add the fully processed participant data to the list
                        # Check if both given_name and family_name are provided before appending,
                        # because these are the minimal requirements to display the name
                        if attendee_data['given_name'] and attendee_data['last_name']:
                            attendee_data_list.append(attendee_data)

            # Get the URL for the next page, if any
            url = data.get('next')

        # make alphabetical
        sorted_attendee_data_list = sorted(attendee_data_list, key=lambda x: (x['last_name'], x['given_name']))

        # Cache the data for a specified duration
        cache.set(cache_key, sorted_attendee_data_list, timeout=600)  # cached for 10 minutes - 3600 - Cache for 1 hour

        #return JsonResponse(data)  # Return the data as a response to the client
        return sorted_attendee_data_list

    def get_queryset(self):
        return self.attendees
