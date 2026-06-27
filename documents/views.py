"""Views for documents: the type chooser and the recipient address book.

Every recipient view is scoped to ``request.user`` so one user can never see or
touch another user's saved recipients — the same ownership rule the sender
profiles follow. A recipient is always saved with its owner attached.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RecipientForm
from .models import Recipient

DOC_TYPES = [
    {"key": "rechnung", "name": "Rechnung", "desc": "Positionen, USt, Summen, Zahlungsziel."},
    {"key": "angebot", "name": "Angebot", "desc": "Positionen und Gültigkeit."},
    {"key": "vertrag", "name": "Vertrag", "desc": "Parteien, §-Klauseln, Unterschriften."},
    {"key": "zahlungserinnerung", "name": "Zahlungserinnerung", "desc": "Bezug auf Rechnung, Frist."},
]


@login_required
def choose_type(request: HttpRequest) -> HttpResponse:
    """Dokumenttyp wählen — Formulare folgen je Typ (Build-Loop)."""
    return render(request, "documents/choose_type.html", {"types": DOC_TYPES})


@login_required
def recipient_list(request: HttpRequest) -> HttpResponse:
    """Show all recipients (Adressbuch) the current user owns."""
    recipients = Recipient.objects.filter(user=request.user)
    return render(
        request,
        "documents/recipient_list.html",
        {"recipients": recipients},
    )


@login_required
def recipient_create(request: HttpRequest) -> HttpResponse:
    """Create a new recipient owned by the current user."""
    if request.method == "POST":
        form = RecipientForm(request.POST)
        if form.is_valid():
            recipient = form.save(commit=False)
            recipient.user = request.user
            recipient.save()
            messages.success(request, "Empfänger gespeichert.")
            return redirect("documents:recipient_list")
    else:
        form = RecipientForm()
    return render(
        request,
        "documents/recipient_form.html",
        {"form": form, "is_edit": False},
    )


@login_required
def recipient_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit one of the current user's recipients."""
    recipient = get_object_or_404(Recipient, pk=pk, user=request.user)
    if request.method == "POST":
        form = RecipientForm(request.POST, instance=recipient)
        if form.is_valid():
            form.save()
            messages.success(request, "Empfänger aktualisiert.")
            return redirect("documents:recipient_list")
    else:
        form = RecipientForm(instance=recipient)
    return render(
        request,
        "documents/recipient_form.html",
        {"form": form, "is_edit": True, "recipient": recipient},
    )


@login_required
def recipient_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete one of the current user's recipients after confirmation."""
    recipient = get_object_or_404(Recipient, pk=pk, user=request.user)
    if request.method == "POST":
        recipient.delete()
        messages.success(request, "Empfänger gelöscht.")
        return redirect("documents:recipient_list")
    return render(
        request,
        "documents/recipient_confirm_delete.html",
        {"recipient": recipient},
    )
