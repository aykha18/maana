"""Merger stage for specialized analyzer outputs."""

from maana_ingest.annotation.models import (
    AnalyzerExecution,
    CitationResolutionOutput,
    CoupletDetectionOutput,
    HadithDetectionOutput,
    MergedChapterAnnotation,
    PersianDetectionOutput,
    PoetDetectionOutput,
    QuranDetectionOutput,
)
from pathlib import Path


def merge_chapter_annotations(
    *,
    chapter_number: int,
    source_cleaned_path: Path,
    merged_output_path: Path,
    analyzers: list[AnalyzerExecution],
    couplets: CoupletDetectionOutput,
    quran: QuranDetectionOutput,
    hadith: HadithDetectionOutput,
    poets: PoetDetectionOutput,
    persian: PersianDetectionOutput,
    citations: CitationResolutionOutput,
) -> MergedChapterAnnotation:
    return MergedChapterAnnotation(
        chapter_number=chapter_number,
        source_cleaned_path=source_cleaned_path.resolve(),
        merged_output_path=merged_output_path.resolve(),
        analyzers=analyzers,
        couplets=couplets.couplets,
        quran_references=quran.verses,
        hadith_references=hadith.hadiths,
        poets=poets.poets,
        persian_passages=persian.passages,
        citations=citations.citations,
    )
