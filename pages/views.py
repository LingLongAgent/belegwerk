from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    """Übersicht der erstellten Dokumente (Build-Loop füllt es aus)."""
    return render(request, "pages/dashboard.html", {"documents": []})
