"""Form for the recipient address book (Empfänger/Kunden).

German placeholders keep the mask self-explaining without DIN knowledge — the
MVP's guiding principle. Only the name is required; everything else is optional
so a quick "name + city" entry is enough to start with.
"""

from __future__ import annotations

from django import forms

from .models import Recipient


class RecipientForm(forms.ModelForm):
    """Edit all of a :class:`Recipient`'s address fields with helpful placeholders."""

    class Meta:
        model = Recipient
        fields = [
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
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Erika Beispiel"}),
            "company": forms.TextInput(attrs={"placeholder": "Beispiel AG"}),
            "street": forms.TextInput(attrs={"placeholder": "Beispielweg 7"}),
            "postal_code": forms.TextInput(attrs={"placeholder": "20095"}),
            "city": forms.TextInput(attrs={"placeholder": "Hamburg"}),
            "country": forms.TextInput(attrs={"placeholder": "Deutschland"}),
            "contact": forms.TextInput(attrs={"placeholder": "Ansprechpartner/in"}),
            "email": forms.EmailInput(attrs={"placeholder": "kontakt@beispiel.de"}),
            "phone": forms.TextInput(attrs={"placeholder": "+49 40 1234567"}),
            "vat_id": forms.TextInput(attrs={"placeholder": "DE123456789"}),
        }
