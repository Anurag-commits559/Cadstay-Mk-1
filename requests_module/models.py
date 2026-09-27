from django.conf import settings
from django.db import models
from django.db.models import Q


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    hostel = models.ForeignKey(
        "hostels.Hostel",
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "hostel"],
                name="unique_user_hostel_favorite",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.hostel}"


class BookingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="booking_requests",
    )
    hostel = models.ForeignKey(
        "hostels.Hostel",
        on_delete=models.CASCADE,
        related_name="booking_requests",
    )
    room = models.ForeignKey(
        "hostels.Room",
        on_delete=models.CASCADE,
        related_name="booking_requests",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_booking_requests",
    )
    message = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "room"],
                condition=Q(status__in=["PENDING", "ACCEPTED"]),
                name="unique_active_student_room_request",
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.hostel} ({self.status})"


class Notification(models.Model):
    class Type(models.TextChoices):
        NEW_REQUEST = "NEW_REQUEST", "New Request"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        GENERAL = "GENERAL", "General"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.GENERAL,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Report(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEWED = "REVIEWED", "Reviewed"
        RESOLVED = "RESOLVED", "Resolved"
        DISMISSED = "DISMISSED", "Dismissed"

    class Reason(models.TextChoices):
        INCORRECT = "INCORRECT", "Incorrect information"
        FAKE = "FAKE", "Fake listing"
        INAPPROPRIATE = "INAPPROPRIATE", "Inappropriate content"
        UNAVAILABLE = "UNAVAILABLE", "Already unavailable"
        OTHER = "OTHER", "Other"

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hostel_reports",
    )
    hostel = models.ForeignKey(
        "hostels.Hostel",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report #{self.pk} - {self.hostel}"
