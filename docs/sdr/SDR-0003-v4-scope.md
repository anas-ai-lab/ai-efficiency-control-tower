# SDR-0003 -- V4-Scope (Demo-Build)

**Status:** Accepted
**Datum:** 2026-07-09
**Autor:** Anas
**Uebergeordnet:** SDR-0002 (v1.3). Diese SDR erweitert und schaerft dessen Scope fuer V4.

> Hinweis: SDR-0001/0002 sind bewusst nicht eingecheckt (IP-sensitiv). Diese SDR
> haelt nur generische Methodik und Engineering-Entscheidungen fest -- keine
> Stundensatz-Zahlen (das Repo ist oeffentlich, siehe Entscheidung 1).

## Kontext

V1.0-V3.1 sind abgeschlossen (zuletzt v3.1.1, Phase G Post-v1-Audit). V4 ist ein
klar abgegrenzter Build mit einem konkreten Zweck: eine vorzeigbare Demo fuer
einen internen Vorgesetzten. Kein Produktivbetrieb, kein Multi-User-Rollout, kein
Verkauf. Dieser Rahmen praegt jede folgende Entscheidung -- vor allem die
Nutzenformel, das Rollenmodell und die Freiheit, die Demo-Datenbank zuruecksetzen
zu duerfen.

## Entscheidungen

1. **V4-Charakter.** V4 ist ein Demo-Build fuer einen internen Vorgesetzten; kein
   produktiver Einsatz. Das Repo bleibt oeffentlich. Die IP-Schichttrennung
   (generischer Code + getrackte `config/*.toml` vs. echte Werte in
   `config/*.local.toml`, gitignored) bleibt unveraendert und wird eher
   verschaerft: keine echten Stundensaetze, realen Cases oder internen Begriffe
   in getrackten Artefakten.

2. **Nutzenformel (personen-basiert, fixierte Semantik).**
   - Zeitersparnis pro Vorgang = `t_ist - t_ai` (darf <= 0 sein -- eine Idee darf
     auch Zeit kosten; das Modell verschweigt das nicht).
   - Roh-Nutzen/Jahr = Zeitersparnis pro Vorgang x Vorgaenge pro Mitarbeiter und
     Jahr x Anzahl Mitarbeiter x Stundensatz(Land, Level).
   - Erwarteter Nutzen = Roh-Nutzen x Verbindlichkeitsfaktor x Evidenzfaktor.
   - Netto-Nutzen = Erwarteter Nutzen - jaehrliche Lizenzkosten.

   Die Semantik ist fixiert -- keine spaetere stille Umdeutung der Faktoren-Kette.

3. **Faktoren (multiplikativ, bewusst streng).**
   - Verbindlichkeit: 0.50 freiwillig / 0.70 empfohlener Teamstandard / 0.90
     fester Prozessschritt.
   - Evidenz: 0.40 reine Einschaetzung / 0.55 eigene Erfahrung bzw.
     Analogieprojekt / 0.90 mit realen Beispielen getestet.

   Multiplikativ verknuepft, Worst Case 0.50 x 0.40 = 0.20. Eine ungepruefte
   freiwillige Idee ist damit fast nichts wert -- das ist Absicht.

4. **Composite-Aufwandscore neu (Range 1-9).**
   - Komplexitaet 1-5 aus dem Implementierungsansatz: einfache Integration (1) ->
     Entwicklung auf Bestehendem (2) -> API-Anbindung (3) -> Eigenentwicklung (4)
     -> neues Tool (5).
   - Kostenpunkte 0-2: +1 wenn Impl.-Kosten >= 10 000 EUR, +1 wenn Lizenz >=
     10 000 EUR/Jahr.
   - Datenschutz 0-2: 0/1/1/2 fuer keine / pseudonym / personenbezogen /
     besondere Kategorie.

   Summe 1-9. Das separate Komplexitaets-Eingabefeld und die fruehere
   Lizenz-Tier-Logik entfallen -- der Implementierungsansatz und die zwei
   Kostenschwellen ersetzen sie.

5. **Zonen-Schwellen unveraendert.** Die Triage-Zonenlogik und ihre Schwellen
   bleiben wie in v1-v3. Das Golden-Case-Agreement wird gegen das neue Nutzen-/
   Aufwand-Modell neu gemessen; die Experten-Labels selbst bleiben unangetastet
   (kein nachtraegliches Anpassen der Ground Truth an das Modell).

6. **Schaerfung gegen halluzinierte Zahlen.** Ein deterministischer
   Zahlen-Validator (Regel vor LLM) plus ein Draft/Diff/Accept-Reject-Flow.
   Halluzinierte Zahlen werden nie gespeichert oder angezeigt -- ein LLM-Draft
   wird erst nach explizitem Accept persistiert.

7. **Rollenmodell (anonym vs. Admin).** Anonym: Einreichen, Ideation,
   Listen-/Detail-Ansicht (read-only). Admin: alle Aktionen. Umsetzung ueber
   Session-Cookie + scrypt-Passwort-Hash; der API-Key bleibt fuer Skripte
   bestehen. Das hebt die "API-Key only"-Grenze aus SDR-0002 Paragraph 12a
   kontrolliert auf -- weiterhin kein Multi-User, kein JWT/OAuth.

8. **DB-Reset erlaubt.** Weil V4 ein Demo-Build ist, darf die Datenbank
   zurueckgesetzt werden. Ein Seed-Skript stellt reproduzierbare Demo-Daten her
   (generisch, keine realen Cases).

9. **Design-Neuausrichtung Frontend.** Als letzter Block: Struktur nach
   Mockup-Vorbild, professionelle Farbwelt. Reine Praesentationsschicht -- ohne
   Rueckwirkung auf Domain- oder Nutzenlogik.

## Konsequenzen

**Positiv:**
- Die Nutzenformel ist personen-basiert und ehrlich (Zeitersparnis darf negativ
  sein, strenge Faktoren-Kette) -- schwer schoenzurechnen.
- Ein Aufwandscore aus dem Implementierungsansatz statt aus einem frei
  eingegebenen Komplexitaetswert reduziert subjektive Eingaben.
- Anonym-vs-Admin macht die Demo ohne Login begehbar, ohne Schreibaktionen zu
  oeffnen.

**Trade-offs:**
- Neue Faktoren-Stufen (3 statt bisher 2 bei Verbindlichkeit; geaenderte
  Evidenz-Werte) und das neue Datenschutz-Mapping (personenbezogen jetzt 1 statt
  2) bedeuten eine Neukalibrierung -- Config-Keys und Golden-Case-Agreement
  muessen nachgezogen werden (Folge-Prompts, nicht diese SDR).
- Session-Auth mit scrypt fuehrt einen Passwort-/Cookie-Pfad ein, den es vorher
  nicht gab -- bewusst minimal gehalten (kein JWT/OAuth, kein Multi-User).

**Abgrenzung (nicht in dieser SDR):**
- Keine Stundensatz-Zahlen (oeffentliches Repo). Echte Raten liegen in
  `config/roi_config.local.toml` (gitignored).
- Kein Feature-Code. Diese SDR ist reine Scope-/Entscheidungsgrundlage; die
  Umsetzung erfolgt in nummerierten Folge-Prompts.
