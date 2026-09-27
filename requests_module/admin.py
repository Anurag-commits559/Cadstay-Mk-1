from django.contrib import admin

from .models import BookingRequest, Favorite, Notification, Report


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "hostel", "created_at")
    search_fields = ("user__username", "hostel__hostel_name")


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "hostel", "room", "owner", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("student__username", "hostel__hostel_name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "type", "is_read", "created_at")
    list_filter = ("type", "is_read")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("hostel", "reported_by", "reason", "status", "created_at")
    list_filter = ("status", "reason")
