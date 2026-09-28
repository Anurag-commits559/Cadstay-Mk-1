from django import forms
from .models import RoommateProfile


class RoommateProfileForm(forms.ModelForm):

  class Meta:
    model = RoommateProfile
    fields = ['location', 'budget', 'gender_preference', 'bio']
    widgets = {
        'location': forms.TextInput(attrs={'class': 'form-control'}),
        'budget': forms.NumberInput(attrs={'class': 'form-control'}),
        'gender_preference': forms.Select(attrs={'class': 'form-select'}),
        'bio': forms.Textarea(
            attrs={'class': 'form-control', 'rows': 3}
        ),
    }