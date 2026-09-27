from django.urls import path

from . import views

app_name = "requests_module"

urlpatterns = [
    # Favorites
    path("favorites/", views.favorites, name="favorites"),
    path("favorite/<int:hostel_id>/", views.add_favorite, name="add_favorite"),
    path(
        "favorite/<int:hostel_id>/remove/",
        views.remove_favorite,
        name="remove_favorite",
    ),

    # Student requests
    path("my-requests/", views.my_requests, name="my_requests"),
    path("request/create/", views.create_request, name="create_request"),
    path(
        "request/<int:request_id>/cancel/",
        views.cancel_request,
        name="cancel_request",
    ),

    # Owner requests
    path("owner/requests/", views.owner_requests, name="owner_requests"),
    path(
        "owner/request/<int:request_id>/accept/",
        views.accept_request,
        name="accept_request",
    ),
    path(
        "owner/request/<int:request_id>/reject/",
        views.reject_request,
        name="reject_request",
    ),

    # Notifications
    path("notifications/", views.notifications, name="notifications"),
    path(
        "notification/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "notifications/read-all/",
        views.mark_all_read,
        name="mark_all_read",
    ),

    # Reports
    path(
        "hostel/<int:hostel_id>/report/",
        views.report_hostel,
        name="report_hostel",
    ),

    # Custom admin dashboard
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/users/", views.admin_users, name="admin_users"),
    path(
        "admin-dashboard/users/<int:user_id>/toggle/",
        views.toggle_user_status,
        name="toggle_user_status",
    ),
    path("admin-dashboard/hostels/", views.admin_hostels, name="admin_hostels"),
    path(
        "admin-dashboard/hostels/<int:hostel_id>/toggle/",
        views.toggle_hostel_status,
        name="toggle_hostel_status",
    ),
    path("admin-dashboard/reports/", views.admin_reports, name="admin_reports"),
    path(
        "admin-dashboard/reports/<int:report_id>/status/",
        views.update_report_status,
        name="update_report_status",
    ),
]
