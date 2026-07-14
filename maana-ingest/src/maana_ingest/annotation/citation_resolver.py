"""Specialized analyzer for citation resolution."""

from maana_ingest.annotation.base import BaseAnnotationAnalyzer
from maana_ingest.annotation.models import CitationResolutionOutput


class CitationResolver(BaseAnnotationAnalyzer[CitationResolutionOutput]):
    name = "citation_resolver"
    result_model = CitationResolutionOutput
    instructions = (
        "Identify and resolve citations to books, people, events, or named works where possible. "
        "Return JSON with a `citations` array of objects containing "
        "`citation`, optional `resolved_as`, optional `citation_type`, optional `confidence`, "
        "optional `notes`, optional `interpretation_hints`, and `evidence`."
    )
