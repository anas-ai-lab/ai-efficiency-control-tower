"""PresidioRedactor -- PIIRedactorPort-Adapter ueber Presidio + deutsches
spaCy-NER (Phase G Privacy-Haertung).

B1-Spike (dieselbe Session) hat Footprint (160 MB zusaetzlich zum
bestehenden ~1-GB-ML-Stack), Latenz (28 ms warm, ~0.4 s kalter erster Call)
und Genauigkeit (5/5 Ziel-Entitaeten auf handgeschriebenen deutschen
Testsaetzen) gemessen und "integrieren: ja" empfohlen.

Scope-Grenze (zentral, siehe Aufrufer application/service.py::
check_similarity()): redact() wird NUR auf den Text angewendet, der an den
Dedup-Embedder geht -- NICHT auf die gespeicherten title/current_state-
Felder selbst. Diese bleiben im Klartext, weil sie fuer Fallbearbeitung und
nachfolgende LLM-Calls (sharpen_case/propose_solution) unveraendert
gebraucht werden. Nur der potenziell invertierbare Vektor wird aus
redaktiertem Text gebaut. Dieser Adapter kennt diese Grenze nicht selbst --
sie ist eine Entscheidung des Aufrufers, nicht dieses Moduls.

Lazy-Loading: AnalyzerEngine/AnonymizerEngine werden erst beim ERSTEN
tatsaechlichen redact()-Aufruf instanziiert (functools.cached_property),
nicht im Konstruktor -- die B1-gemessenen ~0.4s Modell-Ladezeit werden nur
bezahlt, wenn tatsaechlich ein Case mit Dedup-Check reinkommt (Mock-/
Testbetrieb ruft redact() nie auf). Die presidio_analyzer/presidio_anonymizer-
IMPORTS selbst stehen bewusst auf Modulebene (nicht lokal in der Property)
-- das Importieren der Klassen ist billig (~0.55s beim allerersten Import
im Prozess, B1-Messwert), teuer ist erst die Modell-INSTANZIIERUNG.

Score-Threshold (bewusst kein einzelner globaler Wert): B1 zeigt, dass ein
pauschaler score_threshold=0.5 den 0.4-PHONE_NUMBER-Fall verwerfen wuerde
(empirisch verifiziert) -- das widerspraeche dem Ziel, echte Telefonnummern
zuverlaessig zu maskieren. Die B1-False-Positives (satzinitiale
Grossschreibung, generische Substantive als LOCATION/ORGANIZATION) kommen
ausschliesslich aus den NER-basierten Recognizern (PERSON/LOCATION/
ORGANIZATION) -- das ist eine Grenze von de_core_news_sm, keine von
Presidio (siehe docs/owasp-llm-checklist.md LLM08). EMAIL_ADDRESS/IBAN_CODE
(Regex+Checksum, B1-Score 1.0) und PHONE_NUMBER (Regex-Pattern, B1-Score
0.4) sind strukturell erkannt: der Threshold gilt deshalb NUR fuer die drei
NER-Typen. Uebermaskierung eines faelschlich erkannten Strings ist billig;
eine tatsaechliche Telefonnummer/IBAN/E-Mail NICHT zu maskieren waere das
eigentliche Risiko -- deshalb bleiben diese drei Typen ungefiltert.
"""

from __future__ import annotations

from functools import cached_property

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

_NLP_CONFIG = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "de", "model_name": "de_core_news_sm"}],
}

# Platzhalter pro Entity-Typ -- generisch, kein Rueckschluss auf den
# tatsaechlichen Wert moeglich (z. B. kein "<PERSON:Anna Schmidt>").
_PLACEHOLDERS: dict[str, str] = {
    "PERSON": "<PERSON>",
    "EMAIL_ADDRESS": "<EMAIL>",
    "IBAN_CODE": "<IBAN>",
    "PHONE_NUMBER": "<PHONE>",
    "LOCATION": "<LOCATION>",
    "ORGANIZATION": "<ORGANIZATION>",
}

# Nur diese drei NER-basierten Typen sind die B1-False-Positive-Quelle --
# EMAIL_ADDRESS/IBAN_CODE/PHONE_NUMBER (strukturelle Recognizer) bleiben
# ungefiltert (siehe Modul-Docstring).
_SCORE_THRESHOLDED_ENTITIES = frozenset({"PERSON", "LOCATION", "ORGANIZATION"})
_SCORE_THRESHOLD = 0.5


def _passes_threshold(result: RecognizerResult) -> bool:
    if result.entity_type not in _SCORE_THRESHOLDED_ENTITIES:
        return True
    return result.score >= _SCORE_THRESHOLD


class PresidioRedactor:
    """PIIRedactorPort-Implementierung via Presidio AnalyzerEngine +
    AnonymizerEngine, deutsches NER (de_core_news_sm).

    Implementiert PIIRedactorPort via strukturellem Subtyping (kein Import
    von PIIRedactorPort noetig -- analog SentenceTransformerEmbedder).
    """

    @cached_property
    def _analyzer(self) -> AnalyzerEngine:
        provider = NlpEngineProvider(nlp_configuration=_NLP_CONFIG)
        return AnalyzerEngine(
            nlp_engine=provider.create_engine(), supported_languages=["de"]
        )

    @cached_property
    def _anonymizer(self) -> AnonymizerEngine:
        # presidio_anonymizer.AnonymizerEngine.__init__ ist intern nicht
        # vollstaendig typannotiert (trotz py.typed-Marker) -- kein Bug
        # unsererseits, siehe presidio-anonymizer==2.2.363.
        return AnonymizerEngine()  # type: ignore[no-untyped-call]

    def redact(self, text: str) -> str:
        if not text:
            return text

        results = self._analyzer.analyze(
            text=text, language="de", entities=list(_PLACEHOLDERS)
        )
        filtered = [r for r in results if _passes_threshold(r)]
        if not filtered:
            return text

        operators = {
            entity_type: OperatorConfig("replace", {"new_value": placeholder})
            for entity_type, placeholder in _PLACEHOLDERS.items()
        }
        # presidio_analyzer.RecognizerResult und presidio_anonymizer.entities.
        # engine.recognizer_result.RecognizerResult sind zwei nominell
        # verschiedene, strukturell identische Klassen (start/end/entity_type/
        # score) -- das ist der von Presidio selbst dokumentierte Uebergabeweg
        # von analyze() an anonymize(), mypy sieht nur die Nominal-Differenz.
        anonymized = self._anonymizer.anonymize(
            text=text,
            analyzer_results=filtered,  # type: ignore[arg-type]
            operators=operators,
        )
        return anonymized.text
