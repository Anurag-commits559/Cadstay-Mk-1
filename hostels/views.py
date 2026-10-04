from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Min, Max
from django.core.paginator import Paginator
from django.template.loader import render_to_string

from .models import Hostel, Room, HostelImage
from .forms import HostelForm, RoomForm, RoomFormSet, HostelImageUploadForm, HostelImageForm


# ==========================================
# PUBLIC LIST & DETAIL VIEWS
# ==========================================

def hostel_list(request):
    """
    Public listing page with search, price filtering, gender filtering,
    sorting, pagination, and AJAX support for live search updates.
    """
    queryset = Hostel.objects.filter(status=Hostel.Status.ACTIVE).select_related('owner').prefetch_related('images', 'rooms')

    # Keyword / Area search
    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(
            Q(hostel_name__icontains=query) |
            Q(address__icontains=query) |
            Q(area__icontains=query) |
            Q(city__icontains=query) |
            Q(description__icontains=query)
        )

    # Gender filter
    gender = request.GET.get('gender', '').strip().upper()
    if gender in dict(Hostel.GenderAllowed.choices):
        queryset = queryset.filter(gender_allowed=gender)

    # Budget / Price filter
    min_rent = request.GET.get('min_rent', '').strip()
    max_rent = request.GET.get('max_rent', '').strip()
    if min_rent.isdigit():
        queryset = queryset.filter(rooms__rent__gte=float(min_rent)).distinct()
    if max_rent.isdigit():
        queryset = queryset.filter(rooms__rent__lte=float(max_rent)).distinct()

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        queryset = queryset.annotate(cheapest_rent=Min('rooms__rent')).order_by('cheapest_rent', '-created_at')
    elif sort == 'price_high':
        queryset = queryset.annotate(priciest_rent=Max('rooms__rent')).order_by('-priciest_rent', '-created_at')
    elif sort == 'available':
        queryset = queryset.order_by('-rooms__available_beds', '-created_at').distinct()
    else:
        sort = 'newest'
        queryset = queryset.order_by('-created_at')

    total_count = queryset.count()

    # Active filter count for mobile badge
    active_filters = [
        bool(query),
        bool(gender),
        bool(min_rent),
        bool(max_rent),
    ]
    active_filter_count = sum(1 for f in active_filters if f)

    # Pagination: 6 listings per page
    paginator = Paginator(queryset, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Build hidden query parameters for pagination / filter preserving
    hidden_qs_pairs = []
    for key, values in request.GET.lists():
        if key not in ('page', 'sort'):
            for value in values:
                hidden_qs_pairs.append((key, value))

    context = {
        'page_obj': page_obj,
        'hostels': page_obj.object_list,
        'total_count': total_count,
        'active_filter_count': active_filter_count,
        'sort': sort,
        'hidden_qs_pairs': hidden_qs_pairs,
        'gender_choices': Hostel.GenderAllowed.choices,
    }

    # AJAX live update support for search.js
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        html = render_to_string('hostels/_search_results.html', context, request=request)
        return JsonResponse({'html': html, 'count': total_count})

    return render(request, 'hostels/listings.html', context)


# Aliases for flexible URL routing patterns
index = hostel_list
home = hostel_list


def hostel_detail(request, pk):
    """
    Detailed view of a single hostel property.
    """
    hostel = get_object_or_404(
        Hostel.objects.select_related('owner').prefetch_related('rooms', 'images'),
        pk=pk
    )

    # If inactive or draft, only allow owner or staff/superuser to view
    if hostel.status != Hostel.Status.ACTIVE:
        if not request.user.is_authenticated or (hostel.owner != request.user and not request.user.is_superuser):
            messages.error(request, "This hostel listing is currently unavailable.")
            return redirect('hostels:hostel_list')

    context = {
        'hostel': hostel,
        'rooms': hostel.rooms.all(),
        'images': hostel.images.all(),
    }
    return render(request, 'hostels/details.html', context)


# ==========================================
# HOSTEL MANAGEMENT VIEWS (OWNER PORTAL)
# ==========================================

@login_required
def my_listings(request):
    """
    Displays all listings owned by the logged-in user with summary stats.
    """
    hostels = Hostel.objects.filter(owner=request.user).prefetch_related('images', 'rooms')
    stats = {
        'total': hostels.count(),
        'active': hostels.filter(status=Hostel.Status.ACTIVE).count(),
        'draft': hostels.filter(status=Hostel.Status.DRAFT).count(),
        'available_rooms': sum(h.available_rooms for h in hostels),
    }
    return render(request, 'hostels/my_listings.html', {'hostels': hostels, 'stats': stats})


@login_required
def hostel_add(request):
    """
    Multi-step wizard to create a new hostel listing along with rooms and photos.
    """
    if request.method == 'POST':
        hostel_form = HostelForm(request.POST)
        formset = RoomFormSet(request.POST)
        image_form = HostelImageUploadForm(request.POST, request.FILES)

        if hostel_form.is_valid() and formset.is_valid() and image_form.is_valid():
            hostel = hostel_form.save(commit=False)
            hostel.owner = request.user
            if 'save_draft' in request.POST:
                hostel.status = Hostel.Status.DRAFT
            else:
                hostel.status = Hostel.Status.ACTIVE
            hostel.save()

            formset.instance = hostel
            formset.save()

            # Process uploaded images
            uploaded_images = image_form.cleaned_data.get('images') or request.FILES.getlist('images') or request.FILES.getlist('image')
            for index, img_file in enumerate(uploaded_images):
                img_instance = HostelImage(
                    hostel=hostel,
                    image=img_file,
                    is_primary=(index == 0)
                )
                img_instance.save()

            messages.success(request, f"'{hostel.hostel_name}' has been listed successfully!")
            return redirect('hostels:hostel_detail', pk=hostel.pk)
        else:
            messages.error(request, "Please check the form for errors before continuing.")
    else:
        hostel_form = HostelForm()
        formset = RoomFormSet()
        image_form = HostelImageUploadForm()

    return render(request, 'hostels/add.html', {
        'hostel_form': hostel_form,
        'formset': formset,
        'image_form': image_form,
        'mode': 'add',
    })


@login_required
def hostel_edit(request, pk):
    """
    Edit an existing hostel listing, room configurations, and photos.
    """
    hostel = get_object_or_404(Hostel, pk=pk)
    if hostel.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to edit this hostel.")

    if request.method == 'POST':
        hostel_form = HostelForm(request.POST, instance=hostel)
        formset = RoomFormSet(request.POST, instance=hostel)
        image_form = HostelImageUploadForm(request.POST, request.FILES)

        if hostel_form.is_valid() and formset.is_valid() and image_form.is_valid():
            hostel = hostel_form.save(commit=False)
            if 'save_draft' in request.POST:
                hostel.status = Hostel.Status.DRAFT
            elif hostel.status == Hostel.Status.DRAFT:
                hostel.status = Hostel.Status.ACTIVE
            hostel.save()

            formset.save()

            # Upload any new photos
            has_primary = hostel.images.filter(is_primary=True).exists()
            uploaded_images = image_form.cleaned_data.get('images') or request.FILES.getlist('images') or request.FILES.getlist('image')
            for index, img_file in enumerate(uploaded_images):
                img_instance = HostelImage(
                    hostel=hostel,
                    image=img_file,
                    is_primary=(not has_primary and index == 0)
                )
                img_instance.save()

            messages.success(request, f"Hostel '{hostel.hostel_name}' updated successfully!")
            return redirect('hostels:hostel_detail', pk=hostel.pk)
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        hostel_form = HostelForm(instance=hostel)
        formset = RoomFormSet(instance=hostel)
        image_form = HostelImageUploadForm()

    return render(request, 'hostels/edit.html', {
        'hostel': hostel,
        'hostel_form': hostel_form,
        'formset': formset,
        'image_form': image_form,
        'mode': 'edit',
    })


@login_required
@require_POST
def hostel_delete(request, pk):
    """
    Delete a hostel listing and its associated rooms/images.
    """
    hostel = get_object_or_404(Hostel, pk=pk)
    if hostel.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this hostel.")

    name = hostel.hostel_name
    hostel.delete()
    messages.success(request, f"Hostel '{name}' has been deleted successfully.")
    return redirect('hostels:my_listings')


@login_required
@require_POST
def hostel_deactivate(request, pk):
    """
    Toggle active / inactive status of a hostel listing.
    """
    hostel = get_object_or_404(Hostel, pk=pk)
    if hostel.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to modify this hostel.")

    if hostel.status == Hostel.Status.ACTIVE:
        hostel.status = Hostel.Status.INACTIVE
    else:
        hostel.status = Hostel.Status.ACTIVE
    hostel.save(update_fields=['status'])

    status_str = "activated" if hostel.status == Hostel.Status.ACTIVE else "deactivated"
    messages.info(request, f"Listing for '{hostel.hostel_name}' has been {status_str}.")
    return redirect('hostels:my_listings')


# ==========================================
# ROOM MANAGEMENT VIEWS
# ==========================================

@login_required
def room_add(request, hostel_id):
    """
    Add a room category to a specific hostel.
    """
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    if hostel.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to add rooms to this hostel.")

    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.hostel = hostel
            room.save()
            messages.success(request, "Room added successfully!")
            return redirect('hostels:hostel_detail', pk=hostel.pk)
    else:
        form = RoomForm()

    return redirect('hostels:hostel_edit', pk=hostel.pk)


@login_required
def room_edit(request, room_id):
    """
    Edit details of a specific room type.
    """
    room = get_object_or_404(Room.objects.select_related('hostel'), pk=room_id)
    if room.hostel.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to edit this room.")

    return redirect('hostels:hostel_edit', pk=room.hostel.pk)


@login_required
@require_POST
def room_delete(request, room_id):
    """
    Delete a room from a hostel.
    """
    room = get_object_or_404(Room.objects.select_related('hostel'), pk=room_id)
    if room.hostel.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this room.")

    hostel_id = room.hostel.pk
    room.delete()
    messages.success(request, "Room removed successfully.")
    return redirect('hostels:hostel_edit', pk=hostel_id)


# ==========================================
# IMAGE MANAGEMENT VIEWS
# ==========================================

@login_required
def image_upload(request, hostel_id):
    """
    Upload one or more images for a hostel.
    """
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    if hostel.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to upload images for this hostel.")

    if request.method == 'POST':
        form = HostelImageUploadForm(request.POST, request.FILES)
        files = request.FILES.getlist('images') or request.FILES.getlist('image')
        if form.is_valid() or files:
            files_to_upload = form.cleaned_data.get('images') if form.is_valid() else files
            if not files_to_upload:
                files_to_upload = files
            has_primary = hostel.images.filter(is_primary=True).exists()
            for index, f in enumerate(files_to_upload):
                img_instance = HostelImage(
                    hostel=hostel,
                    image=f,
                    is_primary=(not has_primary and index == 0)
                )
                img_instance.save()
            messages.success(request, "Images uploaded successfully!")
        else:
            messages.error(request, "Please check the selected images and try again.")
    return redirect('hostels:hostel_edit', pk=hostel.pk)


@login_required
@require_POST
def image_delete(request, image_id):
    """
    Delete an image from a hostel gallery.
    """
    image = get_object_or_404(HostelImage.objects.select_related('hostel'), pk=image_id)
    if image.hostel.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this image.")

    hostel_id = image.hostel.pk
    image.delete()
    messages.success(request, "Image deleted.")
    return redirect('hostels:hostel_edit', pk=hostel_id)


@login_required
@require_POST
def image_set_primary(request, image_id):
    """
    Set a specific image as primary showcase image for the hostel.
    """
    image = get_object_or_404(HostelImage.objects.select_related('hostel'), pk=image_id)
    if image.hostel.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to modify this image.")

    HostelImage.objects.filter(hostel=image.hostel, is_primary=True).update(is_primary=False)
    image.is_primary = True
    image.save(update_fields=['is_primary'])

    messages.success(request, "Primary photo updated.")
    return redirect('hostels:hostel_edit', pk=image.hostel.pk)