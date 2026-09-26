from django.contrib.auth.models import AbstractUser
from django.db import models


def profile_picture_upload_path(instance, filename):
    return f"profile_pictures/user_{instance.user_id}/{filename}"


class User(AbstractUser):
    """
    Custom user model for the whole project.

    Built on top of Django's AbstractUser so we keep the battle-tested
    auth system (password hashing, is_staff/is_superuser for admin
    access, permissions, etc.) and only add what this project needs.
    """

    class Role(models.TextChoices):
        TENANT = "TENANT", "Tenant"
        OWNER = "OWNER", "Owner"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.TENANT,
        help_text="Whether this user is looking for a place (Tenant) or listing one (Owner).",
    )

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


class UserProfile(models.Model):
    """
    Extra, optional information about a user. Kept separate from User
    so the core auth model stays lean and other apps can extend profile
    data later without touching authentication.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    profile_picture = models.ImageField(
        upload_to=profile_picture_upload_path, blank=True, null=True
    )
    phone_number = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def completion_percentage(self):
        """Rough profile-completeness indicator shown on the dashboard."""
        fields = [
            self.user.first_name,
            self.user.last_name,
            self.phone_number,
            self.city,
            self.bio,
            bool(self.profile_picture),
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)
