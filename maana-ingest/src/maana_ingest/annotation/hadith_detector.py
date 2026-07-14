"""Specialized analyzer for hadith references."""

from maana_ingest.annotation.base import BaseAnnotationAnalyzer
from maana_ingest.annotation.models import HadithDetectionOutput


class HadithDetector(BaseAnnotationAnalyzer[HadithDetectionOutput]):
    name = "hadith_detector"
    result_model = HadithDetectionOutput
    instructions = (
        "Identify hadith quotations, collections, or clear references to prophetic reports. "
        "Return JSON with a `hadiths` array of objects containing "
        "`label`, `text`, optional `confidence`, optional `notes`, optional `interpretation_hints`, "
        "and `evidence`."
    )
