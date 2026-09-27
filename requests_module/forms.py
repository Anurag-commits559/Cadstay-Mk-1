from django import forms

from .models import BookingRequest, Report


class BookingRequestForm(forms.ModelForm):
    class Meta:
        model = BookingRequest
        fields = ["room", "message"]
        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Tell the owner about your accommodation needs...",
            }),
            "room": forms.Select(attrs={
                "class": "form-select",
            }),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "description"]
        widgets = {
            "reason": forms.Select(attrs={
                "class": "form-select",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Provide additional details...",
            }),
        }
