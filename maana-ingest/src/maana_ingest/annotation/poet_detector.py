"""Specialized analyzer for poet mentions."""

from maana_ingest.annotation.base import BaseAnnotationAnalyzer
from maana_ingest.annotation.models import PoetDetectionOutput


class PoetDetector(BaseAnnotationAnalyzer[PoetDetectionOutput]):
    name = "poet_detector"
    result_model = PoetDetectionOutput
    instructions = (
        "Identify named poets or strong poet attributions in the transcript. "
        "Return JSON with a `poets` array of objects containing "
        "`label`, `text`, optional `confidence`, optional `notes`, and `evidence`."
    )
