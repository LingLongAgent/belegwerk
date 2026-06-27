# Belegwerk — Projektplan (App)

**Produkt:** Web-App zum einfachen Erstellen offizieller PDF-Dokumente
(Rechnung, Angebot, Vertrag, Zahlungserinnerung) — **alle nach DIN 5008 A**.
Engine: das `py_doc`-Package (DIN 5008 A/B, PDF). Die App immer **Form A**.
Repo: `LingLongAgent/belegwerk`. Stack: Django + Design-System (`static/css/design.css`).

## Grundregeln (pro Aufgabe)
- EINEN offenen `[ ]`-Punkt solide umsetzen. KISS, typannotiert.
- **Jede Funktion getestet** (Django-TestCase, factory_boy/Faker). PDF-Erzeugung
  mit echtem py_doc + Textprüfung (pypdf).
- Gate vor Commit: `ruff check .` sauber UND `python manage.py test` grün. Nie rot.
- Commit referenziert den Punkt, **push**, Issue schließen. Haken hier + PROGRESS.md.
- **PDF immer DIN 5008 A** (Form.A). py_doc nicht neu bauen — als Engine nutzen.


## Leitprinzip — INTUITIVE EINGABEMASKEN (MVP-Ziel)
Die Formulare müssen sich mühelos bedienen lassen, auch ohne DIN-Wissen:
- klare Abschnitte (Absender · Empfänger · Positionen · Texte), gute Defaults, Platzhalter & Hilfetexte;
- Positionen/Klauseln per **„+ Zeile hinzufügen"/Entfernen** (Inline-Formset), Beträge in € mit **Live-Summe**;
- sinnvolle Vorbelegung (Datum heute, fortlaufende Nummer, gespeichertes Absender-Profil);
- sofortige, freundliche Validierung; ein klarer Primär-Button **„PDF erstellen"** mit direkter Vorschau.
Nicht der Funktionsumfang entscheidet den MVP, sondern dass das Ausfüllen **schnell und selbsterklärend** ist.

## Aufgaben
- [x] M0 · Scaffold — Design, Auth, Übersicht + Typ-Auswahl, py_doc-Engine eingebunden. (Tests grün)
- [x] M1 (#1) · Absender-Profil — Modell + Formular (Firma, Anschrift, Bank/IBAN/BIC, Steuer), pro Nutzer, wiederverwendet. Tests.
- [x] M2 (#2) · Dokument-Datenmodell — gespeichertes Document (Typ, Empfänger, Metadaten, Nutzer, erstellt); Abbildung auf py_doc-Eingaben. Tests.
- [x] M3 (#3) · Empfänger/Kunden — wiederverwendbare Empfänger (Adressbuch) oder inline je Dokument. Tests.
- [x] M4 (#4) · Rechnung-Formular + Positionen — Positions-Formset → py_doc Invoice → Form-A-PDF. Tests.
- [x] M5 (#5) · Angebot-Formular — Positionen + Gültigkeit → py_doc Offer. Tests.
- [x] M6 (#6) · Vertrag-Formular + Klauseln — Parteien + §-Klauseln-Formset → py_doc Contract. Tests.
- [x] M7 (#7) · Zahlungserinnerung-Formular — Rechnungsbezug + Stufe + Gebühr + Frist → py_doc PaymentReminder. Tests.
- [ ] M8 (#8) · PDF-Erzeugung + Vorschau/Download — View rendert gespeichertes Dokument via py_doc (Form A) → PDF-Stream + Inline-Vorschau. Tests (PDF-Bytes + Inhalt).
- [ ] M9 (#9) · Dokumentenliste + Detail — Übersicht listet Dokumente (Typ/Datum/Empfänger); Detail mit erneutem Download/Bearbeiten. Tests.
- [ ] M10 (#10) · Registrierung + Onboarding — Nutzer + erstes Absender-Profil geführt anlegen. Tests.
- [ ] M11 (#11) · Politur & Produktionsreife — Validierung, Empty States, responsive, seed_demo, README. Finaler Durchgang.

## Done-Log
Siehe `docs/PROGRESS.md`.
