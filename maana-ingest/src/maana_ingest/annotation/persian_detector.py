"""Specialized analyzer for Persian passages."""

from maana_ingest.annotation.base import BaseAnnotationAnalyzer
from maana_ingest.annotation.models import PersianDetectionOutput


class PersianDetector(BaseAnnotationAnalyzer[PersianDetectionOutput]):
    name = "persian_detector"
    result_model = PersianDetectionOutput
    instructions = (
        "Identify Persian passages, phrases, or lines distinct from surrounding Urdu commentary. "
        "Return JSON with a `passages` array of objects containing "
        "`label`, `text`, optional `confidence`, optional `notes`, optional `interpretation_hints`, "
        "and `evidence`."
    )
