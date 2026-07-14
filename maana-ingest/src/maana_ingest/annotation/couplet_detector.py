"""Specialized analyzer for poetry and couplet detection."""

from maana_ingest.annotation.base import BaseAnnotationAnalyzer
from maana_ingest.annotation.models import CoupletDetectionOutput


class CoupletDetector(BaseAnnotationAnalyzer[CoupletDetectionOutput]):
    name = "couplet_detector"
    result_model = CoupletDetectionOutput
    instructions = (
        "Identify quoted or recited couplets, verses, or poetic fragments. "
        "Return JSON with a `couplets` array of objects containing "
        "`label`, `text`, optional `confidence`, optional `notes`, optional `interpretation_hints`, "
        "and `evidence`."
    )
