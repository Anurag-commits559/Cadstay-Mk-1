"""
Forms for the Hostel & Room Listing module.

Server-side validation lives here (never trust the frontend alone):
required fields, rent > 0, deposit >= 0, available <= total beds,
valid image extensions and file size.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import Hostel, HostelImage, Room

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB per image
MAX_IMAGES_PER_UPLOAD = 10


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """
    A single form field that accepts several files at once (native
    Django has no built-in multi-file field). Validation of each file
    happens in HostelImageUploadForm.clean_images.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True, "id": "hs-image-input"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


CHECKBOX_FIELDS = {
    "food_available", "breakfast_included", "lunch_included", "dinner_included",
    "wifi", "ac", "laundry", "parking", "cctv", "security", "power_backup",
    "lift", "common_room", "study_room", "gym", "kitchen", "housekeeping",
    "hot_water", "washing_machine",
}


class HostelForm(forms.ModelForm):
    class Meta:
        model = Hostel
        fields = [
            "hostel_name", "property_type", "description", "gender_allowed",
            "address", "area", "city", "pincode", "latitude", "longitude",
            "contact_phone",
            "food_available", "food_type",
            "breakfast_included", "lunch_included", "dinner_included",
            "wifi", "ac", "laundry", "parking", "cctv", "security",
            "power_backup", "lift", "common_room", "study_room", "gym",
            "kitchen", "housekeeping", "hot_water", "washing_machine",
        ]
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 4, "class": "form-control"}
            ),
            "hostel_name": forms.TextInput(attrs={"class": "form-control"}),
            "property_type": forms.Select(attrs={"class": "form-select"}),
            "gender_allowed": forms.Select(attrs={"class": "form-select"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "area": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "pincode": forms.TextInput(attrs={"class": "form-control"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "contact_phone": forms.TextInput(attrs={"class": "form-control"}),
            "food_type": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in CHECKBOX_FIELDS:
            self.fields[name].widget.attrs["class"] = "form-check-input"

    def clean_pincode(self):
        pincode = self.cleaned_data["pincode"].strip()
        if not pincode.isdigit() or len(pincode) != 6:
            raise ValidationError("Enter a valid 6-digit pincode.")
        return pincode

    def clean_contact_phone(self):
        phone = self.cleaned_data["contact_phone"].strip()
        digits = phone.replace("+", "").replace(" ", "")
        if not digits.isdigit() or not (10 <= len(digits) <= 13):
            raise ValidationError("Enter a valid contact phone number.")
        return phone


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            "room_type", "rent", "security_deposit", "total_beds",
            "available_beds", "bathroom_type", "furnishing", "ac_available",
            "attached_bathroom", "balcony", "room_size", "description",
        ]
        widgets = {
            "room_type": forms.Select(attrs={"class": "form-select"}),
            "rent": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "security_deposit": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "total_beds": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "available_beds": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "bathroom_type": forms.Select(attrs={"class": "form-select"}),
            "furnishing": forms.Select(attrs={"class": "form-select"}),
            "ac_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "attached_bathroom": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "balcony": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "room_size": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 120 sq.ft."}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        rent = cleaned_data.get("rent")
        deposit = cleaned_data.get("security_deposit")
        total_beds = cleaned_data.get("total_beds")
        available_beds = cleaned_data.get("available_beds")

        if rent is not None and rent <= 0:
            raise ValidationError({"rent": "Rent must be greater than ₹0."})
        if deposit is not None and deposit < 0:
            raise ValidationError(
                {"security_deposit": "Security deposit cannot be negative."}
            )
        if (
            total_beds is not None
            and available_beds is not None
            and available_beds > total_beds
        ):
            raise ValidationError(
                {"available_beds": "Available beds cannot exceed total beds."}
            )
        return cleaned_data


# Owners add multiple rooms dynamically on the same page (Step 6 of the
# add-hostel wizard). min_num=1 already shows one room row to start, so
# extra=0 (no additional blank row); JS clones it for "+ Add Another Room".
RoomFormSet = inlineformset_factory(
    Hostel,
    Room,
    form=RoomForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class HostelImageUploadForm(forms.Form):
    images = MultipleFileField(required=False)

    def clean_images(self):
        files = self.cleaned_data.get("images") or []
        if len(files) > MAX_IMAGES_PER_UPLOAD:
            raise ValidationError(
                f"You can upload at most {MAX_IMAGES_PER_UPLOAD} images at once."
            )
        for f in files:
            ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise ValidationError(
                    f"'{f.name}' is not a supported image type. "
                    "Allowed: JPG, JPEG, PNG, WEBP."
                )
            if f.size > MAX_IMAGE_SIZE_BYTES:
                raise ValidationError(
                    f"'{f.name}' is too large. Maximum size is 5 MB per image."
                )
        return files


class HostelImageForm(forms.ModelForm):
    """
    ModelForm for individual HostelImage records.
    Safely assigns the parent Hostel instance before calling save().
    """

    class Meta:
        model = HostelImage
        fields = ["image", "is_primary"]

    def save(self, commit=True, hostel=None):
        instance = super().save(commit=False)
        if hostel is not None:
            instance.hostel = hostel
        if commit:
            if not instance.hostel_id and not getattr(instance, "hostel", None):
                raise ValueError(
                    "HostelImage requires a parent Hostel instance to be assigned before calling .save()."
                )
            instance.save()
        return instance