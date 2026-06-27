"""Reusable issuer profiles (Absender) — the "from" side of every document.

A user fills in their company, banking and tax details once; Belegwerk then
reuses that profile on every Rechnung, Angebot, Vertrag and Zahlungserinnerung.
The fields mirror exactly what py_doc's :class:`Sender`/:class:`Party` expect, so
:meth:`SenderProfile.to_sender` can hand the PDF engine what it needs without the
views ever having to know py_doc's internal shape.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from py_doc import Party, Sender


class SenderProfile(models.Model):
    """One saved sender (Absender) belonging to a single user.

    A user may keep several profiles (e.g. a company and a private one) and mark
    one as the default that new documents pre-select.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sender_profiles",
    )
    label = models.CharField(
        "Profilname",
        max_length=120,
        help_text="Nur zur Unterscheidung, z. B. „Meine Firma“.",
    )

    # --- Identität & Anschrift (py_doc Party) ---
    name = models.CharField("Name", max_length=200)
    company = models.CharField("Firma", max_length=200, blank=True)
    street = models.CharField("Straße & Hausnr.", max_length=200, blank=True)
    postal_code = models.CharField("PLZ", max_length=20, blank=True)
    city = models.CharField("Ort", max_length=120, blank=True)
    country = models.CharField("Land", max_length=120, blank=True)
    contact = models.CharField("Ansprechpartner", max_length=200, blank=True)
    email = models.EmailField("E-Mail", blank=True)
    phone = models.CharField("Telefon", max_length=60, blank=True)

    # --- Bank & Steuer (py_doc Sender) ---
    bank_name = models.CharField("Bank", max_length=200, blank=True)
    iban = models.CharField("IBAN", max_length=40, blank=True)
    bic = models.CharField("BIC", max_length=20, blank=True)
    tax_number = models.CharField("Steuernummer", max_length=60, blank=True)
    vat_id = models.CharField("USt-IdNr.", max_length=40, blank=True)
    register_court = models.CharField("Registergericht", max_length=120, blank=True)
    register_number = models.CharField("Registernummer", max_length=60, blank=True)

    is_default = models.BooleanField("Standardprofil", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "label"]

    def __str__(self) -> str:
        return self.label

    def save(self, *args: object, **kwargs: object) -> None:
        """Keep at most one default profile per user.

        Marking a profile as default silently demotes any sibling that was the
        default before, so the rest of the app never has to reason about two
        defaults existing at once.
        """
        super().save(*args, **kwargs)
        if self.is_default:
            SenderProfile.objects.filter(user=self.user).exclude(pk=self.pk).update(
                is_default=False
            )

    def to_sender(self) -> Sender:
        """Translate this stored profile into the py_doc :class:`Sender` object.

        Empty strings become ``None`` because py_doc treats absent fields as
        ``None`` (and would otherwise print blank "IBAN " fragments in the
        footer). The single USt-IdNr. feeds both the party and the sender, which
        is where German documents print it.
        """
        party = Party(
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
        return Sender(
            party=party,
            bank_name=self.bank_name or None,
            iban=self.iban or None,
            bic=self.bic or None,
            tax_number=self.tax_number or None,
            vat_id=self.vat_id or None,
            register_court=self.register_court or None,
            register_number=self.register_number or None,
        )
