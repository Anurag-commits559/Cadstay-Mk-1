from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import UserProfile

User = get_user_model()

BOOTSTRAP_INPUT = "form-control"
BOOTSTRAP_SELECT = "form-select"


class RegistrationForm(forms.ModelForm):
    """Registration form with password confirmation and role selection."""

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "First name"}),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "Last name"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "you@example.com"})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "Password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "Confirm password"}),
    )
    role = forms.ChoiceField(
        choices=User.Role.choices,
        initial=User.Role.TENANT,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "role"]
        widgets = {
            "username": forms.TextInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "Choose a username"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")

        if password1:
            # Run Django's configured password validators (length,
            # common-password check, similarity to user attributes, etc.)
            from django.contrib.auth.password_validation import validate_password

            temp_user = User(
                username=cleaned_data.get("username", ""),
                email=cleaned_data.get("email", ""),
                first_name=cleaned_data.get("first_name", ""),
                last_name=cleaned_data.get("last_name", ""),
            )
            try:
                validate_password(password1, user=temp_user)
            except ValidationError as error:
                self.add_error("password1", error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UsernameOrEmailAuthenticationForm(AuthenticationForm):
    """Login form styled with Bootstrap; field relabelled for clarity."""

    username = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "Username or email", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "Password"}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Invalid username/email or password.",
    }


class BootstrapPasswordChangeForm(PasswordChangeForm):
    """Django's built-in password-change form, styled with Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = BOOTSTRAP_INPUT


class UserUpdateForm(forms.ModelForm):
    """Lets a user edit their own basic account fields — nothing else."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": BOOTSTRAP_INPUT}),
            "last_name": forms.TextInput(attrs={"class": BOOTSTRAP_INPUT}),
            "email": forms.EmailInput(attrs={"class": BOOTSTRAP_INPUT}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Another account is already using this email.")
        return email


class UserProfileUpdateForm(forms.ModelForm):
    """Lets a user edit their profile fields, including a validated photo."""

    class Meta:
        model = UserProfile
        fields = ["profile_picture", "phone_number", "city", "bio"]
        widgets = {
            "profile_picture": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "Phone number"}),
            "city": forms.TextInput(attrs={"class": BOOTSTRAP_INPUT, "placeholder": "City"}),
            "bio": forms.Textarea(attrs={"class": BOOTSTRAP_INPUT, "rows": 4, "placeholder": "Tell others a little about yourself"}),
        }

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture")
        if picture and hasattr(picture, "size"):
            max_size = getattr(settings, "MAX_PROFILE_IMAGE_SIZE_BYTES", 2 * 1024 * 1024)
            if picture.size > max_size:
                raise ValidationError(
                    f"Image file too large ( > {max_size // (1024 * 1024)}MB )."
                )
            valid_types = {"image/jpeg", "image/png", "image/webp"}
            content_type = getattr(picture, "content_type", None)
            if content_type and content_type not in valid_types:
                raise ValidationError("Only JPEG, PNG or WEBP images are allowed.")
        return picture
