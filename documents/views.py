"""Views for documents: the type chooser and the recipient address book.

Every recipient view is scoped to ``request.user`` so one user can never see or
touch another user's saved recipients — the same ownership rule the sender
profiles follow. A recipient is always saved with its owner attached.
"""

from __future__ import annotations

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ContractClauseFormSet,
    ContractForm,
    InvoiceForm,
    InvoiceItemFormSet,
    OfferForm,
    OfferItemFormSet,
    RecipientForm,
    ReminderForm,
)
from .models import Document, Recipient

DOC_TYPES = [
    {"key": "rechnung", "name": "Rechnung", "desc": "Positionen, USt, Summen, Zahlungsziel.",
     "url_name": "documents:invoice_create"},
    {"key": "angebot", "name": "Angebot", "desc": "Positionen und Gültigkeit.",
     "url_name": "documents:offer_create"},
    {"key": "vertrag", "name": "Vertrag", "desc": "Parteien, §-Klauseln, Unterschriften.",
     "url_name": "documents:contract_create"},
    {"key": "zahlungserinnerung", "name": "Zahlungserinnerung", "desc": "Bezug auf Rechnung, Frist.",
     "url_name": "documents:reminder_create"},
]


@login_required
def choose_type(request: HttpRequest) -> HttpResponse:
    """Dokumenttyp wählen — Formulare folgen je Typ (Build-Loop)."""
    return render(request, "documents/choose_type.html", {"types": DOC_TYPES})


@login_required
def invoice_create(request: HttpRequest) -> HttpResponse:
    """Create a Rechnung: invoice fields plus a positions formset → saved Document.

    A fresh form arrives pre-filled where it sensibly can be — today's date, the
    user's standard sender profile, and (via ``?recipient=<id>``) a chosen
    address-book entry — so the user mostly fills in the positions. On success the
    document and its positions are stored; the PDF preview/download follows in M8.
    """
    if request.method == "POST":
        form = InvoiceForm(request.POST, user=request.user)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.doc_type = Document.Type.INVOICE
            document.save()
            formset.instance = document
            items = formset.save(commit=False)
            for position, item in enumerate(items, start=1):
                item.position = position
                item.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
            messages.success(request, "Rechnung gespeichert.")
            return redirect("dashboard")
    else:
        initial = {"date": datetime.date.today()}
        recipient_id = request.GET.get("recipient")
        if recipient_id:
            recipient = get_object_or_404(
                Recipient, pk=recipient_id, user=request.user
            )
            initial.update(recipient.as_document_initial())
        form = InvoiceForm(user=request.user, initial=initial)
        formset = InvoiceItemFormSet()
    return render(
        request,
        "documents/invoice_form.html",
        {"form": form, "formset": formset},
    )


@login_required
def offer_create(request: HttpRequest) -> HttpResponse:
    """Create an Angebot: offer fields plus a positions formset → saved Document.

    Mirrors :func:`invoice_create` — today's date, the standard sender and an
    optional ``?recipient=<id>`` address-book entry are pre-filled — but stores a
    document of type Angebot. The validity date carries py_doc's ``valid_until``;
    the PDF preview/download follows in M8.
    """
    if request.method == "POST":
        form = OfferForm(request.POST, user=request.user)
        formset = OfferItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.doc_type = Document.Type.OFFER
            document.save()
            formset.instance = document
            items = formset.save(commit=False)
            for position, item in enumerate(items, start=1):
                item.position = position
                item.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
            messages.success(request, "Angebot gespeichert.")
            return redirect("dashboard")
    else:
        initial = {"date": datetime.date.today()}
        recipient_id = request.GET.get("recipient")
        if recipient_id:
            recipient = get_object_or_404(
                Recipient, pk=recipient_id, user=request.user
            )
            initial.update(recipient.as_document_initial())
        form = OfferForm(user=request.user, initial=initial)
        formset = OfferItemFormSet()
    return render(
        request,
        "documents/offer_form.html",
        {"form": form, "formset": formset},
    )


@login_required
def contract_create(request: HttpRequest) -> HttpResponse:
    """Create a Vertrag: contract fields plus a clauses formset → saved Document.

    Mirrors :func:`invoice_create` — today's date, the standard sender and an
    optional ``?recipient=<id>`` address-book entry are pre-filled — but stores a
    document of type Vertrag, where the sender and recipient are the two parties
    and the formset holds the numbered §-clauses. The PDF preview/download
    follows in M8.
    """
    if request.method == "POST":
        form = ContractForm(request.POST, user=request.user)
        formset = ContractClauseFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.doc_type = Document.Type.CONTRACT
            document.save()
            formset.instance = document
            clauses = formset.save(commit=False)
            for position, clause in enumerate(clauses, start=1):
                clause.position = position
                clause.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
            messages.success(request, "Vertrag gespeichert.")
            return redirect("dashboard")
    else:
        initial = {"date": datetime.date.today()}
        recipient_id = request.GET.get("recipient")
        if recipient_id:
            recipient = get_object_or_404(
                Recipient, pk=recipient_id, user=request.user
            )
            initial.update(recipient.as_document_initial())
        form = ContractForm(user=request.user, initial=initial)
        formset = ContractClauseFormSet()
    return render(
        request,
        "documents/contract_form.html",
        {"form": form, "formset": formset},
    )


@login_required
def reminder_create(request: HttpRequest) -> HttpResponse:
    """Create a Zahlungserinnerung: reminder fields → saved Document.

    Mirrors :func:`invoice_create` — today's date, the standard sender and an
    optional ``?recipient=<id>`` address-book entry are pre-filled — but stores a
    document of type Zahlungserinnerung. A reminder has no positions, so it is a
    flat form (no formset); the PDF preview/download follows in M8.
    """
    if request.method == "POST":
        form = ReminderForm(request.POST, user=request.user)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.doc_type = Document.Type.REMINDER
            document.save()
            messages.success(request, "Zahlungserinnerung gespeichert.")
            return redirect("dashboard")
    else:
        initial = {"date": datetime.date.today()}
        recipient_id = request.GET.get("recipient")
        if recipient_id:
            recipient = get_object_or_404(
                Recipient, pk=recipient_id, user=request.user
            )
            initial.update(recipient.as_document_initial())
        form = ReminderForm(user=request.user, initial=initial)
    return render(
        request,
        "documents/reminder_form.html",
        {"form": form},
    )


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
