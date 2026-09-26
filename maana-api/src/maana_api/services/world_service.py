"""World service: lifecycle, governance, versioning, and projection."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlmodel import Session, select

from maana_api.config import get_settings
from maana_api.domain.models import (
    Chapter,
    Claim,
    ClaimStatus,
    ClaimType,
    OntologyRegistryEntry,
    Relation,
    RelationType,
    Scope,
    SemanticCluster,
    SemanticPath,
    World,
    WorldStatus,
)
from maana_api.infrastructure.database import get_sync_engine
from maana_api.infrastructure.graph import get_graph_projection
from maana_api.infrastructure.projection import project
from maana_api.infrastructure.vector_store import get_vector_store
from maana_api.services.validation import (
    InvariantViolation,
    require_provenance,
    validate_scope_value,
    validate_subject_reference,
)

settings = get_settings()

#: Claim types that describe the merge itself and are retained verbatim
#: against the source World rather than re-pointed to the target (Ontology §8.4).
MERGE_JUSTIFICATION_CLAIM_TYPES = frozenset(
    {ClaimType.COMPARATIVE.value, ClaimType.ONTOLOGICAL.value}
)


class WorldService:
    """Service for World lifecycle, governance, versioning, and projection."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._graph = get_graph_projection()
        self._vector = get_vector_store(session)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_world(self, world_id: str) -> World | None:
        """Get a World by ID."""
        statement = select(World).where(World.world_id == world_id)
        return self._session.exec(statement).first()

    def resolve_world(self, world_id: str) -> World | None:
        """Resolve a World ID through merge and supersede redirects (I-061).

        A merged or superseded World keeps its row so that historical citations
        still resolve, and points ``current_version_id`` at the surviving
        record. Following that pointer makes lookup by a retired ID land on
        live knowledge in a single hop.
        """

        seen: set[str] = set()
        current = self.get_world(world_id)
        while current is not None and current.current_version_id:
            if current.world_id in seen:  # defensive: a cycle must not hang
                raise InvariantViolation(
                    "I-061",
                    f"version redirect cycle detected at {current.world_id}",
                )
            seen.add(current.world_id)
            nxt = self.get_world(current.current_version_id)
            if nxt is None:
                break
            current = nxt
        return current

    def list_worlds(
        self, status: WorldStatus | None = None, scope: Scope | None = None
    ) -> list[World]:
        """List Worlds with optional filters."""
        statement = select(World)
        if status is not None:
            statement = statement.where(World.status == status)
        if scope is not None:
            statement = statement.where(World.scope == scope)
        return list(self._session.exec(statement).all())

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def create_world(self, world: World) -> World:
        """Create a new World in PROPOSED state."""
        validate_scope_value(
            world.scope.value if isinstance(world.scope, Scope) else world.scope
        )
        self._session.add(world)
        self._session.commit()
        self._session.refresh(world)
        return world

    def update_world(self, world_id: str, updates: dict[str, Any]) -> World | None:
        """Update a World. Only DRAFT or PROPOSED Worlds are mutable (I-056)."""
        world = self.get_world(world_id)
        if world is None:
            return None
        if world.status not in (WorldStatus.DRAFT, WorldStatus.PROPOSED):
            raise ValueError(f"Cannot update World in status: {world.status}")
        for key, value in updates.items():
            setattr(world, key, value)
        world.updated_at = datetime.utcnow()
        self._session.add(world)
        self._session.commit()
        self._session.refresh(world)
        return world

    def approve_world(self, world_id: str) -> World | None:
        """Approve a World, project to graph, and generate embeddings."""
        world = self.get_world(world_id)
        if world is None:
            return None
        require_provenance(world)
        world.status = WorldStatus.APPROVED
        world.updated_at = datetime.utcnow()
        self._session.add(world)
        self._session.commit()
        self._session.refresh(world)
        # A projection failure does not undo a governance decision: PostgreSQL
        # is authoritative and the node is repairable (Ontology I-076, I-077).
        project(
            "create_world_node",
            "world",
            world.world_id,
            lambda: self._graph.create_world_node(world),
        )
        return world

    def deprecate_world(self, world_id: str) -> World | None:
        """Deprecate a World (I-046: DEPRECATED is not terminal)."""
        world = self.get_world(world_id)
        if world is None:
            return None
        world.status = WorldStatus.DEPRECATED
        world.updated_at = datetime.utcnow()
        self._session.add(world)
        self._session.commit()
        self._session.refresh(world)
        return world

    def reinstate_world(self, world_id: str) -> World | None:
        """Reinstate a DEPRECATED World to APPROVED (Ontology §7.1)."""
        world = self.get_world(world_id)
        if world is None:
            return None
        if world.status != WorldStatus.DEPRECATED:
            raise ValueError(f"Only DEPRECATED Worlds can be reinstated: {world.status}")
        world.status = WorldStatus.APPROVED
        world.updated_at = datetime.utcnow()
        self._session.add(world)
        self._session.commit()
        self._session.refresh(world)
        return world

    # ------------------------------------------------------------------
    # Versioning (Ontology §8.3)
    # ------------------------------------------------------------------

    def supersede_world(
        self, world_id: str, new_world_id: str, corrections: dict[str, Any] | None = None
    ) -> World | None:
        """Create a new version of a World and retire the original (I-053).

        Versions are new IDs, never mutated IDs: ``world_id`` permanently
        remains the first version, which is what makes the audit trail
        trustworthy. The original row is retained and marked SUPERSEDED so that
        citations against it still resolve.
        """

        original = self.get_world(world_id)
        if original is None:
            return None
        if new_world_id == world_id:
            raise InvariantViolation("I-001", "a version must have a new ID")
        if original.status in (WorldStatus.MERGED, WorldStatus.SUPERSEDED):
            raise ValueError(
                f"Cannot supersede a World in terminal status: {original.status}"
            )
        if self.get_world(new_world_id) is not None:
            raise ValueError(f"Target version already exists: {new_world_id}")

        successor = _clone_world(original, new_world_id)
        successor.version_history = list(original.version_history) + [world_id]
        if corrections:
            for key, value in corrections.items():
                setattr(successor, key, value)
        successor.status = WorldStatus.APPROVED
        successor.created_at = datetime.utcnow()
        successor.updated_at = datetime.utcnow()

        original.status = WorldStatus.SUPERSEDED
        original.current_version_id = new_world_id
        original.updated_at = datetime.utcnow()

        self._session.add(successor)
        self._session.add(original)
        self._session.commit()
        self._session.refresh(successor)
        self._session.refresh(original)

        project(
            "create_world_node",
            "world",
            successor.world_id,
            lambda: self._graph.create_world_node(successor),
        )
        self._repoint_edges(world_id, new_world_id)
        return successor
    def _repoint_edges(self, old_world_id: str, new_world_id: str) -> None:
        """Re-point incoming and outgoing Relations at a new version (I-057)."""

        statement = select(Relation).where(
            (Relation.source_world_id == old_world_id)
            | (Relation.target_world_id == old_world_id)
        )
        for relation in self._session.exec(statement).all():
            if relation.source_world_id == old_world_id:
                relation.source_world_id = new_world_id
            if relation.target_world_id == old_world_id:
                relation.target_world_id = new_world_id
            self._session.add(relation)
        self._session.commit()

    # ------------------------------------------------------------------
    # Merge and split (Ontology §8.4 - §8.6)
    # ------------------------------------------------------------------

    def merge_worlds(self, source_id: str, target_id: str) -> World | None:
        """Merge ``source_id`` into ``target_id``. Nothing disappears.

        Both Worlds must be APPROVED. On success the source is marked MERGED,
        redirected to the target in a single hop, its Claims and Relations
        re-pointed, and a ``merged_into`` Relation recorded so the
        relationship survives independently of the redirect.
        """

        source = self.get_world(source_id)
        target = self.get_world(target_id)
        if source is None or target is None:
            return None
        if source.world_id == target.world_id:
            raise InvariantViolation("I-021", "a World cannot be merged into itself")
        if source.status != WorldStatus.APPROVED or target.status != WorldStatus.APPROVED:
            raise ValueError("Only APPROVED Worlds can be merged")
        if source.status == WorldStatus.MERGED:
            raise InvariantViolation(
                "I-060", f"{source_id} is already merged; merge into its surviving target"
            )

        self._reassign([source], [target])
        return target

    def split_world(
        self,
        parent_id: str,
        children: list[dict[str, Any]],
        axis: str | None = None,
    ) -> list[World]:
        """Split one World into several along a recorded axis (Ontology §8.5).

        A split is a one-to-many merge: the parent is retained as a redirect to
        its children, and every Claim and Relation is assigned to exactly one
        child. ``children`` items accept ``world_id``, ``canonical_term``,
        ``claim_ids``, and ``relation_ids``.
        """

        parent = self.get_world(parent_id)
        if parent is None:
            return []
        if not children:
            raise ValueError("a split requires at least one child")
        if parent.status != WorldStatus.APPROVED:
            raise ValueError("Only APPROVED Worlds can be split")
        if not axis:
            raise InvariantViolation(
                "I-064", "a split must record the axis along which it occurred"
            )

        created: list[World] = []
        for spec in children:
            child_id = spec["world_id"]
            if self.get_world(child_id) is not None:
                raise ValueError(f"Child World already exists: {child_id}")
            child = _clone_world(parent, child_id)
            child.canonical_term = spec.get("canonical_term", child.canonical_term)
            child.central_axis = spec.get("central_axis", axis)
            child.status = WorldStatus.APPROVED
            child.created_at = datetime.utcnow()
            child.updated_at = datetime.utcnow()
            self._session.add(child)
            created.append(child)
        self._session.commit()

        # I-063: every Claim and Relation is assigned to exactly one child.
        # Assignment happens before the parent becomes a redirect, so nothing
        # is silently inherited by the first child.
        assigned_claims: set[str] = set()
        assigned_relations: set[str] = set()
        for child, spec in zip(created, children):
            claim_ids = set(spec.get("claim_ids", []))
            relation_ids = set(spec.get("relation_ids", []))
            if claim_ids & assigned_claims:
                raise ValueError(
                    f"a Claim may not be assigned to more than one child: "
                    f"{sorted(claim_ids & assigned_claims)}"
                )
            if relation_ids & assigned_relations:
                raise ValueError(
                    f"a Relation may not be assigned to more than one child: "
                    f"{sorted(relation_ids & assigned_relations)}"
                )
            assigned_claims |= claim_ids
            assigned_relations |= relation_ids
            self._assign_claims_to_child(child, claim_ids)
            self._assign_relations_to_child(parent, child, relation_ids)

        # Record the division axis on the parent before it becomes a redirect
        # (Ontology §8.5 step 8), so the reason for the split survives.
        parent.central_axis = axis
        self._reassign([parent], created)
        return created

    def _assign_claims_to_child(self, child: World, claim_ids: set[str]) -> None:
        """Move the listed Claims onto ``child`` (I-063)."""

        if not claim_ids:
            return
        for row in self._session.exec(
            select(Claim).where(Claim.claim_id.in_(claim_ids))
        ).all():
            row.subject_reference_id = child.world_id
            row.subject_label = child.canonical_term
            row.updated_at = datetime.utcnow()
            self._session.add(row)
        self._session.commit()

    def _assign_relations_to_child(
        self, parent: World, child: World, relation_ids: set[str]
    ) -> None:
        """Re-point the listed Relations from ``parent`` onto ``child`` (I-063).

        Only the parent endpoint moves. The other endpoint belongs to a
        different World and is untouched, so the relation keeps its meaning.
        """

        if not relation_ids:
            return
        for row in self._session.exec(
            select(Relation).where(Relation.relation_id.in_(relation_ids))
        ).all():
            if row.source_world_id == parent.world_id:
                row.source_world_id = child.world_id
            elif row.target_world_id == parent.world_id:
                row.target_world_id = child.world_id
            else:
                raise ValueError(
                    f"relation {row.relation_id} does not touch the parent World "
                    f"{parent.world_id} and cannot be assigned to a child"
                )
            self._session.add(row)
        self._session.commit()

    def _reassign(
        self,
        sources: list[World],
        targets: list[World],
    ) -> None:
        """The single primitive behind both merge and split (I-065).

        Sets each source MERGED, records a ``merged_into`` Relation per target,
        re-points Claims and Relations, and updates the registry so that any
        lookup by a retired ID resolves to a surviving World.
        """

        target_ids = {t.world_id for t in targets}

        for source in sources:
            if source.world_id in target_ids:
                raise InvariantViolation(
                    "I-065", f"{source.world_id} cannot be a source and a target"
                )
            if source.status == WorldStatus.MERGED:
                raise InvariantViolation(
                    "I-060", f"{source.world_id} is already merged"
                )
            if source.current_version_id:
                raise InvariantViolation(
                    "I-060",
                    f"{source.world_id} is superseded; reassign its successor instead",
                )

            for target in targets:
                self._add_merge_relation(source, target)

            # Claims: re-point assertions about the source onto the target,
            # except the claims that justify the merge itself (I-059).
            claims = self._session.exec(
                select(Claim).where(Claim.subject_reference_id == source.world_id)
            ).all()
            for claim in claims:
                if claim.claim_type in MERGE_JUSTIFICATION_CLAIM_TYPES:
                    continue
                claim.subject_reference_id = targets[0].world_id
                claim.subject_label = targets[0].canonical_term
                claim.updated_at = datetime.utcnow()
                self._session.add(claim)

            # Relations: re-point both endpoints, dropping duplicates.
            for relation in self._relations_touching(source.world_id):
                if relation.relation_type == RelationType.MERGED_INTO.value:
                    continue
                other = (
                    relation.target_world_id
                    if relation.source_world_id == source.world_id
                    else relation.source_world_id
                )
                if other in target_ids:
                    # Both endpoints now resolve to the same surviving World.
                    relation.status = WorldStatus.MERGED
                    self._session.add(relation)
                    continue
                if relation.source_world_id == source.world_id:
                    relation.source_world_id = targets[0].world_id
                else:
                    relation.target_world_id = targets[0].world_id
                self._session.add(relation)

            # Semantic paths keep their World lists resolvable.
            for path in self._session.exec(
                select(SemanticPath).where(
                    SemanticPath.world_ids.contains([source.world_id])
                )
            ).all():
                if not isinstance(path.world_ids, list):
                    continue
                path.world_ids = [
                    targets[0].world_id if wid == source.world_id else wid
                    for wid in path.world_ids
                ]
                self._session.add(path)

            source.status = WorldStatus.MERGED
            source.current_version_id = targets[0].world_id
            source.updated_at = datetime.utcnow()
            self._session.add(source)

            self._register_alias(source, targets[0])

        self._session.commit()

    def _relations_touching(self, world_id: str) -> list[Relation]:
        statement = select(Relation).where(
            (Relation.source_world_id == world_id)
            | (Relation.target_world_id == world_id)
        )
        return list(self._session.exec(statement).all())

    def _add_merge_relation(self, source: World, target: World) -> None:
        """Record ``source merged_into target`` as a first-class Relation (I-032)."""

        relation_id = f"R_{source.world_id}__merged_into__{target.world_id}"
        if self._session.get(Relation, relation_id) is not None:
            return
        provenance = [
            {
                "contributor_kind": "curator",
                "source": "merge_protocol",
                "method": "WorldService.reassign",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]
        text = (
            f"{source.canonical_term} is retained as an alias of "
            f"{target.canonical_term}."
        )
        if source.central_axis:
            text += f" The division axis is {source.central_axis}."
        self._session.add(
            Relation(
                relation_id=relation_id,
                relation_type=RelationType.MERGED_INTO.value,
                source_world_id=source.world_id,
                target_world_id=target.world_id,
                status=WorldStatus.APPROVED,
                scope=Scope.GLOBAL,
                provenance=provenance,
            )
        )
        self._session.add(
            Claim(
                claim_id=f"C_{relation_id}",
                claim_type=ClaimType.EDITORIAL.value,
                subject_kind="relation",
                subject_reference_id=relation_id,
                subject_label=relation_id,
                predicate="merged_into",
                object=target.world_id,
                text=text,
                status=ClaimStatus.APPROVED.value,
                scope=Scope.GLOBAL.value,
                confidence=1.0,
                evidence=[],
                provenance=provenance,
            )
        )

    def _register_alias(self, source: World, target: World) -> None:
        """Add the retired ID to the surviving World's alias list (I-032)."""

        entry = self._session.get(OntologyRegistryEntry, target.world_id)
        if entry is None:
            entry = OntologyRegistryEntry(
                world_id=target.world_id,
                canonical_term=target.canonical_term,
            )
        aliases = list(entry.aliases or [])
        if source.world_id not in aliases:
            aliases.append(source.world_id)
        entry.aliases = aliases
        entry.status = _enum_value(target.status)
        self._session.add(entry)

    # ------------------------------------------------------------------
    # Claims about this World
    # ------------------------------------------------------------------

    def create_claim(self, claim: Claim) -> Claim:
        """Create a Claim, validating its subject reference (I-039)."""
        validate_subject_reference(self._session, claim)
        self._session.add(claim)
        self._session.commit()
        self._session.refresh(claim)
        return claim


def _enum_value(value: Any) -> str:
    """Normalize an enum-or-string column value to its stored string form.

    Enum-typed columns are declared as ``Text`` (see ``enum_column``), so a
    value read back from the database is a plain ``str`` while a freshly
    constructed object may still hold the enum member.
    """

    return value.value if hasattr(value, "value") else str(value)


def _clone_world(world: World, new_world_id: str) -> World:
    """Copy a World's content onto a new identity (Ontology §8.3 step 1)."""

    clone = World(
        world_id=new_world_id,
        canonical_term=world.canonical_term,
        transliteration=world.transliteration,
        persian_term=world.persian_term,
        urdu_term=world.urdu_term,
        arabic_root=world.arabic_root,
        english_gloss=world.english_gloss,
        short_definition=world.short_definition,
        literal_meaning=world.literal_meaning,
        expanded_meaning=world.expanded_meaning,
        central_question=world.central_question,
        central_axis=world.central_axis,
        semantic_dimensions=dict(world.semantic_dimensions or {}),
        status=world.status,
        scope=world.scope,
        chapter_id=world.chapter_id,
        cluster_id=world.cluster_id,
        version_history=list(world.version_history or []),
        provenance=[dict(p) for p in (world.provenance or [])],
    )
    return clone
