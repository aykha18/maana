"""Specialized analyzer for Quran references."""

from maana_ingest.annotation.base import BaseAnnotationAnalyzer
from maana_ingest.annotation.models import QuranDetectionOutput


class QuranDetector(BaseAnnotationAnalyzer[QuranDetectionOutput]):
    name = "quran_detector"
    result_model = QuranDetectionOutput
    instructions = (
        "Identify direct Quran quotations or references to surah and ayah. "
        "Return JSON with a `verses` array of objects containing "
        "`label`, `text`, optional `confidence`, optional `notes`, and `evidence`."
    )
