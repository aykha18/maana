"""Prompt construction for specialized annotation analyzers."""

from __future__ import annotations

from dataclasses import dataclass

from maana_ingest.cleaning.models import CleanedChapterTranscript


@dataclass(frozen=True)
class PromptPackage:
    """Compiled prompt plus metadata for persistence."""

    analyzer_name: str
    version: str
    system_prompt: str
    user_prompt: str

    def render(self) -> str:
        return (
            f"# Analyzer: {self.analyzer_name}\n"
            f"# Version: {self.version}\n\n"
            "## System Prompt\n\n"
            f"{self.system_prompt}\n\n"
            "## User Prompt\n\n"
            f"{self.user_prompt}\n"
        )


def build_prompt_package(
    *,
    analyzer_name: str,
    version: str,
    instructions: str,
    chapter: CleanedChapterTranscript,
) -> PromptPackage:
    system_prompt = (
        "You are a structured literary annotation analyzer. "
        "Return valid JSON only. Do not include markdown fences."
    )
    user_prompt = (
        f"Analyzer: {analyzer_name}\n"
        f"Prompt Version: {version}\n"
        f"Chapter Number: {chapter.chapter_number}\n"
        f"Language Hint: {chapter.language or 'unknown'}\n\n"
        "Instructions:\n"
        f"{instructions}\n\n"
        "Cleaned Transcript:\n"
        f"{chapter.cleaned_text}\n"
    )
    return PromptPackage(
        analyzer_name=analyzer_name,
        version=version,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
