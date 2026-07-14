"""Deterministic interpretation-hint inference for annotation outputs."""

from __future__ import annotations

from maana_ingest.annotation.models import AnnotationHit, CitationHit, MergedChapterAnnotation


def infer_interpretation_hints(*signals: str | None) -> list[str]:
    haystack = " ".join(value.strip().lower() for value in signals if value and value.strip())
    if not haystack:
        return []

    hint_keywords: list[tuple[str, tuple[str, ...]]] = [
        ("mystical", ("mystical", "mystic", "sufi", "divine", "spiritual", "gnostic")),
        ("philosophical", ("philosophical", "philosophy", "metaphysical", "metaphysics", "ontological", "ontology")),
        ("existential", ("existential", "existence", "being", "meaning of life", "death")),
        ("psychological", ("psychological", "psyche", "ego", "inner self", "anxiety", "desire", "fear")),
        ("emotional", ("emotional", "emotion", "longing", "grief", "joy", "sorrow", "love")),
        ("symbolic", ("symbolic", "symbol", "metaphorical", "metaphor", "allegorical", "allegory")),
        ("pedagogical", ("pedagogical", "pedagogy", "lesson", "teaches", "instructional")),
        ("synthetic", ("synthetic", "synthesis", "summary", "integrative")),
        ("paraphrastic", ("paraphrastic", "paraphrase", "restatement")),
        ("descriptive", ("descriptive", "description", "describes", "observational")),
        ("literal", ("literal", "textual", "verbatim")),
        ("comparative", ("comparative", "parallel", "echo", "analogue", "reference")),
    ]
    for hint, keywords in hint_keywords:
        if any(keyword in haystack for keyword in keywords):
            return [hint]
    return []


def enrich_merged_annotation(merged: MergedChapterAnnotation) -> MergedChapterAnnotation:
    enriched = merged.model_copy(deep=True)
    enriched.couplets = [_enrich_hit(item) for item in enriched.couplets]
    enriched.quran_references = [_enrich_hit(item) for item in enriched.quran_references]
    enriched.hadith_references = [_enrich_hit(item) for item in enriched.hadith_references]
    enriched.poets = [_enrich_hit(item) for item in enriched.poets]
    enriched.persian_passages = [_enrich_hit(item) for item in enriched.persian_passages]
    enriched.citations = [_enrich_citation(item) for item in enriched.citations]
    return enriched


def _enrich_hit(item: AnnotationHit) -> AnnotationHit:
    if item.interpretation_hints:
        return item
    item.interpretation_hints = infer_interpretation_hints(item.notes, item.label, item.text)
    return item


def _enrich_citation(item: CitationHit) -> CitationHit:
    if item.interpretation_hints:
        return item
    item.interpretation_hints = infer_interpretation_hints(item.notes, item.citation, item.resolved_as)
    return item
