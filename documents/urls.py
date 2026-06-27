from django.urls import path

from . import views

app_name = "documents"
urlpatterns = [
    path("neu/", views.choose_type, name="choose_type"),
    path("empfaenger/", views.recipient_list, name="recipient_list"),
    path("empfaenger/neu/", views.recipient_create, name="recipient_create"),
    path("empfaenger/<int:pk>/", views.recipient_edit, name="recipient_edit"),
    path(
        "empfaenger/<int:pk>/loeschen/",
        views.recipient_delete,
        name="recipient_delete",
    ),
]
