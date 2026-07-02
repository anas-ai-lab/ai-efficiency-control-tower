# ADR-0039: L-3 Dedup -- Embedding-Similarity bei Intake

**Status:** Accepted
**Datum:** 2026-06-28
**Autor:** Anas

## Kontext

Mehrere Einreicher koennen denselben oder einen sehr aehnlichen Use Case
unabhaengig voneinander einreichen (Limitation L-3). Bisher erkennt AECT das
nicht -- Duplikate landen unbemerkt als getrennte Cases. Gesucht war ein
Hinweis bei Intake (POST /triage), der Aehnlichkeit sichtbar macht, ohne die
deterministische Triage-Entscheidung zu veraendern.

## Entscheidung

Wir berechnen bei Intake ein Embedding des neuen Cases (Titel + Ist-Zustand),
speichern es in einer neuen SQLite-Spalte `embedding` (nullable, JSON-Float-
Liste) und vergleichen es per Cosinus-Aehnlichkeit gegen die Embeddings
bestehender Cases. Der hoechste Treffer erzeugt -- oberhalb einer Schwelle --
eine additive `SimilarityWarning` in der `TriageResponse`:

- `< 0.75`: kein Hinweis.
- `[0.75, 0.90)`: Hinweis, `suggest_combine=False` ("Aehnliches existiert").
- `>= 0.90`: Hinweis, `suggest_combine=True` ("wahrscheinlich Duplikat").

Die Pruefung ist eine eigene async-Methode `check_similarity()`, die nach
`submit_use_case()` laeuft -- der Case ist dann bereits persistiert, das
Embedding wird nachgetragen. Sie scheitert nie hart (siehe Konsequenzen).

## Begruendung

**Schwellenwahl 0.75 / 0.90:** Zwei Stufen trennen *menschliche Aufmerksamkeit*
von *maschinellem Vorschlag*. 0.75 ist niedrig genug, damit ein Mensch
thematisch Verwandtes prueft (false positives sind hier billig -- nur ein
Hinweis). 0.90 ist hoch genug, dass ein konkreter "zusammenlegen?"-Vorschlag
selten daneben liegt (false positives waeren hier teurer -- sie suggerieren
eine Aktion).

| Frage | Alternative | Entscheidung |
|---|---|---|
| Speicher | Separater Vektor-Store (ChromaDB) | **SQLite-JSON-Spalte** -- keine neue Infra-Abhaengigkeit fuer den Intake-Pfad; bei erwarteten Fallzahlen (< 10k) ist ein linearer Scan ueber gespeicherte Embeddings ausreichend schnell. ChromaDB bliebe der Wissensbasis vorbehalten. |
| Metrik | Skalarprodukt (dot) | **Cosinus** -- skaleninvariant, robust gegen unterschiedliche Vektorlaengen/Magnituden. |
| Integration | `submit_use_case` async machen | **Separate `check_similarity()`** -- haelt den synchronen `submit_use_case`-Vertrag (und ~30 bestehende Tests) unveraendert; Embedding-I/O ist async gekapselt. |

Die Schwellen 0.75/0.90 sind **generische Cosinus-Werte** (Standard-Methodik),
keine firmenspezifischen Werte wie ROI-/Zonen-Schwellen -- daher als
Code-Konstanten gefuehrt, nicht in `config/` (vgl. vertraglich bedingte IP-Trennung).

## Konsequenzen

**Positiv:**
- Duplikat-Bewusstsein bei Intake, ohne die Triage-Entscheidung zu beeinflussen.
- Keine neue Laufzeit-Infrastruktur; abwaertskompatible DB-Migration.

**Negativ / Trade-offs:**
- Linearer Scan ueber alle Embeddings pro Intake -- O(n) je Einreichung. Bei
  < 10k Cases unkritisch; bei deutlich mehr waere ein echter Vektor-Index noetig
  (dokumentierter Folgepunkt).
- Der Dedup-Embedder ist an den echten ML-Pfad gekoppelt (`AECT_CHROMA_HOST`
  gesetzt -> lokales Modell geladen). Im Mock-/Testbetrieb ist kein Embedder
  injiziert -> die Pruefung wird uebersprungen (still, einmal geloggt).
- Der **erste** Case bekommt kein Embedding (keine Vergleichsbasis -> bewusst
  keine Berechnung) und kann daher nie als Duplikat erkannt werden. Akzeptierte
  Effizienz-/Einfachheits-Grenze.

**Robustheit (scheitert nie hart):**
- Kein Embedder -> ueberspringen + Warn-Log.
- Keine anderen Cases -> ueberspringen, kein Embedding.
- Embedding-Fehler -> Error-Log, ohne Hinweis fortfahren. Die Triage selbst
  ist zu diesem Zeitpunkt bereits abgeschlossen und persistiert.
