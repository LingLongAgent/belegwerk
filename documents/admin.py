"""Admin registration for stored documents — a thin read/inspect surface."""

from __future__ import annotations

from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("number", "doc_type", "recipient_name", "date", "user")
    list_filter = ("doc_type", "date")
    search_fields = ("number", "subject", "recipient_name", "recipient_company")
    date_hierarchy = "date"
