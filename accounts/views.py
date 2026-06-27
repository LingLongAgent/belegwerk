"""Views to manage a user's sender profiles (Absender) — list, create, edit, delete.

Every view is scoped to ``request.user`` so one user can never see or touch
another user's profiles. A profile is always saved with its owner attached.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SenderProfileForm
from .models import SenderProfile


@login_required
def profile_list(request: HttpRequest) -> HttpResponse:
    """Show all sender profiles the current user owns."""
    profiles = SenderProfile.objects.filter(user=request.user)
    return render(request, "accounts/profile_list.html", {"profiles": profiles})


@login_required
def profile_create(request: HttpRequest) -> HttpResponse:
    """Create a new sender profile owned by the current user."""
    if request.method == "POST":
        form = SenderProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Absender-Profil gespeichert.")
            return redirect("profile_list")
    else:
        # First profile becomes the default by default — one less click.
        is_first = not SenderProfile.objects.filter(user=request.user).exists()
        form = SenderProfileForm(initial={"is_default": is_first})
    return render(
        request,
        "accounts/profile_form.html",
        {"form": form, "is_edit": False},
    )


@login_required
def profile_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit one of the current user's sender profiles."""
    profile = get_object_or_404(SenderProfile, pk=pk, user=request.user)
    if request.method == "POST":
        form = SenderProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Absender-Profil aktualisiert.")
            return redirect("profile_list")
    else:
        form = SenderProfileForm(instance=profile)
    return render(
        request,
        "accounts/profile_form.html",
        {"form": form, "is_edit": True, "profile": profile},
    )


@login_required
def profile_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete one of the current user's sender profiles after confirmation."""
    profile = get_object_or_404(SenderProfile, pk=pk, user=request.user)
    if request.method == "POST":
        profile.delete()
        messages.success(request, "Absender-Profil gelöscht.")
        return redirect("profile_list")
    return render(
        request,
        "accounts/profile_confirm_delete.html",
        {"profile": profile},
    )
