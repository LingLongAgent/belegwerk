from django.contrib import admin

from .models import SenderProfile


@admin.register(SenderProfile)
class SenderProfileAdmin(admin.ModelAdmin):
    list_display = ("label", "user", "company", "city", "is_default", "created_at")
    list_filter = ("is_default",)
    search_fields = ("label", "name", "company", "city")
