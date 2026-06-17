# Wissensbasis (knowledge_base/)

Kuratierte Quellen fuer die belegten Compliance- und Stack-Hinweise (Phase D,
Master-Plan v3.1). Hier liegen die Markdown-Dateien, aus denen das Retrieval
Belege zieht -- jeder Hinweis im Output wird mit Quelle zitiert, nicht aus
Modellwissen erzeugt (interne Referenz (entfernt) SS3.2).

**Stand:** Struktur + Policy. Die eigentlichen kuratierten Inhalte
(DSGVO-/EU-AI-Act-Auszuege, Security-Massnahmen, Stack-Doku) folgen als
einzelne Markdown-Dateien an Folge-Tagen. Das aktuelle Retrieval laeuft gegen
eine synthetische Platzhalter-Wissensbasis im MockRetriever
(adapters/in_memory/retriever.py).

## Policy

- **Nur kuratierte, vertrauenswuerdige Quellen.** Keine ungeprueften oder
  beliebigen Web-Inhalte (aect-security-checklist v2.1, Phase D).
- **Retrieved-Content ist Daten, nie Instruktion.** Beim Prompt-Aufbau werden
  Treffer in einem abgegrenzten Block (Delimiter, analog
  application/sanitization.py) als Daten markiert -- ein Textausschnitt darf
  das Modell nicht steuern (OWASP LLM01).
- **Provenienz pro Eintrag.** Jeder Chunk traegt einen stabilen source_id
  (RetrievedChunk, application/ports/retriever.py). Doppelzweck: Citation-Anker
  im Output und Loesch-Tag fuer gezielte Quellen-Entfernung.
- **PII-Redaction vor dem Embedding.** Sobald Embeddings erzeugt werden, laeuft
  PII-Redaction davor (LLM08; Embeddings gelten als personenbezogen). Heute
  nicht aktiv -- kein Embedding.
- **IP-Trennung (interne Referenz (entfernt) SS5).** Firmenspezifische Werte (echte Stundensaetze,
  Laenderlisten, interne Plattform-Namen) gehoeren nicht hierher, sondern in
  config/. Kuratierte Doku zu oeffentlichen Standards/Tools ist davon nicht
  betroffen.
