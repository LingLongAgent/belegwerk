from django.urls import path

from . import views

app_name = "documents"
urlpatterns = [path("neu/", views.choose_type, name="choose_type")]
