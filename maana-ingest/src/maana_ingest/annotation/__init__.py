"""Annotation pipeline package."""

from maana_ingest.annotation.client import (
    AnnotationClientFactory,
    AnnotationLLMClient,
    MockAnnotationLLMClient,
    OpenAICompatibleAnnotationLLMClient,
)
from maana_ingest.annotation.models import AnnotationManifest, AnnotationResult, MergedChapterAnnotation
from maana_ingest.annotation.service import AnnotationError, AnnotationService

__all__ = [
    "AnnotationClientFactory",
    "AnnotationError",
    "AnnotationLLMClient",
    "AnnotationManifest",
    "AnnotationResult",
    "AnnotationService",
    "MergedChapterAnnotation",
    "MockAnnotationLLMClient",
    "OpenAICompatibleAnnotationLLMClient",
]
