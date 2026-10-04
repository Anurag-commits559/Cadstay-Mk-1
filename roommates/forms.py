from django import forms
from django.core.exceptions import ValidationError
from .models import RoommateProfile


class RoommateProfileForm(forms.ModelForm):
    class Meta:
        model = RoommateProfile
        fields = ['location', 'budget', 'gender_preference', 'bio']
        widgets = {
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Koramangala 4th Block, Near Christ College',
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 8000',
                'min': '500',
            }),
            'gender_preference': forms.Select(attrs={
                'class': 'form-select',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your habits, college/workplace, preferred amenities, cleanliness habits, and moving date...',
            }),
        }

    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget is not None and budget <= 0:
            raise ValidationError("Budget must be greater than zero.")
        return budget