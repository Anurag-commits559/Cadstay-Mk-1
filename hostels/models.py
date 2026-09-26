"""
Models for the Hostel & Room Listing module (Member 2's scope).

Reuses the project's existing custom user model (accounts.User) via
settings.AUTH_USER_MODEL for ownership — never import accounts.models
directly here, so this app stays loosely coupled to Member 1's app.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


def hostel_image_upload_path(instance, filename):
    """media/hostel_images/hostel_<id_or_tmp>/<filename>"""
    hostel_id = instance.hostel_id or "unsaved"
    return f"hostel_images/hostel_{hostel_id}/{filename}"


class Hostel(models.Model):
    class PropertyType(models.TextChoices):
        HOSTEL = "HOSTEL", "Hostel"
        PG = "PG", "PG"
        STUDENT_RESIDENCE = "RESIDENCE", "Student Residence"
        SHARED_APARTMENT = "APARTMENT", "Shared Apartment"

    class GenderAllowed(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        UNISEX = "UNISEX", "Unisex"

    class FoodType(models.TextChoices):
        VEG = "VEG", "Vegetarian"
        NON_VEG = "NON_VEG", "Non-Vegetarian"
        BOTH = "BOTH", "Veg & Non-Veg"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        DRAFT = "DRAFT", "Draft"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hostels",
    )

    hostel_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, default=PropertyType.HOSTEL
    )

    # Location
    address = models.CharField(max_length=255)
    area = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    gender_allowed = models.CharField(
        max_length=10, choices=GenderAllowed.choices, default=GenderAllowed.UNISEX
    )

    # Food
    food_available = models.BooleanField(default=False)
    food_type = models.CharField(
        max_length=10, choices=FoodType.choices, blank=True
    )
    breakfast_included = models.BooleanField(default=False)
    lunch_included = models.BooleanField(default=False)
    dinner_included = models.BooleanField(default=False)

    # Amenities (kept as simple booleans for fast filtering/checkboxes in the UI)
    wifi = models.BooleanField(default=False)
    ac = models.BooleanField(default=False)
    laundry = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    cctv = models.BooleanField(default=False)
    security = models.BooleanField(default=False)
    power_backup = models.BooleanField(default=False)
    lift = models.BooleanField(default=False)
    common_room = models.BooleanField(default=False)
    study_room = models.BooleanField(default=False)
    gym = models.BooleanField(default=False)
    kitchen = models.BooleanField(default=False)
    housekeeping = models.BooleanField(default=False)
    hot_water = models.BooleanField(default=False)
    washing_machine = models.BooleanField(default=False)

    contact_phone = models.CharField(max_length=15)

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.hostel_name

    def get_absolute_url(self):
        return reverse("hostels:hostel_detail", kwargs={"pk": self.pk})

    # --- Derived / convenience properties -------------------------------
    @property
    def total_rooms(self):
        return self.rooms.count()

    @property
    def available_rooms(self):
        return self.rooms.filter(available_beds__gt=0).count()

    @property
    def starting_rent(self):
        cheapest = self.rooms.order_by("rent").first()
        return cheapest.rent if cheapest else None

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def amenity_list(self):
        """Human-readable list of enabled amenities, for cards/detail page."""
        labels = {
            "wifi": "Wi-Fi", "ac": "AC", "laundry": "Laundry",
            "parking": "Parking", "cctv": "CCTV", "security": "Security",
            "power_backup": "Power Backup", "lift": "Lift",
            "common_room": "Common Room", "study_room": "Study Room",
            "gym": "Gym", "kitchen": "Kitchen", "housekeeping": "Housekeeping",
            "hot_water": "Hot Water", "washing_machine": "Washing Machine",
        }
        return [label for field, label in labels.items() if getattr(self, field)]


class Room(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = "SINGLE", "Single"
        DOUBLE = "DOUBLE", "Double Sharing"
        TRIPLE = "TRIPLE", "Triple Sharing"
        FOUR = "FOUR", "Four Sharing"

    class BathroomType(models.TextChoices):
        ATTACHED = "ATTACHED", "Attached"
        SHARED = "SHARED", "Shared"

    class Furnishing(models.TextChoices):
        FULLY = "FULLY", "Fully Furnished"
        SEMI = "SEMI", "Semi Furnished"
        UNFURNISHED = "UNFURNISHED", "Unfurnished"

    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        LIMITED = "LIMITED", "Limited"
        FULL = "FULL", "Full"

    hostel = models.ForeignKey(
        Hostel, on_delete=models.CASCADE, related_name="rooms"
    )

    room_type = models.CharField(max_length=10, choices=RoomType.choices)
    rent = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(1)]
    )
    security_deposit = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    total_beds = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    available_beds = models.PositiveIntegerField(default=0)
    bathroom_type = models.CharField(
        max_length=10, choices=BathroomType.choices, default=BathroomType.SHARED
    )
    furnishing = models.CharField(
        max_length=15, choices=Furnishing.choices, default=Furnishing.SEMI
    )
    ac_available = models.BooleanField(default=False)
    attached_bathroom = models.BooleanField(default=False)
    balcony = models.BooleanField(default=False)
    room_size = models.CharField(
        max_length=50, blank=True, help_text="e.g. 120 sq.ft."
    )
    description = models.TextField(blank=True)
    availability_status = models.CharField(
        max_length=10,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.AVAILABLE,
        editable=False,
    )

    class Meta:
        ordering = ["rent"]

    def __str__(self):
        return f"{self.get_room_type_display()} — {self.hostel.hostel_name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.available_beds > self.total_beds:
            raise ValidationError(
                {"available_beds": "Available beds cannot exceed total beds."}
            )

    def save(self, *args, **kwargs):
        # Auto-derive availability_status from the bed counts, so the
        # owner never has to set it manually and it can't go stale.
        if self.total_beds and self.available_beds <= 0:
            self.availability_status = self.AvailabilityStatus.FULL
        elif self.total_beds and self.available_beds < self.total_beds:
            self.availability_status = self.AvailabilityStatus.LIMITED
        else:
            self.availability_status = self.AvailabilityStatus.AVAILABLE
        super().save(*args, **kwargs)


class HostelImage(models.Model):
    hostel = models.ForeignKey(
        Hostel, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to=hostel_image_upload_path)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "uploaded_at"]

    def __str__(self):
        return f"Image for {self.hostel.hostel_name}"
