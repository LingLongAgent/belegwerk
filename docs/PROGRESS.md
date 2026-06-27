# Belegwerk — Progress

Neueste oben.

## Done

- **M3 · Empfänger/Kunden (Adressbuch)** — `Recipient`-Modell (gleiche Adressfelder wie `Document.recipient_*`, pro Nutzer), `to_recipient()` → py_doc `Party` (Blanks→None), `as_document_initial()` liefert `recipient_*`-Initialwerte für die späteren Dokument-Formulare (M4+). Formular mit Platzhaltern, List/Create/Edit/Delete (ownership-scoped), Sidebar-Link „Empfänger", Admin. 12 neue Tests (Mapping, Initial-Keys, str-Regel, View-Scoping/CRUD). Gesamt 33 grün, ruff sauber.
- **M2 · Dokument-Datenmodell** — `Document`-Modell (Typ-Choices Rechnung/Angebot/Vertrag/Zahlungserinnerung, Inline-Empfänger, Nummer/Datum/Betreff, Absender-FK mit PROTECT, pro Nutzer). `to_recipient()` → py_doc `Party`, `to_meta()` → `DocumentMeta` (deutsches Datum, typ-abhängiges Nummern-Label im Informationsblock). Admin-Registrierung. 7 Tests grün (Mapping, Blanks→None, Label-pro-Typ, PROTECT). Gesamt 21 grün.
- **M1 · Absender-Profil** — `SenderProfile`-Modell (Party+Sender-Felder, `to_sender()` → py_doc), pro Nutzer, Standardprofil-Regel; Formular mit Abschnitten/Platzhaltern, List/Create/Edit/Delete (ownership-scoped), Sidebar-Link, Admin. 14 Tests grün (Modell-Mapping, Default-Regel, View-Scoping).
- **M0 · Scaffold** — Django + Design + Auth + Typ-Auswahl + py_doc-Engine. Tests grün.
