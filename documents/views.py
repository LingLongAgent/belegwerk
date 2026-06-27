from django.contrib.auth.decorators import login_required
from django.shortcuts import render

DOC_TYPES = [
    {"key": "rechnung", "name": "Rechnung", "desc": "Positionen, USt, Summen, Zahlungsziel."},
    {"key": "angebot", "name": "Angebot", "desc": "Positionen und Gültigkeit."},
    {"key": "vertrag", "name": "Vertrag", "desc": "Parteien, §-Klauseln, Unterschriften."},
    {"key": "zahlungserinnerung", "name": "Zahlungserinnerung", "desc": "Bezug auf Rechnung, Frist."},
]


@login_required
def choose_type(request):
    """Dokumenttyp wählen — Formulare folgen je Typ (Build-Loop)."""
    return render(request, "documents/choose_type.html", {"types": DOC_TYPES})
