"""Graph projection dispatch.

Ontology §12.4 and I-076: Neo4j is a projection of PostgreSQL, never a source
of truth. A projection failure is therefore a repairable inconsistency, not a
governance failure. Canonical approval must not become unavailable because the
graph is down, so projection errors are recorded for repair rather than raised.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable


@dataclass(frozen=True)
class ProjectionFailure:
    """A projection that did not complete, recorded for repair."""

    operation: str
    entity_type: str
    entity_id: str
    error: str
    at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


#: Failures awaiting repair. Compared against Neo4j on the next rebuild
#: (Ontology §12.5): PostgreSQL is always the correct side of a divergence.
_failures: list[ProjectionFailure] = []


def record_failure(
    operation: str, entity_type: str, entity_id: str, error: BaseException
) -> ProjectionFailure:
    failure = ProjectionFailure(
        operation=operation,
        entity_type=entity_type,
        entity_id=entity_id,
        error=f"{type(error).__name__}: {error}",
    )
    _failures.append(failure)
    return failure


def pending_failures() -> list[ProjectionFailure]:
    """Projection failures recorded since the last drain."""

    return list(_failures)


def clear_failures() -> None:
    _failures.clear()


def run_sync(coro: Awaitable[Any]) -> Any:
    """Run a coroutine from synchronous service code.

    Does not re-enter a running loop; delegates to a worker thread instead.
    """

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def project(
    operation: str,
    entity_type: str,
    entity_id: str,
    call: Callable[[], Awaitable[Any]],
) -> bool:
    """Attempt a projection, recording failure instead of raising.

    Returns ``True`` when the projection completed. A ``False`` return means the
    projection is pending repair; the PostgreSQL write that triggered it is
    still committed and still authoritative.
    """

    try:
        run_sync(call())
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see module docstring
        record_failure(operation, entity_type, entity_id, exc)
        return False
    return True
