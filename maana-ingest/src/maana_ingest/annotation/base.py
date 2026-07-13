"""Base analyzer implementation for specialized annotation stages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from maana_ingest.annotation.client import AnnotationLLMClient, AnnotationRequest
from maana_ingest.annotation.models import AnalyzerExecution
from maana_ingest.annotation.prompts import build_prompt_package
from maana_ingest.cleaning.models import CleanedChapterTranscript

T = TypeVar("T", bound=BaseModel)


class BaseAnnotationAnalyzer(Generic[T]):
    """Shared prompt, persistence, and validation behavior for analyzers."""

    name: str
    result_model: type[T]
    instructions: str

    def analyze(
        self,
        *,
        chapter: CleanedChapterTranscript,
        chapter_output_dir: Path,
        client: AnnotationLLMClient,
        prompt_version: str,
        force: bool = False,
    ) -> tuple[T, AnalyzerExecution]:
        prompt_path = chapter_output_dir / "prompts" / f"{self.name}-{prompt_version}.md"
        output_path = chapter_output_dir / f"{self.name}.json"
        raw_response_path = chapter_output_dir / f"{self.name}.raw.json"

        if not force and output_path.exists() and raw_response_path.exists() and prompt_path.exists():
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            result = self.result_model.model_validate(payload)
            return result, AnalyzerExecution(
                analyzer_name=self.name,
                prompt_version=prompt_version,
                prompt_path=prompt_path.resolve(),
                output_path=output_path.resolve(),
                raw_response_path=raw_response_path.resolve(),
                skipped=True,
                item_count=self.item_count(result),
            )

        prompt_package = build_prompt_package(
            analyzer_name=self.name,
            version=prompt_version,
            instructions=self.instructions,
            chapter=chapter,
        )
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_package.render(), encoding="utf-8")

        raw_response = client.annotate_json(
            AnnotationRequest(
                analyzer_name=self.name,
                prompt_version=prompt_version,
                system_prompt=prompt_package.system_prompt,
                user_prompt=prompt_package.user_prompt,
            )
        )
        raw_response_path.write_text(
            json.dumps(raw_response, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        result = self.result_model.model_validate(raw_response)
        output_path.write_text(
            json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return result, AnalyzerExecution(
            analyzer_name=self.name,
            prompt_version=prompt_version,
            prompt_path=prompt_path.resolve(),
            output_path=output_path.resolve(),
            raw_response_path=raw_response_path.resolve(),
            skipped=False,
            item_count=self.item_count(result),
        )

    @staticmethod
    def item_count(result: BaseModel) -> int:
        payload = result.model_dump()
        total = 0
        for value in payload.values():
            if isinstance(value, list):
                total += len(value)
        return total
