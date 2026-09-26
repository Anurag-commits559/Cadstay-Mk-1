from django.contrib import admin

from .models import Hostel, HostelImage, Room


class RoomInline(admin.TabularInline):
    model = Room
    extra = 0


class HostelImageInline(admin.TabularInline):
    model = HostelImage
    extra = 0


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = (
        "hostel_name", "owner", "city", "property_type",
        "status", "total_rooms", "available_rooms", "created_at",
    )
    list_filter = ("status", "property_type", "gender_allowed", "city")
    search_fields = ("hostel_name", "address", "city", "owner__username")
    inlines = [RoomInline, HostelImageInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "hostel", "room_type", "rent", "total_beds",
        "available_beds", "availability_status",
    )
    list_filter = ("room_type", "availability_status")
