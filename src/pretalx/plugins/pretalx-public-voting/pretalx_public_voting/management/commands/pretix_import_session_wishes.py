from django.core.management.base import BaseCommand
import requests
from django.http import JsonResponse

from pretalx.event.models import Event
from pretalx_public_voting.models import SubmissionWish
from django_scopes import scopes_disabled

class Command(BaseCommand):
    help = 'Imports submission wishes from the pretix API'

    @scopes_disabled()
    def handle(self, *args, **kwargs):

        events = Event.objects.all()

        for event in events:
            if (not event.is_pretix_api_session_wishes_configured):
                self.stdout.write(
                    self.style.WARNING(f"Pretix API is not configured for event [{event.id} - {event.slug}]. Skipping.")
                )
                continue

            self.stdout.write(
                self.style.SUCCESS(f"Processing event [{event.id} - {event.slug}]:")
            )

            loaded_unique_submission_wishes = self.getUniqueSubmissionWishes(event)
            if 'error' in loaded_unique_submission_wishes and loaded_unique_submission_wishes['error']:
                self.stdout.write(
                    self.style.ERROR(f"Pretix API did not return a 200 response. Error Message: {loaded_unique_submission_wishes['error']}")
                )

            if len(loaded_unique_submission_wishes) == 0:
                self.stdout.write(
                    self.style.WARNING("No pretix submission wishes found. Skipping")
                )
                continue
            else:
                self.stdout.write(
                    self.style.WARNING(f"{len(loaded_unique_submission_wishes)} pretix submission wishes found.")
                )

            existing_submission_wishes = SubmissionWish.objects.filter(event=event)
            self.stdout.write(
                self.style.WARNING(f"{len(existing_submission_wishes)} already imported submission wishes found.")
            )

            MAX_NAME_LENGTH = 255
            # Create a set of existing names for quick lookup
            # Existing DB entries for this event, normalized for comparison
            existing_names_lookup = {wish.name.strip().lower() for wish in existing_submission_wishes}

            # Loop through the submission_wishes and add new ones if they don't exist
            new_wishes = []
            for name in loaded_unique_submission_wishes:
                clean_name = name.strip()[:MAX_NAME_LENGTH]  # Cut off to max length
                normalized = clean_name.lower()
                if normalized not in existing_names_lookup:
                    new_wish = SubmissionWish(name=clean_name, event=event)
                    new_wish.save()
                    new_wishes.append(clean_name)
                    existing_names_lookup.add(normalized)  # <-- Add to lookup to prevent future duplicates

            # Output the results
            if new_wishes:
                self.stdout.write(self.style.WARNING(f'Added new SubmissionWishes: {", ".join(new_wishes)}'))
            else:
                self.stdout.write(self.style.WARNING('No SubmissionWishes added'))

    def getUniqueSubmissionWishes(self, event):
        url = f"https://{event.pretix_api_domain}/api/v1/organizers/{event.pretix_api_organisator_slug}/events/{event.pretix_api_event_slug}/orders/"
        headers = {
            'Authorization': f"Token {event.pretix_api_key}"
        }

        submission_wishes = []

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
                        # Check if attendee_name is set
                        if position['attendee_name']:
                            # Iterate through the answers list
                            for answer in position.get('answers', []):
                                # Check if question_identifier is 'allow_participant_list' and answer is 'True'
                                if answer.get('question_identifier') == event.pretix_identifier_question_submission_wishes:
                                    # Extract the answer and split by commas
                                    raw_values = answer.get('answer', '').split(';')
                                    # Strip whitespaces and filter out empty or invalid strings
                                    valid_values = [value.strip() for value in raw_values if value.strip()]
                                    # Add attendee_email to the result array
                                    submission_wishes.extend(valid_values)

            # Get the URL for the next page, if any
            url = data.get('next')

        unique_submission_wishes = list(set(submission_wishes))
        #return JsonResponse(data)  # Return the data as a response to the client
        return unique_submission_wishes
