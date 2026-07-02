# 0020 - EU-AI-Act-Recheck und AECT-Einordnung (Stand 2026-06-19)

Status: Accepted
Datum: 2026-06-19
Kontext: Phase D, Vorab-Check vor der Compliance-Wissensbasis
(session-protocol v3 SS4; aect-security-checklist v2.1 "Verifizierte Fakten").

## Kontext

Vor dem Schreiben der kuratierten Compliance-Wissensbasis (Markdown-KB fuer
RAG) verlangt das Protokoll einen Recheck des EU-AI-Act-Stands, weil die
Fakten in der Security-Checkliste zeitgestempelt sind (Stand Juni 2026, "vor
Phase D re-verifizieren"). Dieses ADR fixiert den am 2026-06-19 per Websuche
verifizierten Stand als zitierfaehigen Anker, damit die KB-Files nicht auf
Newsletter-Niveau, sondern auf belegten Fristen aufsetzen.

## Verifizierter Stand (2026-06-19)

1. Digital Omnibus on AI: noch NICHT im Amtsblatt veroeffentlicht.
   Trilog-Einigung 2026-05-07; vereinbarter Kompromisstext = Ratsdokument
   9247/26 vom 2026-05-13. Formelle Annahme + Veroeffentlichung erwartet
   Juni/Juli 2026. Konfidenz: hoch (mehrere unabhaengige Kanzlei-/
   Institutionsquellen, keine meldet Veroeffentlichung).

2. Bis zur Veroeffentlichung gilt rechtlich der urspruengliche Zeitplan:
   Annex-III-Hochrisiko-Pflichten ab 2026-08-02. Die Verschiebung ist
   politisch beschlossen, aber nicht in Kraft. Inkrafttreten der Aenderungen:
   3. Tag nach Amtsblatt-Veroeffentlichung.

3. Verschobene Fristen NACH Inkrafttreten (zweistufig):
   - Annex III (standalone, nutzungsbasiert): 2026-08-02 -> 2027-12-02.
   - Annex I (produktreguliert, eingebettet): 2027-08-02 -> 2028-08-02.

4. Art. 50 Transparenzpflicht: NICHT verschoben, gilt ab 2026-08-02.
   Einzige Ausnahme: maschinenlesbare Wasserzeichen nach Art. 50(2) - fuer
   Systeme, die vor 2026-08-02 bereits am Markt sind, Schonfrist bis
   2026-12-02. Bestandssystem-Regel, keine pauschale Verschiebung.

5. NEU ggue. Tag-45-Stand: Registrierungspflicht fuer als "exempt"
   eingestufte Systeme wieder eingesetzt. Die urspruenglich vorgeschlagene
   Streichung der DB-Registrierung fuer Art.-6(3)-exempte Annex-III-Systeme
   wurde im Trilog zurueckgedreht. Folge: Wer ein System in eine Annex-III-
   Kategorie einordnet und sich auf eine Ausnahme beruft, muss es weiterhin
   in der EU-Datenbank registrieren - mit begruendeter Ausnahme.

6. Der Omnibus aendert die Gesamtstruktur und den risikobasierten Ansatz des
   AI Act NICHT. Er verschiebt Fristen, vereinfacht (SME/SMC-Erleichterungen,
   Sektor-Ueberlappungen), fasst aber die Klassifizierungslogik nicht neu.

## Entscheidung (AECT-Einordnung, hergeleitet)

AECT bleibt Limited Risk. Herleitung, nicht Behauptung:

- AECT bewertet Use-Cases/Projekte (Einreichungen in einem AI-Intake), nicht
  Personen. Es trifft keine Entscheidung ueber eine natuerliche Person -
  keine Einstellung, Bewertung, Zugangs-, Kredit-, Bildungs- oder
  Strafverfolgungsentscheidung. Damit ist kein Annex-III-Tatbestand
  (Art. 6(2)) erfuellt.
- Weil AECT gar nicht in eine Annex-III-Kategorie faellt, greift die unter
  Punkt 5 reaktivierte Registrierungspflicht fuer "exempt"-Systeme nicht:
  Diese setzt voraus, dass ein System in eine Hochrisiko-Kategorie faellt und
  sich erst dann auf eine Ausnahme nach Art. 6(3) beruft. AECTs Position ist
  eine Stufe davor (Negativabgrenzung, nicht Ausnahme). Diese Unterscheidung
  wird in der Portfolio-Doku aktiv gefuehrt, nicht implizit angenommen.
- Art. 50 ist der einzige fuer AECT potenziell einschlaegige Punkt: falls ein
  Frontend KI-Ausgaben anzeigt, gehoert ein Transparenzhinweis "Diese Analyse
  nutzt ein KI-System" ins UI (Phase F). Die Wasserzeichen-Pflicht nach
  Art. 50(2) ist nicht einschlaegig (AECT publiziert keine KI-generierten
  Medieninhalte an die Oeffentlichkeit).

## Konsequenzen

- Die Compliance-KB (Folge-Tag) darf gebaut werden. Sie zitiert konservativ
  gegen 2026-08-02 und benennt die verschobenen Fristen als "politisch
  beschlossen, Inkrafttreten mit Amtsblatt-Veroeffentlichung offen".
- KB-Eintraege zu DSGVO/AI-Act tragen Quelle + Datum + "zu pruefen"-Markierung
  (Projekt-Prinzip: Hinweis mit Quelle, kein Urteil). Kein dpia_required-Boolean.
- Re-Check-Pflicht bleibt: Vor jedem oeffentlichen Compliance-Statement
  (Phase F, LinkedIn) den Amtsblatt-Status erneut pruefen - dieser Stand ist
  zeitgestempelt und veraltet mit der Veroeffentlichung.

## Bewusst nicht jetzt

- Keine KB-Markdown-Files heute (eigener Scope, Folge-Tag).
- Keine Aenderung an der Security-Checkliste v2.1: Deren Fakten bleiben als
  Stand korrekt; dieses ADR praezisiert nur (Art. 50(2)-Schonfrist,
  Registrierungs-Reinstatement) und datiert den Recheck.
- Kein Art.-50-UI-Hinweis: gehoert in Phase F (Frontend), nicht hierher.
