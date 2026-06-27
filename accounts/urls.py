from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path(
        "anmelden/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("abmelden/", auth_views.LogoutView.as_view(), name="logout"),
    path("registrieren/", views.register, name="register"),
    path("absender/", views.profile_list, name="profile_list"),
    path("absender/neu/", views.profile_create, name="profile_create"),
    path("absender/<int:pk>/", views.profile_edit, name="profile_edit"),
    path("absender/<int:pk>/loeschen/", views.profile_delete, name="profile_delete"),
]
