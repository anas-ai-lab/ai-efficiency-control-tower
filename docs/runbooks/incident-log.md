# Incident Log -- AECT

> Chronologisches Protokoll sicherheitsrelevanter Vorfaelle. Pro Eintrag:
> Datum, was passiert ist, was getan wurde. Befuellt aus Phase 5 der Runbooks
> (`secret-compromise.md`, `incident-response.md`). Neueste Eintraege oben.

---

## 2026-06 -- G-045: GitHub PAT in .git/config

- **Was:** GitHub PAT lag im Klartext in `.git/config` als Teil der Remote-URL
  (lokal, kein Push in ein oeffentliches Artefakt).
- **Wie entdeckt:** Phase-G-Audit, manuelle Pruefung der Git-Konfiguration.
- **Massnahmen:** PAT revoked + neu erzeugt; Remote-URL auf token-freie HTTPS-
  Form (`git remote set-url`); macOS-Keychain neu befuellt. Ablauf nach
  `secret-compromise.md` (Phasen 2-3).
- **Audit-Ergebnis:** "Last used" geprueft -- kein Fremdzugriff, keine
  Kostenwirkung. Motivierte die Erweiterung von `secret-compromise.md` auf die
  volle 5-Phasen-Form (AUDIT-015).
