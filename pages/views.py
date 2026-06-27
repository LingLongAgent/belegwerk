from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from documents.models import Document


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Übersicht: list the current user's documents, newest first.

    Each row shows the type, number, date and recipient and links to the detail
    page; an empty state nudges a first-time user to create their first document.
    The queryset is scoped to ``request.user`` so one user never sees another's.
    """
    documents = Document.objects.filter(user=request.user)
    return render(request, "pages/dashboard.html", {"documents": documents})
