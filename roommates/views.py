from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RoommateProfileForm
from .models import RoommateProfile


def index(request):
  query = request.GET.get('q', '').strip()
  gender = request.GET.get('gender', '')
  max_budget = request.GET.get('max_budget', '')
  sort_by = request.GET.get('sort', 'newest')

  profiles = RoommateProfile.objects.all()

  # Search Filter
  if query:
    profiles = profiles.filter(
        Q(location__icontains=query) | Q(bio__icontains=query)
    )

  # Gender Filter
  if gender and gender != 'All Genders':
    profiles = profiles.filter(gender_preference=gender)

  # Budget Filter
  if max_budget:
    try:
      profiles = profiles.filter(budget__lte=float(max_budget))
    except ValueError:
      pass

  # Sorting
  if sort_by == 'budget_asc':
    profiles = profiles.order_by('budget')
  elif sort_by == 'budget_desc':
    profiles = profiles.order_by('-budget')
  else:
    profiles = profiles.order_by('-created_at')

  return render(request, 'roommates/index.html', {'profiles': profiles})


@login_required
def create_request(request):
  if request.method == 'POST':
    form = RoommateProfileForm(request.POST)
    if form.is_valid():
      profile = form.save(commit=False)
      profile.user = request.user
      profile.save()
      return redirect('roommates:roommate_list')
  else:
    form = RoommateProfileForm()
  return render(request, 'roommates/create_request.html', {'form': form})


@login_required
def delete_request(request, pk):
  profile = get_object_or_404(RoommateProfile, pk=pk, user=request.user)
  if request.method == 'POST':
    profile.delete()
  return redirect('roommates:roommate_list')