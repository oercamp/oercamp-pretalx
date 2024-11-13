import requests
import logging

import datetime as dt
import jwt


#from django.core.cache import cache
#from django.http import JsonResponse
from django.utils.functional import cached_property


#import io
#from collections import defaultdict
#from urllib.parse import urlparse

#import vobject
from django.conf import settings
#from django.core.exceptions import SuspiciousFileOperation
#from django.core.files.storage import Storage
#from django.http import FileResponse, Http404, HttpResponse
#from django.shortcuts import redirect

#from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from django_context_decorator import context

#from pretalx.common.text.path import safe_filename
from pretalx.common.views.mixins import (
    EventPermissionRequired,
#    Filterable,
#    PermissionRequired,
#    SocialMediaCardMixin,
)


class VenuelessEmbedded(EventPermissionRequired, TemplateView):
    template_name = "agenda/venueless_embedded.html"
    permission_required = "agenda.view_schedule"

    @context
    def is_venueless_world_enabled(self):
        return self.request.event.is_venueless_world_enabled

    @context
    @cached_property
    def user_venueless_embedded_link(self):

        if (
            not self.is_venueless_world_enabled or
            not self.request.user.is_authenticated
        ):
            return False

        speaker = self.request.user

        iat = dt.datetime.utcnow()
        exp = iat + dt.timedelta(days=30)
        profile = {
            "display_name": speaker.name,
            "fields": {
                "pretalx_id": speaker.code,
            },
        }

        if speaker.avatar_url:
            profile["profile_picture"] = speaker.get_avatar_url(request.event)


        # see 1.1. Authentication in docs: https://venueless.readthedocs.io/_/downloads/en/latest/pdf/
        payload = {
            "iss": "any",
            "aud": "venueless",
            "exp": exp,
            "iat": iat,
            "uid": speaker.code,
            "profile": profile,
            "traits": list(
                {
                    'attendee'
                }
            ),
        }

        token = jwt.encode(payload, self.request.event.venueless_secret, algorithm="HS256")
        return "https://{}/#token={}".format(self.request.event.venueless_domain, token)
