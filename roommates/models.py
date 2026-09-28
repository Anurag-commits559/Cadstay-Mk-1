from django.conf import settings
from django.db import models


class RoommateProfile(models.Model):
  user = models.ForeignKey(
      settings.AUTH_USER_MODEL, on_delete=models.CASCADE
  )
  location = models.CharField(max_length=250)
  budget = models.DecimalField(max_digits=10, decimal_places=2)
  gender_preference = models.CharField(
      max_length=10,
      choices=[('male', 'Male'), ('female', 'Female'), ('any', 'Any')],
      default='any',
  )
  bio = models.TextField(blank=True)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f'{self.user.username} - {self.location}'