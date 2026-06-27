from django.urls import path

from . import views

app_name = "documents"
urlpatterns = [
    path("neu/", views.choose_type, name="choose_type"),
    path("neu/rechnung/", views.invoice_create, name="invoice_create"),
    path("neu/angebot/", views.offer_create, name="offer_create"),
    path("neu/vertrag/", views.contract_create, name="contract_create"),
    path("empfaenger/", views.recipient_list, name="recipient_list"),
    path("empfaenger/neu/", views.recipient_create, name="recipient_create"),
    path("empfaenger/<int:pk>/", views.recipient_edit, name="recipient_edit"),
    path(
        "empfaenger/<int:pk>/loeschen/",
        views.recipient_delete,
        name="recipient_delete",
    ),
]
