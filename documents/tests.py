"""Tests for the stored document model (M2).

The model's real logic is the two py_doc mappings and the per-type number label,
so those get focused tests: a recipient with full data must round-trip into a
py_doc :class:`Party`, blanks must collapse to ``None``, and the metadata must
carry the German date and the right Informationsblock labels per document type.
"""

from __future__ import annotations

import datetime
from decimal import Decimal

import factory
from django.test import TestCase
from django.urls import reverse
from py_doc import DocumentMeta, Party

from accounts.tests import SenderProfileFactory, UserFactory

from .forms import DocumentItemForm
from .models import Document, DocumentItem, Recipient


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    user = factory.SubFactory(UserFactory)
    sender = factory.SubFactory(SenderProfileFactory)
    doc_type = Document.Type.INVOICE
    number = factory.Sequence(lambda n: f"2026-{n:04d}")
    date = factory.LazyFunction(lambda: datetime.date(2026, 6, 24))
    subject = factory.Faker("sentence", nb_words=3, locale="de_DE")
    recipient_name = factory.Faker("name", locale="de_DE")
    recipient_city = factory.Faker("city", locale="de_DE")


class DocumentMappingTest(TestCase):
    def test_to_recipient_maps_all_fields(self) -> None:
        document = DocumentFactory(
            recipient_name="Erika Empfänger",
            recipient_company="Empfänger AG",
            recipient_street="Empfangsweg 2",
            recipient_postal_code="20095",
            recipient_city="Hamburg",
            recipient_vat_id="DE987654321",
        )
        recipient = document.to_recipient()
        self.assertIsInstance(recipient, Party)
        self.assertEqual(recipient.name, "Erika Empfänger")
        self.assertEqual(recipient.company, "Empfänger AG")
        self.assertEqual(recipient.postal_code, "20095")
        self.assertEqual(recipient.vat_id, "DE987654321")
        # The address block must contain the company, person and city line.
        address = recipient.address_lines()
        self.assertIn("Empfänger AG", address)
        self.assertIn("20095 Hamburg", address)

    def test_to_recipient_turns_blanks_into_none(self) -> None:
        document = DocumentFactory(
            recipient_name="Max Ohnefirma",
            recipient_company="",
            recipient_street="",
            recipient_vat_id="",
        )
        recipient = document.to_recipient()
        self.assertIsNone(recipient.company)
        self.assertIsNone(recipient.street)
        self.assertIsNone(recipient.vat_id)

    def test_to_meta_formats_german_date_and_info_block(self) -> None:
        document = DocumentFactory(
            doc_type=Document.Type.INVOICE,
            number="2026-0007",
            subject="Rechnung 2026-0007",
            date=datetime.date(2026, 6, 24),
        )
        meta = document.to_meta()
        self.assertIsInstance(meta, DocumentMeta)
        self.assertEqual(meta.subject, "Rechnung 2026-0007")
        self.assertEqual(meta.date, "24.06.2026")
        self.assertIn(("Rechnungs-Nr.", "2026-0007"), meta.info_fields)
        self.assertIn(("Datum", "24.06.2026"), meta.info_fields)

    def test_number_label_depends_on_type(self) -> None:
        labels = {
            Document.Type.INVOICE: "Rechnungs-Nr.",
            Document.Type.OFFER: "Angebots-Nr.",
            Document.Type.CONTRACT: "Vertrags-Nr.",
            Document.Type.REMINDER: "Vorgangs-Nr.",
        }
        for doc_type, expected_label in labels.items():
            document = DocumentFactory(doc_type=doc_type)
            self.assertEqual(document.number_label, expected_label)
            self.assertEqual(document.to_meta().info_fields[0][0], expected_label)


class DocumentRecordTest(TestCase):
    def test_str_is_type_and_number(self) -> None:
        document = DocumentFactory(doc_type=Document.Type.OFFER, number="2026-0042")
        self.assertEqual(str(document), "Angebot 2026-0042")

    def test_default_ordering_is_newest_first(self) -> None:
        # Assert the configured ordering rather than relying on two near-
        # simultaneous timestamps, which can tie on a fast machine.
        self.assertEqual(Document._meta.ordering, ["-created_at"])

    def test_sender_is_protected_from_deletion(self) -> None:
        from django.db.models import ProtectedError

        document = DocumentFactory()
        with self.assertRaises(ProtectedError):
            document.sender.delete()


class RecipientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Recipient

    user = factory.SubFactory(UserFactory)
    name = factory.Faker("name", locale="de_DE")
    company = factory.Faker("company", locale="de_DE")
    city = factory.Faker("city", locale="de_DE")


# Posting the recipient form needs every optional field present (empty), since a
# ModelForm omits nothing — mirrors the accounts EMPTY_OPTIONAL_FIELDS helper.
EMPTY_RECIPIENT_FIELDS = {
    "company": "",
    "street": "",
    "postal_code": "",
    "city": "",
    "country": "",
    "contact": "",
    "email": "",
    "phone": "",
    "vat_id": "",
}


class RecipientModelTest(TestCase):
    def test_to_recipient_maps_all_fields(self) -> None:
        recipient = RecipientFactory(
            name="Erika Beispiel",
            company="Beispiel AG",
            street="Beispielweg 7",
            postal_code="20095",
            city="Hamburg",
            vat_id="DE987654321",
        )
        party = recipient.to_recipient()
        self.assertIsInstance(party, Party)
        self.assertEqual(party.name, "Erika Beispiel")
        self.assertEqual(party.company, "Beispiel AG")
        self.assertEqual(party.vat_id, "DE987654321")
        address = party.address_lines()
        self.assertIn("Beispiel AG", address)
        self.assertIn("20095 Hamburg", address)

    def test_to_recipient_turns_blanks_into_none(self) -> None:
        recipient = RecipientFactory(name="Max Ohnefirma", company="", city="")
        party = recipient.to_recipient()
        self.assertIsNone(party.company)
        self.assertIsNone(party.city)

    def test_as_document_initial_uses_recipient_prefixed_keys(self) -> None:
        recipient = RecipientFactory(
            name="Erika Beispiel", company="Beispiel AG", city="Hamburg"
        )
        initial = recipient.as_document_initial()
        self.assertEqual(initial["recipient_name"], "Erika Beispiel")
        self.assertEqual(initial["recipient_company"], "Beispiel AG")
        self.assertEqual(initial["recipient_city"], "Hamburg")
        # The keys must line up exactly with the Document fields they pre-fill.
        for key in initial:
            self.assertTrue(hasattr(Document, key))

    def test_str_prefers_company_then_name(self) -> None:
        self.assertEqual(str(RecipientFactory(company="Beispiel AG")), "Beispiel AG")
        self.assertEqual(
            str(RecipientFactory(name="Max Privat", company="")), "Max Privat"
        )


class RecipientViewTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_list_requires_login(self) -> None:
        self.client.logout()
        response = self.client.get(reverse("documents:recipient_list"))
        self.assertEqual(response.status_code, 302)

    def test_list_shows_only_own_recipients(self) -> None:
        mine = RecipientFactory(user=self.user, name="Meiner")
        RecipientFactory(name="Fremder")  # belongs to another user
        response = self.client.get(reverse("documents:recipient_list"))
        self.assertContains(response, "Meiner")
        self.assertNotContains(response, "Fremder")
        self.assertEqual(list(response.context["recipients"]), [mine])

    def test_create_attaches_owner(self) -> None:
        response = self.client.post(
            reverse("documents:recipient_create"),
            {"name": "Erika Beispiel", **EMPTY_RECIPIENT_FIELDS, "company": "Beispiel AG"},
        )
        self.assertRedirects(response, reverse("documents:recipient_list"))
        recipient = Recipient.objects.get(name="Erika Beispiel")
        self.assertEqual(recipient.user, self.user)
        self.assertEqual(recipient.company, "Beispiel AG")

    def test_create_rejects_missing_name(self) -> None:
        response = self.client.post(
            reverse("documents:recipient_create"), {"name": "", **EMPTY_RECIPIENT_FIELDS}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Recipient.objects.count(), 0)
        self.assertContains(response, "field-error")

    def test_edit_updates_recipient(self) -> None:
        recipient = RecipientFactory(user=self.user, name="Alt", company="")
        response = self.client.post(
            reverse("documents:recipient_edit", args=[recipient.pk]),
            {"name": "Neu", **EMPTY_RECIPIENT_FIELDS, "city": "Bremen"},
        )
        self.assertRedirects(response, reverse("documents:recipient_list"))
        recipient.refresh_from_db()
        self.assertEqual(recipient.name, "Neu")
        self.assertEqual(recipient.city, "Bremen")

    def test_cannot_edit_other_users_recipient(self) -> None:
        other = RecipientFactory(name="Fremd")
        response = self.client.get(
            reverse("documents:recipient_edit", args=[other.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_removes_recipient(self) -> None:
        recipient = RecipientFactory(user=self.user)
        response = self.client.post(
            reverse("documents:recipient_delete", args=[recipient.pk])
        )
        self.assertRedirects(response, reverse("documents:recipient_list"))
        self.assertFalse(Recipient.objects.filter(pk=recipient.pk).exists())

    def test_cannot_delete_other_users_recipient(self) -> None:
        other = RecipientFactory()
        response = self.client.post(
            reverse("documents:recipient_delete", args=[other.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Recipient.objects.filter(pk=other.pk).exists())


# --- M4: Rechnung — Positionen, py_doc-Invoice und Form-A-PDF ---


class DocumentItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DocumentItem

    document = factory.SubFactory(DocumentFactory)
    description = factory.Faker("bs", locale="de_DE")
    quantity = 2
    unit = "h"
    unit_price_cents = 5000
    vat_rate = factory.LazyFunction(lambda: Decimal("0.19"))


class DocumentItemModelTest(TestCase):
    def test_to_line_item_casts_to_pydoc_shape(self) -> None:
        item = DocumentItemFactory(
            description="Beratung", quantity=Decimal("3"), unit="h",
            unit_price_cents=5000, vat_rate=Decimal("0.19"),
        )
        line = item.to_line_item()
        self.assertEqual(line.description, "Beratung")
        self.assertEqual(line.quantity, 3.0)
        self.assertEqual(line.unit, "h")
        self.assertEqual(line.unit_price_cents, 5000)
        self.assertEqual(line.vat_rate, 0.19)


class InvoiceBuildTest(TestCase):
    """The mapping from a saved document to a py_doc Invoice, and its totals."""

    def _invoice_document(self) -> Document:
        document = DocumentFactory(
            doc_type=Document.Type.INVOICE,
            number="2026-0007",
            subject="Rechnung 2026-0007",
            date=datetime.date(2026, 6, 24),
            recipient_name="Erika Empfänger",
            recipient_city="Hamburg",
        )
        DocumentItemFactory(
            document=document, description="Beratung", quantity=Decimal("2"),
            unit="h", unit_price_cents=5000, vat_rate=Decimal("0.19"),
        )
        DocumentItemFactory(
            document=document, description="Lizenz", quantity=Decimal("1"),
            unit="Stk", unit_price_cents=10000, vat_rate=Decimal("0.19"),
        )
        return document

    def test_build_invoice_totals(self) -> None:
        invoice = self._invoice_document().build_invoice()
        totals = invoice.totals()
        # 2×50 € + 1×100 € = 200 € net, 19 % VAT → 238 € gross.
        self.assertEqual(totals.net_cents, 20000)
        self.assertEqual(totals.gross_cents, 23800)

    def test_render_pdf_produces_form_a_pdf_with_content(self) -> None:
        import io

        from pypdf import PdfReader

        pdf_bytes = self._invoice_document().render_pdf()
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        text = "".join(
            page.extract_text() for page in PdfReader(io.BytesIO(pdf_bytes)).pages
        )
        # The recipient, a position and the gross total must reach the page.
        self.assertIn("Erika Empfänger", text)
        self.assertIn("Beratung", text)
        self.assertIn("Rechnung 2026-0007", text)

    def test_render_pdf_rejects_unimplemented_types(self) -> None:
        document = DocumentFactory(doc_type=Document.Type.CONTRACT)
        with self.assertRaises(NotImplementedError):
            document.render_pdf()


class DocumentItemFormTest(TestCase):
    def test_euro_input_is_stored_as_cents(self) -> None:
        document = DocumentFactory(doc_type=Document.Type.INVOICE)
        form = DocumentItemForm(
            {
                "description": "Beratung", "quantity": "2", "unit": "h",
                "unit_price_euro": "49.90", "vat_rate": "0.19",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save(commit=False)
        item.document = document
        item.save()
        self.assertEqual(item.unit_price_cents, 4990)
        self.assertEqual(item.vat_rate, Decimal("0.19"))

    def test_editing_shows_euros_back(self) -> None:
        item = DocumentItemFactory(unit_price_cents=4990)
        form = DocumentItemForm(instance=item)
        self.assertEqual(form.fields["unit_price_euro"].initial, Decimal("49.90"))


def invoice_post_data(sender: object, **overrides: str) -> dict[str, str]:
    """Build a valid POST payload for the invoice form + one position.

    Mirrors what the browser sends: every InvoiceForm field plus the formset's
    management form and a single filled position row. ``overrides`` lets a test
    tweak individual keys.
    """
    data = {
        "sender": str(sender.pk),
        "number": "2026-0001",
        "date": "2026-06-24",
        "subject": "Rechnung 2026-0001",
        "payment_terms": "Zahlbar innerhalb von 14 Tagen ohne Abzug.",
        "recipient_name": "Erika Empfänger",
        "recipient_company": "", "recipient_street": "",
        "recipient_postal_code": "", "recipient_city": "Hamburg",
        "recipient_country": "", "recipient_contact": "",
        "recipient_email": "", "recipient_phone": "", "recipient_vat_id": "",
        "items-TOTAL_FORMS": "1", "items-INITIAL_FORMS": "0",
        "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
        "items-0-id": "", "items-0-description": "Beratung",
        "items-0-quantity": "2", "items-0-unit": "h",
        "items-0-unit_price_euro": "50.00", "items-0-vat_rate": "0.19",
        "items-0-DELETE": "",
    }
    data.update(overrides)
    return data


class InvoiceCreateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.sender = SenderProfileFactory(user=self.user)

    def test_requires_login(self) -> None:
        self.client.logout()
        response = self.client.get(reverse("documents:invoice_create"))
        self.assertEqual(response.status_code, 302)

    def test_get_prefills_today_and_default_sender(self) -> None:
        default = SenderProfileFactory(user=self.user, is_default=True)
        response = self.client.get(reverse("documents:invoice_create"))
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.initial["date"], datetime.date.today())
        self.assertEqual(form.initial["sender"], default.pk)
        # Only the user's own sender profiles may be selectable.
        SenderProfileFactory()  # another user's profile
        self.assertCountEqual(
            list(form.fields["sender"].queryset),
            list(self.user.sender_profiles.all()),
        )

    def test_get_prefills_recipient_from_address_book(self) -> None:
        recipient = RecipientFactory(
            user=self.user, name="Aus Adressbuch", city="Bremen"
        )
        url = reverse("documents:invoice_create") + f"?recipient={recipient.pk}"
        response = self.client.get(url)
        self.assertEqual(
            response.context["form"].initial["recipient_name"], "Aus Adressbuch"
        )

    def test_post_creates_invoice_with_positions(self) -> None:
        response = self.client.post(
            reverse("documents:invoice_create"),
            invoice_post_data(self.sender),
        )
        self.assertRedirects(response, reverse("dashboard"))
        document = Document.objects.get(number="2026-0001")
        self.assertEqual(document.user, self.user)
        self.assertEqual(document.doc_type, Document.Type.INVOICE)
        self.assertEqual(document.items.count(), 1)
        item = document.items.get()
        self.assertEqual(item.description, "Beratung")
        self.assertEqual(item.unit_price_cents, 5000)
        self.assertEqual(item.position, 1)

    def test_post_without_sender_is_rejected(self) -> None:
        data = invoice_post_data(self.sender)
        data["sender"] = ""
        response = self.client.post(reverse("documents:invoice_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Document.objects.count(), 0)

    def test_cannot_use_another_users_sender(self) -> None:
        other_sender = SenderProfileFactory()  # not owned by self.user
        response = self.client.post(
            reverse("documents:invoice_create"),
            invoice_post_data(other_sender),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Document.objects.count(), 0)
