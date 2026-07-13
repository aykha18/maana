"""Annotation data contracts."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class AnnotationEvidence(BaseModel):
    """Timestamp-linked evidence snippet from the cleaned transcript."""

    start: float
    end: float
    excerpt: str


class AnnotationHit(BaseModel):
    """Generic analyzer hit with evidence."""

    label: str
    text: str
    confidence: float | None = None
    notes: str | None = None
    evidence: list[AnnotationEvidence] = Field(default_factory=list)


class CitationHit(BaseModel):
    """Resolved citation candidate."""

    citation: str
    resolved_as: str | None = None
    citation_type: str | None = None
    confidence: float | None = None
    notes: str | None = None
    evidence: list[AnnotationEvidence] = Field(default_factory=list)


class CoupletDetectionOutput(BaseModel):
    couplets: list[AnnotationHit] = Field(default_factory=list)


class QuranDetectionOutput(BaseModel):
    verses: list[AnnotationHit] = Field(default_factory=list)


class HadithDetectionOutput(BaseModel):
    hadiths: list[AnnotationHit] = Field(default_factory=list)


class PoetDetectionOutput(BaseModel):
    poets: list[AnnotationHit] = Field(default_factory=list)


class PersianDetectionOutput(BaseModel):
    passages: list[AnnotationHit] = Field(default_factory=list)


class CitationResolutionOutput(BaseModel):
    citations: list[CitationHit] = Field(default_factory=list)


class PromptRecord(BaseModel):
    analyzer_name: str
    prompt_version: str
    provider: str
    model_name: str
    prompt_path: Path


class AnalyzerExecution(BaseModel):
    analyzer_name: str
    prompt_version: str
    prompt_path: Path
    output_path: Path
    raw_response_path: Path
    skipped: bool = False
    item_count: int = 0


class MergedChapterAnnotation(BaseModel):
    chapter_number: int
    source_cleaned_path: Path
    merged_output_path: Path
    couplets: list[AnnotationHit] = Field(default_factory=list)
    quran_references: list[AnnotationHit] = Field(default_factory=list)
    hadith_references: list[AnnotationHit] = Field(default_factory=list)
    poets: list[AnnotationHit] = Field(default_factory=list)
    persian_passages: list[AnnotationHit] = Field(default_factory=list)
    citations: list[CitationHit] = Field(default_factory=list)
    analyzers: list[AnalyzerExecution] = Field(default_factory=list)


class AnnotationManifest(BaseModel):
    lecture_root: Path
    annotation_dir: Path
    provider: str
    model_name: str
    prompt_version: str
    completed_chapters: int
    skipped_chapters: int
    chapters: list[MergedChapterAnnotation] = Field(default_factory=list)


class AnnotationResult(BaseModel):
    lecture_root: Path
    annotation_manifest_path: Path
    provider: str
    model_name: str
    prompt_version: str
    completed_chapters: int
    skipped_chapters: int
    chapter_count: int
