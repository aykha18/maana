"""Curator backend workflow over lecture claim bundles."""

from __future__ import annotations

import json
from pathlib import Path

from maana_ingest.config import Settings
from maana_ingest.ontology.models import (
    AppliedClaimReviewItem,
    AppliedLectureClaimReviewFile,
    ApplyLectureClaimReviewResult,
    CanonicalEntityCandidate,
    CanonicalMappingStatus,
    CanonicalRegistry,
    CanonicalRegistryEntry,
    CuratorClaimDecision,
    CuratorClaimReviewItem,
    CuratorOntologyCandidateReview,
    CuratorOntologyDecision,
    EditorialState,
    KnowledgeManifest,
    KnowledgeReviewStatus,
    LectureClaimReviewFile,
    LectureClaimReviewResult,
    TruthStatus,
)
from maana_ingest.ontology.resolver import (
    CanonicalRegistryError,
    CanonicalRegistryResolver,
    normalize_registry_label,
)


class LectureCuratorReviewError(RuntimeError):
    """Raised when lecture claim review files cannot be prepared or applied."""


class LectureCuratorReviewService:
    """Prepare and apply curator review over governed lecture claim bundles."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_review_file(
        self,
        knowledge_manifest_path: Path,
        *,
        output_path: Path | None = None,
    ) -> LectureClaimReviewResult:
        manifest_path = knowledge_manifest_path.expanduser().resolve()
        if not manifest_path.exists():
            raise LectureCuratorReviewError(f"Knowledge manifest not found: {manifest_path}")

        manifest = self._load_manifest(manifest_path)
        review_output_path = (
            output_path.expanduser().resolve()
            if output_path is not None
            else manifest_path.with_name(f"{manifest_path.stem}.review.json")
        )
        review_output_path.parent.mkdir(parents=True, exist_ok=True)

        items: list[CuratorClaimReviewItem] = []
        for chapter in manifest.chapters:
            if chapter.claim_bundle_path is None:
                continue
            bundle_path = chapter.claim_bundle_path.expanduser().resolve()
            if not bundle_path.exists():
                raise LectureCuratorReviewError(f"Claim bundle not found: {bundle_path}")
            bundle = self._load_claim_bundle(bundle_path)
            for claim in bundle.claims:
                ontology_reviews = [
                    CuratorOntologyCandidateReview(
                        entity_type=candidate.entity_type,
                        submitted_label=candidate.label,
                        normalized_label=candidate.normalized_label,
                        current_mapping_status=candidate.mapping_status,
                        suggested_canonical_id=(
                            candidate.canonical_id or build_canonical_id(candidate.entity_type, candidate.label)
                        ),
                    )
                    for candidate in claim.ontology_candidates
                ]
                items.append(
                    CuratorClaimReviewItem(
                        chapter_number=chapter.chapter_number,
                        claim_id=claim.claim_id,
                        claim_type=claim.claim_type,
                        statement=claim.statement,
                        source_stage=claim.source_stage,
                        evidence_posture=claim.evidence_posture,
                        current_editorial_state=claim.review.editorial_state,
                        current_truth_status=claim.review.truth_status,
                        approval_scope=claim.review.approval_scope,
                        ontology_reviews=ontology_reviews,
                    )
                )

        review_file = LectureClaimReviewFile(
            lecture_root=manifest.lecture_root,
            knowledge_manifest_path=manifest_path,
            review_path=review_output_path,
            total_items=len(items),
            pending_items=len(items),
            items=items,
        )
        review_output_path.write_text(
            json.dumps(review_file.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return LectureClaimReviewResult(
            lecture_root=manifest.lecture_root,
            review_path=review_output_path,
            total_items=len(items),
            pending_items=len(items),
        )

    def apply_review_file(self, review_path: Path) -> ApplyLectureClaimReviewResult:
        resolved_review_path = review_path.expanduser().resolve()
        if not resolved_review_path.exists():
            raise LectureCuratorReviewError(f"Review file not found: {resolved_review_path}")

        review_file = self._load_review_file(resolved_review_path)
        manifest = self._load_manifest(review_file.knowledge_manifest_path)

        registry: CanonicalRegistry | None = None
        resolver: CanonicalRegistryResolver | None = None
        registry_path: Path | None = None
        if self._settings.canonical_registry_path is not None:
            registry_path = self._settings.canonical_registry_path.expanduser().resolve()
            try:
                resolver = CanonicalRegistryResolver.from_path(registry_path)
            except CanonicalRegistryError as exc:
                raise LectureCuratorReviewError(str(exc)) from exc
            registry = resolver.registry.model_copy(deep=True)
            resolver = CanonicalRegistryResolver(registry)

        items_by_claim = {
            (item.chapter_number, item.claim_id): item
            for item in review_file.items
        }

        approved_claims = 0
        rejected_claims = 0
        revision_requested_claims = 0
        pending_claims = 0
        ontology_appended_entries = 0
        ontology_approved_existing = 0
        ontology_rejected = 0
        applied_items: list[AppliedClaimReviewItem] = []

        for chapter in manifest.chapters:
            if chapter.claim_bundle_path is None:
                continue
            bundle_path = chapter.claim_bundle_path.expanduser().resolve()
            bundle = self._load_claim_bundle(bundle_path)
            chapter_has_pending = False
            chapter_has_rejected = False

            for claim in bundle.claims:
                review_item = items_by_claim.get((chapter.chapter_number, claim.claim_id))
                if review_item is None:
                    chapter_has_pending = True
                    pending_claims += 1
                    applied_items.append(
                        AppliedClaimReviewItem(
                            chapter_number=chapter.chapter_number,
                            claim_id=claim.claim_id,
                            decision=CuratorClaimDecision.PENDING,
                            status="missing_review_item",
                            resulting_editorial_state=claim.review.editorial_state,
                            resulting_truth_status=claim.review.truth_status,
                        )
                    )
                    continue

                ontology_results: list[str] = []
                self._apply_ontology_decisions(
                    claim.ontology_candidates,
                    review_item.ontology_reviews,
                    registry=registry,
                    resolver=resolver,
                    ontology_results=ontology_results,
                )
                ontology_appended_entries += sum(1 for status in ontology_results if status.startswith("appended_new"))
                ontology_approved_existing += sum(
                    1 for status in ontology_results if status.startswith("approved_existing")
                )
                ontology_rejected += sum(1 for status in ontology_results if status.startswith("rejected"))

                if review_item.decision is CuratorClaimDecision.APPROVE:
                    claim.review.editorial_state = EditorialState.APPROVED
                    claim.review.truth_status = review_item.reviewed_truth_status or TruthStatus.SUPPORTED
                    claim.review.reviewed_by = review_item.reviewed_by
                    claim.review.notes = review_item.notes
                    approved_claims += 1
                    item_status = "approved"
                elif review_item.decision is CuratorClaimDecision.REJECT:
                    claim.review.editorial_state = EditorialState.REJECTED
                    claim.review.truth_status = TruthStatus.DEPRECATED
                    claim.review.reviewed_by = review_item.reviewed_by
                    claim.review.notes = review_item.notes
                    rejected_claims += 1
                    chapter_has_rejected = True
                    item_status = "rejected"
                elif review_item.decision is CuratorClaimDecision.REQUEST_REVISION:
                    claim.review.editorial_state = EditorialState.IN_REVIEW
                    claim.review.truth_status = review_item.reviewed_truth_status or TruthStatus.UNRESOLVED
                    claim.review.reviewed_by = review_item.reviewed_by
                    claim.review.notes = review_item.notes
                    revision_requested_claims += 1
                    chapter_has_pending = True
                    item_status = "revision_requested"
                else:
                    pending_claims += 1
                    chapter_has_pending = True
                    item_status = "pending"

                applied_items.append(
                    AppliedClaimReviewItem(
                        chapter_number=chapter.chapter_number,
                        claim_id=claim.claim_id,
                        decision=review_item.decision,
                        status=item_status,
                        resulting_editorial_state=claim.review.editorial_state,
                        resulting_truth_status=claim.review.truth_status,
                        ontology_results=ontology_results,
                        notes=review_item.notes,
                    )
                )

            bundle.review_status = _bundle_review_status(bundle)
            bundle.claim_count = len(bundle.claims)
            bundle.bundle_path.write_text(
                json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            chapter.review_status = bundle.review_status
            chapter.claim_count = bundle.claim_count
            if chapter_has_pending:
                manifest.chapters_pending_review += 0
            if chapter_has_rejected:
                chapter.blockers = _append_unique(chapter.blockers, "One or more claims were rejected during review.")

        manifest.chapters_pending_review = sum(
            1 for chapter in manifest.chapters if chapter.review_status is KnowledgeReviewStatus.PENDING_REVIEW
        )
        manifest.ready_for_canonical_ingestion = (
            manifest.chapters_pending_review == 0
            and all(chapter.review_status is KnowledgeReviewStatus.APPROVED for chapter in manifest.chapters)
        )
        manifest.manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if registry is not None and registry_path is not None:
            registry.entries.sort(
                key=lambda entry: (entry.entity_type.value, entry.normalized_label or entry.label.lower())
            )
            registry_path.write_text(
                json.dumps(registry.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        applied_path = resolved_review_path.with_name(f"{resolved_review_path.stem}.applied.json")
        applied_file = AppliedLectureClaimReviewFile(
            lecture_root=review_file.lecture_root,
            review_path=resolved_review_path,
            registry_path=registry_path,
            applied_path=applied_path,
            approved_claims=approved_claims,
            rejected_claims=rejected_claims,
            revision_requested_claims=revision_requested_claims,
            pending_claims=pending_claims,
            ontology_appended_entries=ontology_appended_entries,
            ontology_approved_existing=ontology_approved_existing,
            ontology_rejected=ontology_rejected,
            items=applied_items,
        )
        applied_path.write_text(
            json.dumps(applied_file.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return ApplyLectureClaimReviewResult(
            review_path=resolved_review_path,
            applied_path=applied_path,
            registry_path=registry_path,
            approved_claims=approved_claims,
            rejected_claims=rejected_claims,
            revision_requested_claims=revision_requested_claims,
            pending_claims=pending_claims,
            ontology_appended_entries=ontology_appended_entries,
            ontology_approved_existing=ontology_approved_existing,
            ontology_rejected=ontology_rejected,
        )

    @staticmethod
    def _load_manifest(path: Path) -> KnowledgeManifest:
        try:
            return KnowledgeManifest.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise LectureCuratorReviewError(f"Knowledge manifest is invalid: {path}") from exc

    @staticmethod
    def _load_claim_bundle(path: Path):  # type: ignore[no-untyped-def]
        from maana_ingest.ontology.models import ChapterClaimBundle

        try:
            return ChapterClaimBundle.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise LectureCuratorReviewError(f"Claim bundle is invalid: {path}") from exc

    @staticmethod
    def _load_review_file(path: Path) -> LectureClaimReviewFile:
        try:
            return LectureClaimReviewFile.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise LectureCuratorReviewError(f"Lecture review file is invalid: {path}") from exc

    def _apply_ontology_decisions(
        self,
        candidates: list[CanonicalEntityCandidate],
        reviews: list[CuratorOntologyCandidateReview],
        *,
        registry: CanonicalRegistry | None,
        resolver: CanonicalRegistryResolver | None,
        ontology_results: list[str],
    ) -> None:
        review_lookup = {
            (review.entity_type, normalize_registry_label(review.submitted_label)): review for review in reviews
        }
        for candidate in candidates:
            key = (candidate.entity_type, normalize_registry_label(candidate.label))
            review = review_lookup.get(key)
            if review is None or review.decision is CuratorOntologyDecision.PENDING:
                ontology_results.append(f"pending:{candidate.entity_type.value}:{candidate.label}")
                continue
            if review.decision is CuratorOntologyDecision.REJECT:
                candidate.mapping_status = CanonicalMappingStatus.UNRESOLVED
                candidate.canonical_id = None
                candidate.rationale = _merge_notes(candidate.rationale, review.notes, "Rejected by curator.")
                ontology_results.append(f"rejected:{candidate.entity_type.value}:{candidate.label}")
                continue

            if registry is None or resolver is None:
                raise LectureCuratorReviewError(
                    "CANONICAL_REGISTRY_PATH must be configured to apply ontology approval decisions."
                )

            if review.decision is CuratorOntologyDecision.APPROVE_EXISTING:
                existing_canonical_id = (review.existing_canonical_id or "").strip()
                if not existing_canonical_id:
                    raise LectureCuratorReviewError(
                        "approve_existing requires existing_canonical_id "
                        f"for candidate {candidate.entity_type.value}:{candidate.label}"
                    )
                existing_entry = _find_registry_entry_by_id(registry, existing_canonical_id)
                if existing_entry is None:
                    raise LectureCuratorReviewError(f"Existing canonical ID not found in registry: {existing_canonical_id}")
                if existing_entry.entity_type is not candidate.entity_type:
                    raise LectureCuratorReviewError(
                        "Existing canonical ID has wrong entity type "
                        f"for candidate {candidate.entity_type.value}:{candidate.label}"
                    )
                candidate.mapping_status = CanonicalMappingStatus.MATCHED
                candidate.canonical_id = existing_entry.canonical_id
                candidate.rationale = _merge_notes(candidate.rationale, review.notes, "Mapped to existing canonical entity.")
                ontology_results.append(
                    f"approved_existing:{candidate.entity_type.value}:{candidate.label}:{existing_entry.canonical_id}"
                )
                continue

            approved_label = (review.approved_label or candidate.label).strip()
            if not approved_label:
                raise LectureCuratorReviewError(
                    f"Approved label is empty for candidate {candidate.entity_type.value}:{candidate.label}"
                )

            resolution = resolver.resolve(entity_type=candidate.entity_type, label=approved_label)
            if resolution.mapping_status is CanonicalMappingStatus.MATCHED:
                existing_entry = resolution.matched_entry
                candidate.mapping_status = CanonicalMappingStatus.MATCHED
                candidate.canonical_id = existing_entry.canonical_id if existing_entry is not None else None
                candidate.label = approved_label
                candidate.normalized_label = normalize_registry_label(approved_label)
                candidate.rationale = _merge_notes(
                    candidate.rationale,
                    review.notes,
                    "Approved label already exists in registry; reused existing canonical entity.",
                )
                ontology_results.append(
                    f"approved_existing:{candidate.entity_type.value}:{candidate.label}:{candidate.canonical_id}"
                )
                continue

            canonical_id = (review.suggested_canonical_id or build_canonical_id(candidate.entity_type, approved_label)).strip()
            if any(entry.canonical_id == canonical_id for entry in registry.entries):
                raise LectureCuratorReviewError(f"Canonical ID already exists in registry: {canonical_id}")

            entry = CanonicalRegistryEntry(
                canonical_id=canonical_id,
                entity_type=candidate.entity_type,
                label=approved_label,
                normalized_label=normalize_registry_label(approved_label),
                description=review.description,
                aliases=sorted({alias.strip() for alias in review.aliases if alias.strip()}),
                source_notes=_build_source_notes(review.notes),
            )
            registry.entries.append(entry)
            resolver = CanonicalRegistryResolver(registry)
            candidate.mapping_status = CanonicalMappingStatus.MATCHED
            candidate.canonical_id = entry.canonical_id
            candidate.label = approved_label
            candidate.normalized_label = entry.normalized_label
            candidate.rationale = _merge_notes(candidate.rationale, review.notes, "Created new canonical entity.")
            ontology_results.append(f"appended_new:{candidate.entity_type.value}:{approved_label}:{entry.canonical_id}")


def build_canonical_id(entity_type, label: str) -> str:  # type: ignore[no-untyped-def]
    prefix_map = {
        "human_experience": "experience",
        "literary_work": "literary-work",
        "literary_unit": "literary-unit",
    }
    prefix = prefix_map.get(entity_type.value, entity_type.value.replace("_", "-"))
    slug = normalize_registry_label(label).replace(" ", "-")
    return f"{prefix}.{slug}"


def _find_registry_entry_by_id(registry: CanonicalRegistry, canonical_id: str) -> CanonicalRegistryEntry | None:
    for entry in registry.entries:
        if entry.canonical_id == canonical_id:
            return entry
    return None


def _build_source_notes(notes: str | None) -> list[str]:
    source_notes = ["Approved from lecture claim review workflow."]
    if notes:
        source_notes.append(notes.strip())
    return source_notes


def _merge_notes(original: str | None, review_notes: str | None, default: str) -> str:
    values = [value.strip() for value in (original, review_notes, default) if value and value.strip()]
    return " ".join(values)


def _append_unique(values: list[str], value: str) -> list[str]:
    if value in values:
        return values
    return [*values, value]


def _bundle_review_status(bundle) -> KnowledgeReviewStatus:  # type: ignore[no-untyped-def]
    if not bundle.claims:
        return KnowledgeReviewStatus.PENDING_REVIEW
    if all(claim.review.editorial_state is EditorialState.APPROVED for claim in bundle.claims):
        return KnowledgeReviewStatus.APPROVED
    if any(claim.review.editorial_state is EditorialState.REJECTED for claim in bundle.claims):
        return KnowledgeReviewStatus.REJECTED
    return KnowledgeReviewStatus.PENDING_REVIEW
