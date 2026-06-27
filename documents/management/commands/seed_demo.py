"""Populate the database with a ready-to-explore demo account.

Running ``python manage.py seed_demo`` creates (or resets) a single demo user
with a default sender profile, a small address book and one document of every
type — so a first-time evaluator can log in and immediately see filled-in
documents and working PDFs instead of empty lists.

The command is idempotent: it deletes the existing demo user (cascading away
the old demo data) and rebuilds everything from scratch, so re-running always
yields the same clean state. It only ever touches the dedicated demo user, never
real accounts.
"""

from __future__ import annotations

import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import SenderProfile
from documents.models import Document, DocumentClause, DocumentItem, Recipient

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "belegwerk-demo"


class Command(BaseCommand):
    help = "Create a demo user with a sender profile and example documents."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        user = self._reset_demo_user()
        sender = self._create_sender_profile(user)
        recipients = self._create_recipients(user)
        self._create_invoice(user, sender, recipients[0])
        self._create_offer(user, sender, recipients[0])
        self._create_contract(user, sender, recipients[1])
        self._create_reminder(user, sender, recipients[0])
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo-Daten angelegt. Login: {DEMO_USERNAME} / {DEMO_PASSWORD}"
            )
        )

    def _reset_demo_user(self) -> User:
        """Drop any previous demo user and its data, then recreate it.

        Documents are deleted first on purpose: ``Document.sender`` is a PROTECT
        relation to the sender profile, so cascading the user straight away would
        raise a ``ProtectedError``. Removing the documents lifts that protection,
        after which deleting the user cascades the remaining profiles/recipients.
        """
        existing = get_user_model().objects.filter(username=DEMO_USERNAME).first()
        if existing is not None:
            Document.objects.filter(user=existing).delete()
            existing.delete()
        return get_user_model().objects.create_user(
            username=DEMO_USERNAME, password=DEMO_PASSWORD
        )

    def _create_sender_profile(self, user: User) -> SenderProfile:
        return SenderProfile.objects.create(
            user=user,
            label="Meine Firma",
            name="Max Mustermann",
            company="Mustermann Webdesign GmbH",
            street="Musterstraße 1",
            postal_code="10115",
            city="Berlin",
            country="Deutschland",
            contact="Max Mustermann",
            email="kontakt@mustermann-webdesign.de",
            phone="+49 30 1234567",
            bank_name="Musterbank Berlin",
            iban="DE89370400440532013000",
            bic="COBADEFFXXX",
            tax_number="12/345/67890",
            vat_id="DE123456789",
            register_court="Amtsgericht Berlin",
            register_number="HRB 123456",
            is_default=True,
        )

    def _create_recipients(self, user: User) -> list[Recipient]:
        return [
            Recipient.objects.create(
                user=user,
                name="Erika Beispiel",
                company="Beispiel Handels AG",
                street="Beispielallee 42",
                postal_code="20095",
                city="Hamburg",
                country="Deutschland",
                email="einkauf@beispiel-ag.de",
                vat_id="DE987654321",
            ),
            Recipient.objects.create(
                user=user,
                name="Thomas Schneider",
                company="Schneider Consulting",
                street="Lindenweg 7",
                postal_code="80331",
                city="München",
                country="Deutschland",
                email="thomas@schneider-consulting.de",
            ),
        ]

    def _create_invoice(
        self, user: User, sender: SenderProfile, recipient: Recipient
    ) -> Document:
        document = Document.objects.create(
            user=user,
            sender=sender,
            doc_type=Document.Type.INVOICE,
            number="2026-0001",
            date=datetime.date(2026, 6, 1),
            subject="Rechnung 2026-0001",
            payment_terms="Zahlbar innerhalb von 14 Tagen ohne Abzug.",
            **recipient.as_document_initial(),
        )
        DocumentItem.objects.create(
            document=document,
            position=1,
            description="Konzeption & Design Website",
            quantity=1,
            unit="Pauschale",
            unit_price_cents=180000,
            vat_rate=0.19,
        )
        DocumentItem.objects.create(
            document=document,
            position=2,
            description="Frontend-Entwicklung",
            quantity=20,
            unit="Std",
            unit_price_cents=9500,
            vat_rate=0.19,
        )
        return document

    def _create_offer(
        self, user: User, sender: SenderProfile, recipient: Recipient
    ) -> Document:
        document = Document.objects.create(
            user=user,
            sender=sender,
            doc_type=Document.Type.OFFER,
            number="2026-A012",
            date=datetime.date(2026, 6, 5),
            subject="Angebot 2026-A012",
            valid_until=datetime.date(2026, 7, 5),
            **recipient.as_document_initial(),
        )
        DocumentItem.objects.create(
            document=document,
            position=1,
            description="Relaunch Onlineshop",
            quantity=1,
            unit="Pauschale",
            unit_price_cents=450000,
            vat_rate=0.19,
        )
        return document

    def _create_contract(
        self, user: User, sender: SenderProfile, recipient: Recipient
    ) -> Document:
        document = Document.objects.create(
            user=user,
            sender=sender,
            doc_type=Document.Type.CONTRACT,
            number="2026-V003",
            date=datetime.date(2026, 6, 10),
            subject="Wartungsvertrag 2026-V003",
            party_a_label="Auftraggeber",
            party_b_label="Auftragnehmer",
            **recipient.as_document_initial(),
        )
        DocumentClause.objects.create(
            document=document,
            position=1,
            heading="Vertragsgegenstand",
            body=(
                "Der Auftragnehmer übernimmt die laufende technische Wartung der "
                "Website des Auftraggebers."
            ),
        )
        DocumentClause.objects.create(
            document=document,
            position=2,
            heading="Vergütung",
            body="Die monatliche Pauschale beträgt 150,00 EUR zzgl. USt.",
        )
        return document

    def _create_reminder(
        self, user: User, sender: SenderProfile, recipient: Recipient
    ) -> Document:
        return Document.objects.create(
            user=user,
            sender=sender,
            doc_type=Document.Type.REMINDER,
            number="2026-M001",
            date=datetime.date(2026, 6, 20),
            subject="Zahlungserinnerung zur Rechnung 2026-0001",
            ref_invoice_number="2026-0001",
            ref_invoice_date=datetime.date(2026, 6, 1),
            ref_amount_cents=394100,
            reminder_stage="Zahlungserinnerung",
            reminder_fee_cents=0,
            new_deadline=datetime.date(2026, 7, 1),
            **recipient.as_document_initial(),
        )
