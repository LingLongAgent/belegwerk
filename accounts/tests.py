"""Tests for the sender profile (Absender) feature — model, mapping, and views.

The model's only real logic is the py_doc mapping and the single-default rule, so
those get focused tests; the views are checked for ownership scoping (a user must
never reach another user's profile) and the create/edit/delete round-trips.
"""

from __future__ import annotations

import factory
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from py_doc import Sender

from .models import SenderProfile

EMPTY_OPTIONAL_FIELDS = {
    "company": "",
    "street": "",
    "postal_code": "",
    "city": "",
    "country": "",
    "contact": "",
    "email": "",
    "phone": "",
    "bank_name": "",
    "iban": "",
    "bic": "",
    "tax_number": "",
    "vat_id": "",
    "register_court": "",
    "register_number": "",
}


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user{n}")
    # Tests authenticate via client.force_login, so no usable password is needed.


class SenderProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SenderProfile

    user = factory.SubFactory(UserFactory)
    label = factory.Faker("company", locale="de_DE")
    name = factory.Faker("name", locale="de_DE")
    company = factory.Faker("company", locale="de_DE")
    street = factory.Faker("street_address", locale="de_DE")
    postal_code = factory.Faker("postcode", locale="de_DE")
    city = factory.Faker("city", locale="de_DE")
    iban = factory.Faker("iban", locale="de_DE")


class SenderProfileModelTest(TestCase):
    def test_to_sender_maps_all_fields(self) -> None:
        profile = SenderProfileFactory(
            name="Max Mustermann",
            company="Mustermann GmbH",
            street="Musterstr. 1",
            postal_code="10115",
            city="Berlin",
            bank_name="Musterbank",
            iban="DE89370400440532013000",
            bic="COBADEFFXXX",
            tax_number="12/345/67890",
            vat_id="DE123456789",
            register_court="Amtsgericht Berlin",
            register_number="HRB 12345",
        )
        sender = profile.to_sender()
        self.assertIsInstance(sender, Sender)
        self.assertEqual(sender.party.name, "Max Mustermann")
        self.assertEqual(sender.party.company, "Mustermann GmbH")
        self.assertEqual(sender.party.postal_code, "10115")
        self.assertEqual(sender.iban, "DE89370400440532013000")
        self.assertEqual(sender.vat_id, "DE123456789")
        self.assertEqual(sender.party.vat_id, "DE123456789")
        # Footer assembled by py_doc must carry the bank and tax data.
        footer = " ".join(sender.footer_lines())
        self.assertIn("DE89370400440532013000", footer)
        self.assertIn("HRB 12345", footer)

    def test_to_sender_turns_blanks_into_none(self) -> None:
        profile = SenderProfileFactory(
            name="Erika Beispiel",
            company="",
            street="",
            iban="",
            bic="",
        )
        sender = profile.to_sender()
        self.assertIsNone(sender.party.company)
        self.assertIsNone(sender.party.street)
        self.assertIsNone(sender.iban)
        # No bank data → no footer noise at all.
        self.assertEqual(sender.footer_lines(), [])

    def test_only_one_default_per_user(self) -> None:
        user = UserFactory()
        first = SenderProfileFactory(user=user, is_default=True)
        second = SenderProfileFactory(user=user, is_default=True)
        first.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)
        self.assertEqual(
            SenderProfile.objects.filter(user=user, is_default=True).count(), 1
        )

    def test_default_rule_is_per_user(self) -> None:
        alice = SenderProfileFactory(is_default=True)
        bob = SenderProfileFactory(is_default=True)
        alice.refresh_from_db()
        # A second user's default must not touch the first user's default.
        self.assertTrue(alice.is_default)
        self.assertTrue(bob.is_default)


class SenderProfileViewTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_list_requires_login(self) -> None:
        self.client.logout()
        response = self.client.get(reverse("profile_list"))
        self.assertEqual(response.status_code, 302)

    def test_list_shows_only_own_profiles(self) -> None:
        mine = SenderProfileFactory(user=self.user, label="Meins")
        SenderProfileFactory(label="Fremdes")  # belongs to another user
        response = self.client.get(reverse("profile_list"))
        self.assertContains(response, "Meins")
        self.assertNotContains(response, "Fremdes")
        self.assertEqual(list(response.context["profiles"]), [mine])

    def test_create_attaches_owner(self) -> None:
        response = self.client.post(
            reverse("profile_create"),
            {
                "label": "Meine Firma",
                "name": "Max Mustermann",
                **EMPTY_OPTIONAL_FIELDS,
                "company": "Mustermann GmbH",
                "is_default": "on",
            },
        )
        self.assertRedirects(response, reverse("profile_list"))
        profile = SenderProfile.objects.get(label="Meine Firma")
        self.assertEqual(profile.user, self.user)
        self.assertTrue(profile.is_default)

    def test_create_rejects_missing_required_fields(self) -> None:
        response = self.client.post(reverse("profile_create"), {"label": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SenderProfile.objects.count(), 0)
        self.assertContains(response, "field-error")

    def test_edit_updates_profile(self) -> None:
        profile = SenderProfileFactory(user=self.user, label="Alt", name="Alt Name")
        response = self.client.post(
            reverse("profile_edit", args=[profile.pk]),
            {"label": "Neu", "name": "Neu Name", **EMPTY_OPTIONAL_FIELDS},
        )
        self.assertRedirects(response, reverse("profile_list"))
        profile.refresh_from_db()
        self.assertEqual(profile.label, "Neu")
        self.assertEqual(profile.name, "Neu Name")

    def test_cannot_edit_other_users_profile(self) -> None:
        other = SenderProfileFactory(label="Fremd")
        response = self.client.get(reverse("profile_edit", args=[other.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete_removes_profile(self) -> None:
        profile = SenderProfileFactory(user=self.user)
        response = self.client.post(reverse("profile_delete", args=[profile.pk]))
        self.assertRedirects(response, reverse("profile_list"))
        self.assertFalse(SenderProfile.objects.filter(pk=profile.pk).exists())

    def test_cannot_delete_other_users_profile(self) -> None:
        other = SenderProfileFactory()
        response = self.client.post(reverse("profile_delete", args=[other.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(SenderProfile.objects.filter(pk=other.pk).exists())
