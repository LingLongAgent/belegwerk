"""Forms for the address book and for creating documents.

German placeholders keep the masks self-explaining without DIN knowledge — the
MVP's guiding principle. Money is typed in euros (with a live sum in the
template) and converted to the cents the model stores; the VAT rate is picked
from the common German rates and stored as the fraction py_doc expects.
"""

from __future__ import annotations

from decimal import Decimal

from django import forms

from accounts.models import SenderProfile

from .models import Document, DocumentItem, Recipient


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


# The German VAT rates a small business needs, as (stored fraction, label) pairs.
VAT_CHOICES = [
    ("0.19", "19 %"),
    ("0.07", "7 %"),
    ("0.00", "0 %"),
]


# The recipient widgets every document form shares — same fields, same German
# placeholders — kept in one place so each form's Meta only adds its own bits.
RECIPIENT_WIDGETS = {
    "recipient_name": forms.TextInput(attrs={"placeholder": "Erika Beispiel"}),
    "recipient_company": forms.TextInput(attrs={"placeholder": "Beispiel AG"}),
    "recipient_street": forms.TextInput(attrs={"placeholder": "Beispielweg 7"}),
    "recipient_postal_code": forms.TextInput(attrs={"placeholder": "20095"}),
    "recipient_city": forms.TextInput(attrs={"placeholder": "Hamburg"}),
    "recipient_country": forms.TextInput(attrs={"placeholder": "Deutschland"}),
    "recipient_contact": forms.TextInput(attrs={"placeholder": "Ansprechpartner/in"}),
    "recipient_email": forms.EmailInput(attrs={"placeholder": "kontakt@beispiel.de"}),
    "recipient_phone": forms.TextInput(attrs={"placeholder": "+49 40 1234567"}),
    "recipient_vat_id": forms.TextInput(attrs={"placeholder": "DE123456789"}),
}


class SenderScopedFormMixin:
    """Scopes the ``sender`` choice to the current user and pre-selects the default.

    Every document form offers only the logged-in user's sender profiles and, on a
    fresh form, starts on their standard profile — so the mask arrives filled where
    it sensibly can be. The view passes ``user=`` in; without it the field is left
    untouched (e.g. when rendering an unbound form in tests).
    """

    def __init__(self, *args: object, user: object | None = None, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        if user is not None:
            senders = SenderProfile.objects.filter(user=user)
            self.fields["sender"].queryset = senders
            # Pre-select the standard profile unless the form is already bound to one.
            if not self.initial.get("sender"):
                default = senders.filter(is_default=True).first()
                if default is not None:
                    self.initial["sender"] = default.pk


class InvoiceForm(SenderScopedFormMixin, forms.ModelForm):
    """The invoice's own fields: who sends it, the metadata, and the recipient.

    The sender list is scoped to the current user and defaults to their standard
    profile, so a fresh form is already filled where it sensibly can be. The
    positions live in a separate formset (:data:`InvoiceItemFormSet`).
    """

    class Meta:
        model = Document
        fields = [
            "sender",
            "number",
            "date",
            "subject",
            "payment_terms",
            "recipient_name",
            "recipient_company",
            "recipient_street",
            "recipient_postal_code",
            "recipient_city",
            "recipient_country",
            "recipient_contact",
            "recipient_email",
            "recipient_phone",
            "recipient_vat_id",
        ]
        widgets = {
            "number": forms.TextInput(attrs={"placeholder": "2026-0001"}),
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "subject": forms.TextInput(attrs={"placeholder": "Rechnung 2026-0001"}),
            "payment_terms": forms.TextInput(),
            **RECIPIENT_WIDGETS,
        }


class OfferForm(SenderScopedFormMixin, forms.ModelForm):
    """The offer's own fields: sender, metadata, recipient, and a validity date.

    Mirrors :class:`InvoiceForm` but carries ``valid_until`` (bis wann das Angebot
    gilt) in place of the invoice's payment terms; positions reuse the shared
    :class:`DocumentItemForm` via :data:`OfferItemFormSet`.
    """

    class Meta:
        model = Document
        fields = [
            "sender",
            "number",
            "date",
            "subject",
            "valid_until",
            "recipient_name",
            "recipient_company",
            "recipient_street",
            "recipient_postal_code",
            "recipient_city",
            "recipient_country",
            "recipient_contact",
            "recipient_email",
            "recipient_phone",
            "recipient_vat_id",
        ]
        widgets = {
            "number": forms.TextInput(attrs={"placeholder": "2026-0001"}),
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "subject": forms.TextInput(attrs={"placeholder": "Angebot 2026-0001"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            **RECIPIENT_WIDGETS,
        }


class DocumentItemForm(forms.ModelForm):
    """One position row: euros in, cents stored; VAT picked from the usual rates.

    ``unit_price_euro`` and ``vat_rate`` replace the raw model fields so the user
    types familiar values; :meth:`save` writes them back as the cents and fraction
    :class:`~documents.models.DocumentItem` keeps.
    """

    unit_price_euro = forms.DecimalField(
        label="Einzelpreis (€)",
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "input num", "step": "0.01", "placeholder": "0,00"}
        ),
    )
    vat_rate = forms.TypedChoiceField(
        label="USt",
        choices=VAT_CHOICES,
        coerce=Decimal,
        widget=forms.Select(attrs={"class": "input"}),
    )

    class Meta:
        model = DocumentItem
        fields = ["description", "quantity", "unit", "vat_rate"]
        widgets = {
            "description": forms.TextInput(
                attrs={"class": "input", "placeholder": "Beratungsleistung"}
            ),
            "quantity": forms.NumberInput(attrs={"class": "input num", "step": "0.01"}),
            "unit": forms.TextInput(attrs={"class": "input", "placeholder": "Stk"}),
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        # Show the stored cents as euros when editing an existing position.
        if self.instance and self.instance.pk:
            self.fields["unit_price_euro"].initial = (
                Decimal(self.instance.unit_price_cents) / 100
            )

    def save(self, commit: bool = True) -> DocumentItem:
        item = super().save(commit=False)
        euro = self.cleaned_data["unit_price_euro"]
        item.unit_price_cents = int((euro * 100).to_integral_value())
        if commit:
            item.save()
        return item


# Inline positions for an invoice: at least one empty row, rows removable.
InvoiceItemFormSet = forms.inlineformset_factory(
    Document,
    DocumentItem,
    form=DocumentItemForm,
    extra=1,
    can_delete=True,
)

# An offer's positions are the same rows as an invoice's, so it reuses the same
# inline formset — one definition, both document types.
OfferItemFormSet = InvoiceItemFormSet
