"""
Views for the Hostel & Room Listing module.

Notes for Member 3 (search/filters/roommate matching):
    hostel_list() below reads a `sort` query param and applies ordering
    to an already-filtered (status=ACTIVE) queryset. Add your filter
    query params (city, gender, rent range, amenities, etc.) to the
    same queryset *before* the sort/pagination logic, and the page will
    keep working exactly the same way.

Notes for Member 4 (requests/favorites/admin):
    hostel_detail() passes `hostel` into the template context. The
    "Contact Owner" / "Send Request" button in hostels/details.html is
    a plain link/button with a `data-hostel-id` attribute and is not
    wired to any request logic — hook your request-creation view/JS
    onto it.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Min, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import HostelForm, HostelImageUploadForm, RoomFormSet
from .models import Hostel, HostelImage, Room

PAGE_SIZE = 12


def _owner_or_403(hostel, user):
    if hostel.owner_id != user.id:
        raise PermissionDenied("You don't have permission to edit this listing.")


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def hostel_list(request):
    hostels = (
        Hostel.objects.filter(status=Hostel.Status.ACTIVE)
        .select_related("owner")
        .prefetch_related("images", "rooms")
    )

    # --- Member 3 hooks into filtering here (before sort/pagination) ---

    sort = request.GET.get("sort", "newest")
    if sort == "price_low":
        hostels = hostels.annotate(min_rent=Min("rooms__rent")).order_by(
            "min_rent"
        )
    elif sort == "price_high":
        hostels = hostels.annotate(min_rent=Min("rooms__rent")).order_by(
            "-min_rent"
        )
    elif sort == "available":
        hostels = hostels.annotate(
            total_available=Sum("rooms__available_beds")
        ).order_by("-total_available")
    else:
        sort = "newest"
        hostels = hostels.order_by("-created_at")

    paginator = Paginator(hostels, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "hostels/listings.html",
        {
            "page_obj": page_obj,
            "sort": sort,
            "total_count": paginator.count,
        },
    )


def hostel_detail(request, pk):
    hostel = get_object_or_404(
        Hostel.objects.prefetch_related("images", "rooms"), pk=pk
    )
    return render(request, "hostels/details.html", {"hostel": hostel})


# ---------------------------------------------------------------------------
# Owner-only pages
# ---------------------------------------------------------------------------

@login_required
def my_listings(request):
    hostels = Hostel.objects.filter(owner=request.user).prefetch_related(
        "images", "rooms"
    )
    stats = {
        "total": hostels.count(),
        "active": hostels.filter(status=Hostel.Status.ACTIVE).count(),
        "draft": hostels.filter(status=Hostel.Status.DRAFT).count(),
        "available_rooms": sum(h.available_rooms for h in hostels),
    }
    return render(
        request, "hostels/my_listings.html", {"hostels": hostels, "stats": stats}
    )


@login_required
def hostel_add(request):
    if request.method == "POST":
        hostel_form = HostelForm(request.POST)
        formset = RoomFormSet(request.POST, instance=Hostel())
        image_form = HostelImageUploadForm(request.POST, request.FILES)

        forms_valid = (
            hostel_form.is_valid() and formset.is_valid() and image_form.is_valid()
        )
        images = image_form.cleaned_data.get("images") if forms_valid else []
        is_draft = "save_draft" in request.POST

        if forms_valid and not images and not is_draft:
            messages.error(request, "Please upload at least one image.")
            forms_valid = False

        if forms_valid:
            hostel = hostel_form.save(commit=False)
            hostel.owner = request.user
            hostel.status = (
                Hostel.Status.DRAFT if is_draft else Hostel.Status.ACTIVE
            )
            hostel.save()

            formset.instance = hostel
            formset.save()

            for index, f in enumerate(images):
                HostelImage.objects.create(
                    hostel=hostel, image=f, is_primary=(index == 0)
                )

            messages.success(
                request,
                "Draft saved." if is_draft else "Listing published successfully!",
            )
            return redirect("hostels:hostel_detail", pk=hostel.pk)
    else:
        hostel_form = HostelForm()
        formset = RoomFormSet(instance=Hostel())
        image_form = HostelImageUploadForm()

    return render(
        request,
        "hostels/add.html",
        {"hostel_form": hostel_form, "formset": formset, "image_form": image_form},
    )


@login_required
def hostel_edit(request, pk):
    hostel = get_object_or_404(Hostel, pk=pk)
    _owner_or_403(hostel, request.user)

    if request.method == "POST":
        hostel_form = HostelForm(request.POST, instance=hostel)
        formset = RoomFormSet(request.POST, instance=hostel)
        image_form = HostelImageUploadForm(request.POST, request.FILES)

        if hostel_form.is_valid() and formset.is_valid() and image_form.is_valid():
            hostel = hostel_form.save()
            formset.save()

            new_images = image_form.cleaned_data.get("images") or []
            has_primary_already = hostel.images.filter(is_primary=True).exists()
            for index, f in enumerate(new_images):
                HostelImage.objects.create(
                    hostel=hostel,
                    image=f,
                    is_primary=(index == 0 and not has_primary_already),
                )

            messages.success(request, "Listing updated successfully!")
            return redirect("hostels:hostel_detail", pk=hostel.pk)
    else:
        hostel_form = HostelForm(instance=hostel)
        formset = RoomFormSet(instance=hostel)
        image_form = HostelImageUploadForm()

    return render(
        request,
        "hostels/edit.html",
        {
            "hostel": hostel,
            "hostel_form": hostel_form,
            "formset": formset,
            "image_form": image_form,
        },
    )


@login_required
@require_POST
def hostel_delete(request, pk):
    hostel = get_object_or_404(Hostel, pk=pk)
    _owner_or_403(hostel, request.user)
    name = hostel.hostel_name
    hostel.delete()
    messages.success(request, f'"{name}" was deleted.')
    return redirect("hostels:my_listings")


@login_required
@require_POST
def hostel_deactivate(request, pk):
    hostel = get_object_or_404(Hostel, pk=pk)
    _owner_or_403(hostel, request.user)
    hostel.status = (
        Hostel.Status.INACTIVE
        if hostel.status == Hostel.Status.ACTIVE
        else Hostel.Status.ACTIVE
    )
    hostel.save(update_fields=["status", "updated_at"])
    messages.success(
        request, f'"{hostel.hostel_name}" is now {hostel.get_status_display()}.'
    )
    return redirect("hostels:my_listings")


# ---------------------------------------------------------------------------
# Lightweight JSON endpoints (used by hostel.js for one-off edits from the
# Edit page / owner dashboard, without resubmitting the whole form)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def room_add(request, hostel_id):
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    _owner_or_403(hostel, request.user)
    from .forms import RoomForm

    form = RoomForm(request.POST)
    if form.is_valid():
        room = form.save(commit=False)
        room.hostel = hostel
        room.save()
        return JsonResponse({"success": True, "room_id": room.id})
    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_POST
def room_edit(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    _owner_or_403(room.hostel, request.user)
    from .forms import RoomForm

    form = RoomForm(request.POST, instance=room)
    if form.is_valid():
        form.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_POST
def room_delete(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    _owner_or_403(room.hostel, request.user)
    room.delete()
    return JsonResponse({"success": True})


@login_required
@require_POST
def image_upload(request, hostel_id):
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    _owner_or_403(hostel, request.user)

    form = HostelImageUploadForm(request.POST, request.FILES)
    if form.is_valid():
        files = form.cleaned_data.get("images") or []
        has_primary_already = hostel.images.filter(is_primary=True).exists()
        created_ids = []
        for index, f in enumerate(files):
            img = HostelImage.objects.create(
                hostel=hostel,
                image=f,
                is_primary=(index == 0 and not has_primary_already),
            )
            created_ids.append(img.id)
        return JsonResponse({"success": True, "image_ids": created_ids})
    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_POST
def image_delete(request, image_id):
    image = get_object_or_404(HostelImage, pk=image_id)
    _owner_or_403(image.hostel, request.user)
    image.image.delete(save=False)
    image.delete()
    return JsonResponse({"success": True})


@login_required
@require_POST
def image_set_primary(request, image_id):
    image = get_object_or_404(HostelImage, pk=image_id)
    _owner_or_403(image.hostel, request.user)
    image.hostel.images.update(is_primary=False)
    image.is_primary = True
    image.save(update_fields=["is_primary"])
    return JsonResponse({"success": True})
