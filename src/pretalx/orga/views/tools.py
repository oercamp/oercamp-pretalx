import collections
import datetime as dt
import json
from contextlib import suppress
import openpyxl

import dateutil.parser
from csp.decorators import csp_update
from django.conf import settings
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView, UpdateView, View
from django_context_decorator import context
from i18nfield.strings import LazyI18nString
from i18nfield.utils import I18nJSONEncoder

from pretalx.agenda.management.commands.export_schedule_html import get_export_zip_path
from pretalx.agenda.tasks import export_schedule_html
from pretalx.agenda.views.utils import get_schedule_exporters
from pretalx.common.language import get_current_language_information
from pretalx.common.text.path import safe_filename
from pretalx.common.text.phrases import phrases
from pretalx.common.views import CreateOrUpdateView, OrderModelView
from pretalx.common.views.mixins import (
    ActionFromUrl,
    EventPermissionRequired,
    PermissionRequired,
)
from pretalx.orga.forms.tools import (
    SurveyMergerForm,
)
from pretalx.schedule.forms import QuickScheduleForm, RoomForm
from pretalx.schedule.models import Availability, Room, TalkSlot, Schedule
from pretalx.schedule.utils import guess_schedule_version


class SurveyMergerView(EventPermissionRequired, FormView):
    template_name = "orga/tools/survey_merger.html"
    permission_required = "orga.change_settings"
    form_class = SurveyMergerForm

    def form_valid(self, form):
        uploaded_file = form.cleaned_data.get("excel_file")
        if not uploaded_file:
            return self.form_invalid(form)  # Re-render the form with an error
        # Process the file
        # Example: Read and process the file in memory
        try:
            # Add your logic to process the file here
            # Example: log file size
            messages.error(self.request, f"Uploaded file size: {uploaded_file.size} bytes")
        except Exception as e:
            form.add_error("excel_file", f"Error processing file: {e}")
            return self.form_invalid(form)

        modified_file = self.process_excel_file(uploaded_file)

        # Return the modified file as a downloadable response
        response = HttpResponse(
            modified_file,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="modified_file.xlsx"'
        return response

    def get_success_url(self):
        return self.request.event.orga_urls.tools_survey_merger

    def get_form_kwargs(self):
        result = super().get_form_kwargs()
        result["event"] = self.request.event
        return result


    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        return result

    def process_excel_file(self, uploaded_file):
        workbook = openpyxl.load_workbook(uploaded_file)
        sheet = workbook.active  # or specify sheet by name: workbook['Sheet1']

        # Iterate over each row (skip header row if needed)
        for row_index, row in enumerate(sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column), start=2):
            # Example: Add new columns to each row (modify the cells directly)
            new_column_1 = "New Value 1"
            new_column_2 = "New Value 2"

            # Insert the new values into the last columns of each row
            sheet.cell(row=row_index, column=sheet.max_column + 1, value=new_column_1)
            sheet.cell(row=row_index, column=sheet.max_column + 2, value=new_column_2)


        # Save the modified workbook to a byte stream (instead of saving to disk)
        from io import BytesIO
        file_stream = BytesIO()
        workbook.save(file_stream)
        file_stream.seek(0)  # Move back to the start of the byte stream

        return file_stream.read()

