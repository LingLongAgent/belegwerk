# Belegwerk

Web-App zum einfachen Erstellen offizieller **PDF-Dokumente nach DIN 5008 A**:
Rechnung, Angebot, Vertrag, Zahlungserinnerung. Formular ausfüllen → fertiges PDF.

PDF-Engine ist das Package **py_doc** (DIN 5008 A & B). Belegwerk rendert immer Form A.

## Entwicklung
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e /home/julius/py-doc   # PDF-Engine
pip install Django ruff factory_boy faker pypdf
python manage.py migrate && python manage.py runserver
```
Status: Gerüst steht — siehe `docs/PROJECT_PLAN.md`.
