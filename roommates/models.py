from django.conf import settings
from django.db import models


class RoommateProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Looking for Male'),
        ('female', 'Looking for Female'),
        ('any', 'Any Gender'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roommate_requests'
    )
    location = models.CharField(max_length=250)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    gender_preference = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='any',
    )
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.location}'