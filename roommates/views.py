from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

from .models import RoommateProfile
from .forms import RoommateProfileForm


def roommate_list(request):
    """
    List active roommate profiles with search filters and sorting.
    """
    profiles = RoommateProfile.objects.filter(is_active=True).select_related('user', 'user__profile')

    query = request.GET.get('q', '').strip()
    gender = request.GET.get('gender', '').strip().lower()
    max_budget = request.GET.get('max_budget', '').strip()
    sort = request.GET.get('sort', 'newest')

    if query:
        profiles = profiles.filter(
            Q(location__icontains=query) |
            Q(bio__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query)
        )

    if gender in ['male', 'female', 'any']:
        profiles = profiles.filter(gender_preference=gender)

    if max_budget.isdigit():
        profiles = profiles.filter(budget__lte=float(max_budget))

    if sort == 'budget_asc':
        profiles = profiles.order_by('budget', '-created_at')
    elif sort == 'budget_desc':
        profiles = profiles.order_by('-budget', '-created_at')
    else:
        profiles = profiles.order_by('-created_at')

    context = {
        'profiles': profiles,
        'sort': sort,
    }
    return render(request, 'roommates/index.html', context)


# Route alias
index = roommate_list


@login_required
def create_roommate_request(request):
    """
    Post a new roommate requirement listing.
    """
    if request.method == 'POST':
        form = RoommateProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.is_active = True
            profile.save()
            messages.success(request, "Your roommate request has been posted successfully!")
            return redirect('roommates:roommate_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RoommateProfileForm()

    return render(request, 'roommates/create_request.html', {'form': form})


# Route aliases for compatibility
create_or_edit_profile = create_roommate_request
create_profile = create_roommate_request


@login_required
def edit_roommate_request(request, pk):
    """
    Edit an existing roommate requirement listing.
    """
    profile = get_object_or_404(RoommateProfile, pk=pk)
    if profile.user != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to edit this listing.")

    if request.method == 'POST':
        form = RoommateProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Roommate request updated successfully!")
            return redirect('roommates:roommate_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RoommateProfileForm(instance=profile)

    return render(request, 'roommates/create_request.html', {
        'form': form,
        'is_edit': True,
        'profile': profile,
    })


@login_required
@require_POST
def delete_roommate_request(request, pk):
    """
    Delete a roommate request.
    """
    profile = get_object_or_404(RoommateProfile, pk=pk)
    if profile.user != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this listing.")

    profile.delete()
    messages.success(request, "Roommate request deleted.")
    return redirect('roommates:roommate_list')


def roommate_detail(request, pk):
    """
    Detail page for a specific roommate request.
    """
    profile = get_object_or_404(RoommateProfile.objects.select_related('user', 'user__profile'), pk=pk)
    return render(request, 'roommates/detail.html', {'profile': profile})