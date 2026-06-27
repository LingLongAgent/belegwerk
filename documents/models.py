"""The stored document — the shared core of every Rechnung, Angebot, Vertrag
and Zahlungserinnerung.

A :class:`Document` keeps the parts every letter type has in common: who issued
it (a saved :class:`~accounts.models.SenderProfile`), who receives it (an inline
recipient address), and the metadata that prints in the Informationsblock
(number, date, subject). The type-specific content — invoice positions, contract
clauses, reminder details — is added by the later milestones; this model is what
they all hang off.

The two ``to_*`` methods translate the stored row into exactly the py_doc inputs
the engine expects (:class:`py_doc.Party` and :class:`py_doc.DocumentMeta`), so
the PDF views never have to know py_doc's shape — the same separation the sender
profile already follows.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from py_doc import DocumentMeta, Party

from accounts.models import SenderProfile


class Document(models.Model):
    """One saved document belonging to a user, addressed to one recipient.

    The recipient is stored inline (its own fields) rather than as a relation so
    a document stays a faithful record of what was sent even if an address book
    entry is later edited or deleted; M3 adds the convenience of copying a saved
    recipient into these fields.
    """

    class Type(models.TextChoices):
        INVOICE = "invoice", "Rechnung"
        OFFER = "offer", "Angebot"
        CONTRACT = "contract", "Vertrag"
        REMINDER = "reminder", "Zahlungserinnerung"

    # Which Informationsblock label the document number prints under, per type.
    NUMBER_LABELS = {
        Type.INVOICE: "Rechnungs-Nr.",
        Type.OFFER: "Angebots-Nr.",
        Type.CONTRACT: "Vertrags-Nr.",
        Type.REMINDER: "Vorgangs-Nr.",
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    sender = models.ForeignKey(
        SenderProfile,
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name="Absender",
    )
    doc_type = models.CharField("Dokumenttyp", max_length=20, choices=Type.choices)

    number = models.CharField(
        "Nummer",
        max_length=60,
        help_text="Fortlaufende Nummer, z. B. „2026-0001“.",
    )
    date = models.DateField("Datum")
    subject = models.CharField(
        "Betreff",
        max_length=200,
        help_text="Erscheint fett über dem Text, z. B. „Rechnung 2026-0001“.",
    )

    # --- Empfänger (inline; py_doc Party) ---
    recipient_name = models.CharField("Name", max_length=200)
    recipient_company = models.CharField("Firma", max_length=200, blank=True)
    recipient_street = models.CharField("Straße & Hausnr.", max_length=200, blank=True)
    recipient_postal_code = models.CharField("PLZ", max_length=20, blank=True)
    recipient_city = models.CharField("Ort", max_length=120, blank=True)
    recipient_country = models.CharField("Land", max_length=120, blank=True)
    recipient_contact = models.CharField("Ansprechpartner", max_length=200, blank=True)
    recipient_email = models.EmailField("E-Mail", blank=True)
    recipient_phone = models.CharField("Telefon", max_length=60, blank=True)
    recipient_vat_id = models.CharField("USt-IdNr.", max_length=40, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_doc_type_display()} {self.number}"

    @property
    def number_label(self) -> str:
        """The Informationsblock label this document's number prints under."""
        return self.NUMBER_LABELS[self.Type(self.doc_type)]

    def to_recipient(self) -> Party:
        """Translate the inline recipient fields into a py_doc :class:`Party`.

        Empty strings become ``None`` so py_doc omits absent address lines rather
        than printing blank ones — the same rule the sender profile applies.
        """
        return Party(
            name=self.recipient_name,
            company=self.recipient_company or None,
            street=self.recipient_street or None,
            postal_code=self.recipient_postal_code or None,
            city=self.recipient_city or None,
            country=self.recipient_country or None,
            contact=self.recipient_contact or None,
            email=self.recipient_email or None,
            phone=self.recipient_phone or None,
            vat_id=self.recipient_vat_id or None,
        )

    def to_meta(self) -> DocumentMeta:
        """Build the py_doc :class:`DocumentMeta` (subject, German date, info block).

        The date is formatted to the German ``TT.MM.JJJJ`` form py_doc prints
        verbatim, and the info block carries the type-specific number label plus
        the date so both appear right-aligned in the Informationsblock.
        """
        formatted_date = self.date.strftime("%d.%m.%Y")
        return DocumentMeta(
            subject=self.subject,
            date=formatted_date,
            info_fields=[
                (self.number_label, self.number),
                ("Datum", formatted_date),
            ],
        )


# The address fields a Recipient shares with a Document's inline recipient. Kept
# in one place so the address book can copy an entry straight into a new document
# without either side having to spell the field list out twice.
RECIPIENT_ADDRESS_FIELDS = (
    "name",
    "company",
    "street",
    "postal_code",
    "city",
    "country",
    "contact",
    "email",
    "phone",
    "vat_id",
)


class Recipient(models.Model):
    """A saved recipient (Empfänger/Kunde) in a user's address book.

    Belegwerk stores each document's recipient inline (on :class:`Document`) so a
    finished document never changes when an address is edited later. This model is
    the convenience layer above that: a user enters a customer once and can copy
    it into any new document. The address fields mirror :class:`Document`'s
    ``recipient_*`` fields exactly, which lets :meth:`as_document_initial` hand a
    document form ready-to-use initial values.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipients",
    )

    name = models.CharField("Name", max_length=200)
    company = models.CharField("Firma", max_length=200, blank=True)
    street = models.CharField("Straße & Hausnr.", max_length=200, blank=True)
    postal_code = models.CharField("PLZ", max_length=20, blank=True)
    city = models.CharField("Ort", max_length=120, blank=True)
    country = models.CharField("Land", max_length=120, blank=True)
    contact = models.CharField("Ansprechpartner", max_length=200, blank=True)
    email = models.EmailField("E-Mail", blank=True)
    phone = models.CharField("Telefon", max_length=60, blank=True)
    vat_id = models.CharField("USt-IdNr.", max_length=40, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Company first when present, otherwise the person's name — the label a
        # user scans the address book by.
        ordering = ["company", "name"]

    def __str__(self) -> str:
        return self.company or self.name

    def to_recipient(self) -> Party:
        """Translate this address-book entry into a py_doc :class:`Party`.

        Empty strings become ``None`` so py_doc omits absent address lines — the
        same rule :meth:`Document.to_recipient` and the sender profile follow.
        """
        return Party(
            name=self.name,
            company=self.company or None,
            street=self.street or None,
            postal_code=self.postal_code or None,
            city=self.city or None,
            country=self.country or None,
            contact=self.contact or None,
            email=self.email or None,
            phone=self.phone or None,
            vat_id=self.vat_id or None,
        )

    def as_document_initial(self) -> dict[str, str]:
        """Return this entry as ``recipient_*`` initial values for a document form.

        M4+ document forms pre-fill their inline recipient section from a chosen
        address-book entry; the keys match :class:`Document`'s field names so the
        result can be passed straight to a form's ``initial``.
        """
        return {
            f"recipient_{field}": getattr(self, field)
            for field in RECIPIENT_ADDRESS_FIELDS
        }
