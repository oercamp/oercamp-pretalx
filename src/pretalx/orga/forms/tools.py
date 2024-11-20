from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_scopes.forms import SafeModelMultipleChoiceField
from i18nfield.forms import I18nFormMixin, I18nModelForm

from pretalx.common.forms.mixins import I18nHelpText
from pretalx.common.text.phrases import phrases
from pretalx.orga.forms.export import ExportForm


class SurveyMergerForm(forms.Form):
    excel_file = forms.FileField(
        label="Upload Excel File",
        required=True,
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": ".xlsx, .xls"}
        ),
    )

    def __init__(self, *args, event=None, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)
