from django.apps import AppConfig


class HostelsConfig(AppConfig):
    """
    App config for the Hostel & Room Listing module (Member 2's scope).

    Owns: Hostel, Room, HostelImage models and everything needed to
    list, browse, add, edit and delete hostel listings.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "hostels"
    verbose_name = "Hostel & Room Listings"
