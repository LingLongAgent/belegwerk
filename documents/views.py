"""Views for documents: the type chooser, the create/edit masks and the
recipient address book.

Every view is scoped to ``request.user`` so one user can never see or touch
another user's documents or saved recipients — the same ownership rule the
sender profiles follow. A document or recipient is always saved with its owner
attached.

The four ``*_create`` views double as edit views: pass a ``pk`` and they bind to
that existing document instead of a blank one. :func:`document_edit` is the
single entry point that picks the right one from a stored document's type.
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


def _save_positioned_children(formset, document: Document) -> None:
    """Persist an inline formset's rows, numbered 1..n in their on-screen order.

    Shared by the invoice/offer positions and the contract clauses. Renumbering
    *every* surviving row — not only the ones the user changed — keeps the order
    a clean, gap-free sequence when a document is edited later, not just when it
    is first created.
    """
    formset.instance = document
    formset.save(commit=False)
    for deleted in formset.deleted_objects:
        deleted.delete()
    position = 0
    for form in formset.forms:
        if form in formset.deleted_forms:
            continue
        if not getattr(form, "cleaned_data", None):
            continue
        position += 1
        form.instance.position = position
        form.instance.save()


def _document_for_edit(request: HttpRequest, pk: int | None) -> Document | None:
    """Return the owner's document to edit, or ``None`` for a fresh create form."""
    if pk is None:
        return None
    return get_object_or_404(Document, pk=pk, user=request.user)


def _new_document_initial(request: HttpRequest) -> dict[str, object]:
    """Sensible starting values for a blank document form.

    Pre-fills today's date and, when ``?recipient=<id>`` points at one of the
    user's address-book entries, that recipient's fields — so the mask arrives
    filled where it sensibly can be.
    """
    initial: dict[str, object] = {"date": datetime.date.today()}
    recipient_id = request.GET.get("recipient")
    if recipient_id:
        recipient = get_object_or_404(Recipient, pk=recipient_id, user=request.user)
        initial.update(recipient.as_document_initial())
    return initial


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
def invoice_create(request: HttpRequest, pk: int | None = None) -> HttpResponse:
    """Create or edit a Rechnung: invoice fields plus a positions formset.

    A fresh form arrives pre-filled where it sensibly can be — today's date, the
    user's standard sender profile, and (via ``?recipient=<id>``) a chosen
    address-book entry — so the user mostly fills in the positions. With a ``pk``
    it edits that existing document instead. On success the document and its
    positions are stored and the user lands on the PDF preview.
    """
    document = _document_for_edit(request, pk)
    if request.method == "POST":
        form = InvoiceForm(request.POST, user=request.user, instance=document)
        formset = InvoiceItemFormSet(request.POST, instance=document)
        if form.is_valid() and formset.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.doc_type = Document.Type.INVOICE
            document.save()
            _save_positioned_children(formset, document)
            messages.success(request, "Rechnung gespeichert.")
            return redirect("documents:document_preview", pk=document.pk)
    elif document is not None:
        form = InvoiceForm(user=request.user, instance=document)
        formset = InvoiceItemFormSet(instance=document)
    else:
        form = InvoiceForm(user=request.user, initial=_new_document_initial(request))
        formset = InvoiceItemFormSet()
    return render(
        request,
        "documents/invoice_form.html",
        {"form": form, "formset": formset, "is_edit": document is not None},
    )


@login_required
def offer_create(request: HttpRequest, pk: int | None = None) -> HttpResponse:
    """Create or edit an Angebot: offer fields plus a positions formset.

    Mirrors :func:`invoice_create` — today's date, the standard sender and an
    optional ``?recipient=<id>`` address-book entry are pre-filled, or a ``pk``
    edits an existing document — but stores a document of type Angebot. The
    validity date carries py_doc's ``valid_until``; on success the user lands on
    the PDF preview.
    """
    document = _document_for_edit(request, pk)
    if request.method == "POST":
        form = OfferForm(request.POST, user=request.user, instance=document)
        formset = OfferItemFormSet(request.POST, instance=document)
        if form.is_valid() and formset.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.doc_type = Document.Type.OFFER
            document.save()
            _save_positioned_children(formset, document)
            messages.success(request, "Angebot gespeichert.")
            return redirect("documents:document_preview", pk=document.pk)
    elif document is not None:
        form = OfferForm(user=request.user, instance=document)
        formset = OfferItemFormSet(instance=document)
    else:
        form = OfferForm(user=request.user, initial=_new_document_initial(request))
        formset = OfferItemFormSet()
    return render(
        request,
        "documents/offer_form.html",
        {"form": form, "formset": formset, "is_edit": document is not None},
    )


@login_required
def contract_create(request: HttpRequest, pk: int | None = None) -> HttpResponse:
    """Create or edit a Vertrag: contract fields plus a clauses formset.

    Mirrors :func:`invoice_create` — today's date, the standard sender and an
    optional ``?recipient=<id>`` address-book entry are pre-filled, or a ``pk``
    edits an existing document — but stores a document of type Vertrag, where the
    sender and recipient are the two parties and the formset holds the numbered
    §-clauses. On success the user lands on the PDF preview.
    """
    document = _document_for_edit(request, pk)
    if request.method == "POST":
        form = ContractForm(request.POST, user=request.user, instance=document)
        formset = ContractClauseFormSet(request.POST, instance=document)
        if form.is_valid() and formset.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.doc_type = Document.Type.CONTRACT
            document.save()
            _save_positioned_children(formset, document)
            messages.success(request, "Vertrag gespeichert.")
            return redirect("documents:document_preview", pk=document.pk)
    elif document is not None:
        form = ContractForm(user=request.user, instance=document)
        formset = ContractClauseFormSet(instance=document)
    else:
        form = ContractForm(user=request.user, initial=_new_document_initial(request))
        formset = ContractClauseFormSet()
    return render(
        request,
        "documents/contract_form.html",
        {"form": form, "formset": formset, "is_edit": document is not None},
    )


@login_required
def reminder_create(request: HttpRequest, pk: int | None = None) -> HttpResponse:
    """Create or edit a Zahlungserinnerung: reminder fields → saved Document.

    Mirrors :func:`invoice_create` — today's date, the standard sender and an
    optional ``?recipient=<id>`` address-book entry are pre-filled, or a ``pk``
    edits an existing document — but stores a document of type Zahlungserinnerung.
    A reminder has no positions, so it is a flat form (no formset); on success
    the user lands on the PDF preview.
    """
    document = _document_for_edit(request, pk)
    if request.method == "POST":
        form = ReminderForm(request.POST, user=request.user, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.doc_type = Document.Type.REMINDER
            document.save()
            messages.success(request, "Zahlungserinnerung gespeichert.")
            return redirect("documents:document_preview", pk=document.pk)
    elif document is not None:
        form = ReminderForm(user=request.user, instance=document)
    else:
        form = ReminderForm(user=request.user, initial=_new_document_initial(request))
    return render(
        request,
        "documents/reminder_form.html",
        {"form": form, "is_edit": document is not None},
    )


def _pdf_filename(document: Document) -> str:
    """Build a human-friendly download name like ``Rechnung_2026-0001.pdf``.

    The document number may contain a slash (``2026/0001``), which is illegal in
    a filename, so it is replaced; spaces become underscores so the name stays a
    single token for browsers and shells.
    """
    label = document.get_doc_type_display()
    safe_number = document.number.replace("/", "-").replace(" ", "_")
    return f"{label}_{safe_number}.pdf"


@login_required
def document_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    """Stream a saved document as a DIN 5008 Form-A PDF.

    The model already knows how to render itself (:meth:`Document.render_pdf`);
    this view only wraps the bytes in an HTTP response scoped to the owner. By
    default the PDF opens inline (so the preview page can embed it); ``?download=1``
    forces a download with a sensible filename.
    """
    document = get_object_or_404(Document, pk=pk, user=request.user)
    response = HttpResponse(document.render_pdf(), content_type="application/pdf")
    disposition = "attachment" if request.GET.get("download") else "inline"
    response["Content-Disposition"] = (
        f'{disposition}; filename="{_pdf_filename(document)}"'
    )
    return response


@login_required
def document_preview(request: HttpRequest, pk: int) -> HttpResponse:
    """Show a saved document's PDF inline with a download button.

    Users land here straight after creating a document, so they immediately see
    the finished Form-A page and can download it. The PDF itself is served by
    :func:`document_pdf`; this page just embeds that URL.
    """
    document = get_object_or_404(Document, pk=pk, user=request.user)
    return render(
        request,
        "documents/document_preview.html",
        {"document": document},
    )


@login_required
def document_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit an existing document by routing to the create view for its type.

    The four create masks already know how to bind to an existing document; this
    view just looks at the stored type and hands off to the matching one, so the
    detail page only needs a single „Bearbeiten" link regardless of document type.
    """
    document = get_object_or_404(Document, pk=pk, user=request.user)
    edit_views = {
        Document.Type.INVOICE: invoice_create,
        Document.Type.OFFER: offer_create,
        Document.Type.CONTRACT: contract_create,
        Document.Type.REMINDER: reminder_create,
    }
    return edit_views[Document.Type(document.doc_type)](request, pk=pk)


@login_required
def document_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete one of the current user's documents after a confirmation step."""
    document = get_object_or_404(Document, pk=pk, user=request.user)
    if request.method == "POST":
        document.delete()
        messages.success(request, "Dokument gelöscht.")
        return redirect("dashboard")
    return render(
        request,
        "documents/document_confirm_delete.html",
        {"document": document},
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
