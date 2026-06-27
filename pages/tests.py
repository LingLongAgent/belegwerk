from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
