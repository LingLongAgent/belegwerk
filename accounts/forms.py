"""Form for creating and editing a sender profile (Absender).

The widgets carry German placeholders and section-friendly defaults so the mask
is self-explaining even without DIN knowledge — the MVP's guiding principle.
"""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import SenderProfile


class RegistrationForm(UserCreationForm):
    """Sign-up form for a new account — username plus a confirmed password.

    Kept deliberately minimal: the very next onboarding step is the sender
    profile, which carries the real contact details, so registration only asks
    for the credentials needed to log in.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Benutzername"}),
        }


class SenderProfileForm(forms.ModelForm):
    """Edit all of a :class:`SenderProfile`'s fields with helpful placeholders."""

    class Meta:
        model = SenderProfile
        fields = [
            "label",
            "name",
            "company",
            "street",
            "postal_code",
            "city",
            "country",
            "contact",
            "email",
            "phone",
            "bank_name",
            "iban",
            "bic",
            "tax_number",
            "vat_id",
            "register_court",
            "register_number",
            "is_default",
        ]
        widgets = {
            "label": forms.TextInput(attrs={"placeholder": "Meine Firma"}),
            "name": forms.TextInput(attrs={"placeholder": "Max Mustermann"}),
            "company": forms.TextInput(attrs={"placeholder": "Mustermann GmbH"}),
            "street": forms.TextInput(attrs={"placeholder": "Musterstraße 1"}),
            "postal_code": forms.TextInput(attrs={"placeholder": "10115"}),
            "city": forms.TextInput(attrs={"placeholder": "Berlin"}),
            "country": forms.TextInput(attrs={"placeholder": "Deutschland"}),
            "contact": forms.TextInput(attrs={"placeholder": "Ansprechpartner/in"}),
            "email": forms.EmailInput(attrs={"placeholder": "kontakt@firma.de"}),
            "phone": forms.TextInput(attrs={"placeholder": "+49 30 1234567"}),
            "bank_name": forms.TextInput(attrs={"placeholder": "Musterbank"}),
            "iban": forms.TextInput(attrs={"placeholder": "DE89 3704 0044 0532 0130 00"}),
            "bic": forms.TextInput(attrs={"placeholder": "COBADEFFXXX"}),
            "tax_number": forms.TextInput(attrs={"placeholder": "12/345/67890"}),
            "vat_id": forms.TextInput(attrs={"placeholder": "DE123456789"}),
            "register_court": forms.TextInput(attrs={"placeholder": "Amtsgericht Berlin"}),
            "register_number": forms.TextInput(attrs={"placeholder": "HRB 12345"}),
        }
