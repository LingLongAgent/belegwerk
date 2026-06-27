from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.tests import SenderProfileFactory
from documents.tests import DocumentFactory


class DashboardSmokeTest(TestCase):
    def test_redirects_anonymous(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    def test_renders_for_user(self):
        get_user_model().objects.create_user(username="u", password="test12345")
        self.client.login(username="u", password="test12345")
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Belegwerk")
        self.assertContains(r, "Neues Dokument")


class DashboardDocumentListTest(TestCase):
    """The Übersicht lists the user's own documents and links to their details."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner", password="test12345"
        )
        self.client.force_login(self.user)
        self.sender = SenderProfileFactory(user=self.user)

    def test_empty_state_when_no_documents(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Noch keine Dokumente")

    def test_lists_own_documents_with_type_date_and_recipient(self):
        document = DocumentFactory(
            user=self.user,
            sender=self.sender,
            number="2026-0007",
            recipient_name="Erika Empfänger",
            recipient_company="",
        )
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "2026-0007")
        self.assertContains(response, "Erika Empfänger")
        self.assertContains(response, "Rechnung")
        self.assertContains(
            response, reverse("documents:document_preview", args=[document.pk])
        )

    def test_does_not_list_other_users_documents(self):
        DocumentFactory(number="9999-FREMD", recipient_name="Fremd")
        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, "9999-FREMD")
