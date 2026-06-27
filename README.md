# Belegwerk

Web-App zum einfachen Erstellen offizieller **PDF-Dokumente nach DIN 5008 A**:
**Rechnung, Angebot, Vertrag, Zahlungserinnerung**. Formular ausfüllen → fertiges
PDF mit Vorschau und Download.

## Funktionen

- **Vier Dokumenttypen** mit eigenen, selbsterklärenden Eingabemasken (Abschnitte
  Absender · Empfänger · Positionen/Klauseln · Texte).
- **Absender-Profile** (Firma, Anschrift, Bank/IBAN/BIC, Steuer) — einmal anlegen,
  überall wiederverwenden; ein Standardprofil ist vorausgewählt.
- **Adressbuch** für wiederverwendbare Empfänger.
- **Positionen & Klauseln** per Inline-Formset („+ Zeile/Klausel hinzufügen"),
  Beträge in € mit Live-Summe; intern in Cent gespeichert.
- **PDF-Erzeugung** über die Engine **py_doc** — immer DIN 5008 **Form A** — mit
  Inline-Vorschau und Download.
- **Dokumentenübersicht** (Typ/Nummer/Datum/Empfänger) mit Bearbeiten & Löschen.
- **Registrierung + Onboarding**: Konto anlegen → direkt zum ersten Absender-Profil.

## Abhängigkeit: py_doc

Die PDF-Engine ist das separate Package **`py_doc`** (DIN 5008 A & B). Belegwerk
baut sie *nicht* nach, sondern nutzt sie und rendert ausschließlich **Form A**.
`py_doc` muss installiert sein (hier editable aus dem Nachbarverzeichnis).

## Schnellstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e /home/julius/py-doc          # PDF-Engine py_doc
pip install Django ruff factory_boy faker pypdf
python manage.py migrate
python manage.py seed_demo                   # Beispiel-Daten + Demo-Login
python manage.py runserver
```

Dann <http://127.0.0.1:8000/> öffnen.

### Login

`seed_demo` legt einen fertigen Demo-Account mit Absender-Profil, Adressbuch und je
einem Beispiel-Dokument pro Typ an:

- **Benutzername:** `demo`
- **Passwort:** `belegwerk-demo`

Alternativ über „Registrieren" ein eigenes Konto anlegen — das Onboarding führt
direkt zum ersten Absender-Profil.

## Entwicklung

```bash
ruff check .            # Linter
python manage.py test   # Test-Suite
```

Gate vor jedem Commit: `ruff` sauber **und** `python manage.py test` komplett grün.

Projektplan & Fortschritt: `docs/PROJECT_PLAN.md`, `docs/PROGRESS.md`.
