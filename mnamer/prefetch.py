"""Background preparation of the next media target while the user chooses."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Iterator

from mnamer.exceptions import MnamerNetworkException, MnamerNotFoundException
from mnamer.metadata import Metadata
from mnamer.target import Target


@dataclass
class PreparedTarget:
    """A discovered target with its provider query already attempted."""

    target: Target
    matches: list[Metadata] = field(default_factory=list)
    not_found: bool = False
    network_error: bool = False


def prepare_target(target: Target) -> PreparedTarget:
    """Run provider query (and optional resolution probe) for a target."""
    prepared = PreparedTarget(target=target)
    try:
        prepared.matches = target.query()
    except MnamerNotFoundException:
        prepared.not_found = True
        prepared.matches = []
    except MnamerNetworkException:
        prepared.network_error = True
        prepared.matches = []
    if target.needs_resolution():
        target.ensure_resolution()
    return prepared


def _discover_and_prepare(targets: Iterator[Target]) -> PreparedTarget | None:
    try:
        target = next(targets)
    except StopIteration:
        return None
    return prepare_target(target)


class TargetLookahead:
    """
    One-file lookahead: while the user is prompted for the current file,
    discover and query the next one on a background thread.
    """

    def __init__(self, targets: Iterator[Target]):
        self._targets = targets
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="mnamer-prefetch"
        )
        self._future: Future[PreparedTarget | None] | None = None

    def __enter__(self) -> TargetLookahead:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        if self._future is not None:
            # Don't cancel mid-request; just wait so the session stays consistent.
            try:
                self._future.result()
            except Exception:
                pass
            self._future = None
        self._executor.shutdown(wait=True)

    def prime(self) -> PreparedTarget | None:
        """Synchronously prepare the first target, then start prefetching the next."""
        prepared = _discover_and_prepare(self._targets)
        if prepared is not None:
            self._schedule_prefetch()
        return prepared

    def take(self) -> PreparedTarget | None:
        """Return the next prepared target, waiting for prefetch if needed."""
        if self._future is None:
            return _discover_and_prepare(self._targets)
        prepared = self._future.result()
        self._future = None
        if prepared is not None:
            self._schedule_prefetch()
        return prepared

    def _schedule_prefetch(self) -> None:
        self._future = self._executor.submit(_discover_and_prepare, self._targets)
