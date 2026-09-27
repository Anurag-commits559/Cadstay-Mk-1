from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from hostels.models import Hostel, Room

from .forms import BookingRequestForm, ReportForm
from .models import BookingRequest, Favorite, Notification, Report


def is_student(user):
    return user.is_authenticated and user.role == User.Role.TENANT


def is_owner(user):
    return user.is_authenticated and user.role == User.Role.OWNER


def is_admin(user):
    return user.is_authenticated and user.is_staff


# ---------------- FAVORITES ----------------

@login_required
def favorites(request):
    saved = Favorite.objects.filter(
        user=request.user
    ).select_related("hostel").prefetch_related(
        "hostel__images", "hostel__rooms"
    )

    return render(
        request,
        "requests_module/favorites.html",
        {"favorites": saved},
    )


@login_required
@require_POST
def add_favorite(request, hostel_id):
    hostel = get_object_or_404(
        Hostel,
        pk=hostel_id,
        status=Hostel.Status.ACTIVE,
    )

    Favorite.objects.get_or_create(
        user=request.user,
        hostel=hostel,
    )

    messages.success(request, "Hostel saved to favorites.")
    return redirect(request.POST.get("next") or "requests_module:favorites")


@login_required
@require_POST
def remove_favorite(request, hostel_id):
    Favorite.objects.filter(
        user=request.user,
        hostel_id=hostel_id,
    ).delete()

    messages.success(request, "Hostel removed from favorites.")
    return redirect(request.POST.get("next") or "requests_module:favorites")


# ---------------- STUDENT REQUESTS ----------------

@login_required
def my_requests(request):
    if not is_student(request.user):
        raise PermissionDenied

    requests = BookingRequest.objects.filter(
        student=request.user
    ).select_related("hostel", "room", "owner")

    stats = requests.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status="PENDING")),
        accepted=Count("id", filter=Q(status="ACCEPTED")),
        rejected=Count("id", filter=Q(status="REJECTED")),
        cancelled=Count("id", filter=Q(status="CANCELLED")),
    )

    return render(
        request,
        "requests_module/student_requests.html",
        {"requests": requests, "stats": stats},
    )


@login_required
@require_POST
def create_request(request):
    if not is_student(request.user):
        raise PermissionDenied

    form = BookingRequestForm(request.POST)

    if not form.is_valid():
        messages.error(request, "Please select a valid room.")
        return redirect(request.META.get("HTTP_REFERER", "hostels:hostel_list"))

    room = form.cleaned_data["room"]
    hostel = room.hostel

    if hostel.status != Hostel.Status.ACTIVE:
        messages.error(request, "This hostel is not currently available.")
        return redirect("hostels:hostel_detail", pk=hostel.pk)

    if room.available_beds <= 0:
        messages.error(request, "This room is no longer available.")
        return redirect("hostels:hostel_detail", pk=hostel.pk)

    if hostel.owner_id == request.user.id:
        messages.error(request, "You cannot request your own hostel.")
        return redirect("hostels:hostel_detail", pk=hostel.pk)

    if BookingRequest.objects.filter(
        student=request.user,
        room=room,
        status__in=["PENDING", "ACCEPTED"],
    ).exists():
        messages.warning(request, "You already have an active request for this room.")
        return redirect("requests_module:my_requests")

    booking = form.save(commit=False)
    booking.student = request.user
    booking.hostel = hostel
    booking.owner = hostel.owner
    booking.status = BookingRequest.Status.PENDING
    booking.save()

    Notification.objects.create(
        user=hostel.owner,
        title="New hostel request",
        message=f"{request.user.full_name} sent a request for {room.get_room_type_display()} at {hostel.hostel_name}.",
        type=Notification.Type.NEW_REQUEST,
    )

    messages.success(request, "Your request has been sent.")
    return redirect("requests_module:my_requests")


@login_required
@require_POST
def cancel_request(request, request_id):
    if not is_student(request.user):
        raise PermissionDenied

    booking = get_object_or_404(
        BookingRequest,
        pk=request_id,
        student=request.user,
    )

    if booking.status != BookingRequest.Status.PENDING:
        messages.error(request, "Only pending requests can be cancelled.")
    else:
        booking.status = BookingRequest.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        messages.success(request, "Request cancelled.")

    return redirect("requests_module:my_requests")


# ---------------- OWNER REQUESTS ----------------

@login_required
def owner_requests(request):
    if not is_owner(request.user):
        raise PermissionDenied

    requests = BookingRequest.objects.filter(
        owner=request.user
    ).select_related("student", "hostel", "room")

    stats = requests.aggregate(
        pending=Count("id", filter=Q(status="PENDING")),
        accepted=Count("id", filter=Q(status="ACCEPTED")),
        rejected=Count("id", filter=Q(status="REJECTED")),
    )

    return render(
        request,
        "requests_module/owner_requests.html",
        {"requests": requests, "stats": stats},
    )


@login_required
@require_POST
def accept_request(request, request_id):
    if not is_owner(request.user):
        raise PermissionDenied

    with transaction.atomic():
        booking = get_object_or_404(
            BookingRequest.objects.select_for_update(),
            pk=request_id,
            owner=request.user,
        )

        if booking.status != BookingRequest.Status.PENDING:
            messages.error(request, "This request is no longer pending.")
            return redirect("requests_module:owner_requests")

        room = get_object_or_404(
            Room.objects.select_for_update(),
            pk=booking.room_id,
            hostel__owner=request.user,
        )

        if room.available_beds <= 0:
            messages.error(request, "This room is currently full.")
            return redirect("requests_module:owner_requests")

        room.available_beds -= 1
        room.save()

        booking.status = BookingRequest.Status.ACCEPTED
        booking.save(update_fields=["status", "updated_at"])

        Notification.objects.create(
            user=booking.student,
            title="Request accepted",
            message=f"Your request for {room.get_room_type_display()} at {booking.hostel.hostel_name} has been accepted.",
            type=Notification.Type.ACCEPTED,
        )

    messages.success(request, "Request accepted.")
    return redirect("requests_module:owner_requests")


@login_required
@require_POST
def reject_request(request, request_id):
    if not is_owner(request.user):
        raise PermissionDenied

    booking = get_object_or_404(
        BookingRequest,
        pk=request_id,
        owner=request.user,
    )

    if booking.status != BookingRequest.Status.PENDING:
        messages.error(request, "Only pending requests can be rejected.")
        return redirect("requests_module:owner_requests")

    booking.status = BookingRequest.Status.REJECTED
    booking.rejection_reason = request.POST.get("reason", "").strip()
    booking.save(update_fields=["status", "rejection_reason", "updated_at"])

    Notification.objects.create(
        user=booking.student,
        title="Request rejected",
        message=f"Your request for {booking.room.get_room_type_display()} at {booking.hostel.hostel_name} was rejected.",
        type=Notification.Type.REJECTED,
    )

    messages.success(request, "Request rejected.")
    return redirect("requests_module:owner_requests")


# ---------------- NOTIFICATIONS ----------------

@login_required
def notifications(request):
    items = Notification.objects.filter(user=request.user)
    return render(
        request,
        "requests_module/notifications.html",
        {"notifications": items},
    )


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        pk=notification_id,
        user=request.user,
    )
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect("requests_module:notifications")


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(is_read=True)
    return redirect("requests_module:notifications")


# ---------------- REPORTS ----------------

@login_required
@require_POST
def report_hostel(request, hostel_id):
    hostel = get_object_or_404(Hostel, pk=hostel_id)

    form = ReportForm(request.POST)
    if form.is_valid():
        report = form.save(commit=False)
        report.reported_by = request.user
        report.hostel = hostel
        report.save()
        messages.success(request, "Your report has been submitted.")
    else:
        messages.error(request, "Please select a valid report reason.")

    return redirect("hostels:hostel_detail", pk=hostel_id)


# ---------------- ADMIN DASHBOARD ----------------

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()

    context = {
        "total_users": UserModel.objects.count(),
        "total_hostels": Hostel.objects.count(),
        "total_rooms": Room.objects.count(),
        "pending_requests": BookingRequest.objects.filter(
            status="PENDING"
        ).count(),
        "reported_listings": Report.objects.filter(
            status="PENDING"
        ).count(),
    }

    return render(
        request,
        "requests_module/admin_dashboard.html",
        context,
    )


@login_required
@user_passes_test(is_admin)
def admin_users(request):
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()

    query = request.GET.get("q", "").strip()
    users = UserModel.objects.all().order_by("username")

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )

    return render(
        request,
        "requests_module/admin_users.html",
        {"users": users, "query": query},
    )


@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_user_status(request, user_id):
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()

    user = get_object_or_404(UserModel, pk=user_id)

    if user.pk == request.user.pk:
        messages.error(request, "You cannot deactivate your own account.")
    elif user.is_superuser:
        messages.error(request, "Superuser accounts cannot be deactivated here.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        messages.success(request, "User status updated.")

    return redirect("requests_module:admin_users")


@login_required
@user_passes_test(is_admin)
def admin_hostels(request):
    hostels = Hostel.objects.select_related("owner").order_by("-created_at")
    return render(
        request,
        "requests_module/admin_hostels.html",
        {"hostels": hostels},
    )


@login_required
@user_passes_test(is_admin)
@require_POST
def toggle_hostel_status(request, hostel_id):
    hostel = get_object_or_404(Hostel, pk=hostel_id)

    if hostel.status == Hostel.Status.ACTIVE:
        hostel.status = Hostel.Status.INACTIVE
    else:
        hostel.status = Hostel.Status.ACTIVE

    hostel.save(update_fields=["status"])
    messages.success(request, "Hostel status updated.")
    return redirect("requests_module:admin_hostels")


@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    reports = Report.objects.select_related(
        "hostel", "reported_by"
    ).order_by("-created_at")

    return render(
        request,
        "requests_module/admin_reports.html",
        {"reports": reports},
    )


@login_required
@user_passes_test(is_admin)
@require_POST
def update_report_status(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    status = request.POST.get("status")

    valid_statuses = {
        Report.Status.REVIEWED,
        Report.Status.RESOLVED,
        Report.Status.DISMISSED,
    }

    if status in valid_statuses:
        report.status = status
        report.save(update_fields=["status"])
        messages.success(request, "Report status updated.")
    else:
        messages.error(request, "Invalid report status.")

    return redirect("requests_module:admin_reports")
