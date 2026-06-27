"""Tests for the stored document model (M2).

The model's real logic is the two py_doc mappings and the per-type number label,
so those get focused tests: a recipient with full data must round-trip into a
py_doc :class:`Party`, blanks must collapse to ``None``, and the metadata must
carry the German date and the right Informationsblock labels per document type.
"""

from __future__ import annotations

import datetime

import factory
from django.test import TestCase
from py_doc import DocumentMeta, Party

from accounts.tests import SenderProfileFactory, UserFactory

from .models import Document


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
