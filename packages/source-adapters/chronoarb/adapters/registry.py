from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceMetadata:
    source_key: str
    adapter_version: str
    access_mode: str
    approval_ref: str | None
    rate_limit_per_minute: int | None = None


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, object] = {}
        self._metadata: dict[str, SourceMetadata] = {}

    def register(
        self,
        metadata: SourceMetadata,
        adapter: object,
    ) -> None:
        if metadata.source_key in self._sources:
            raise ValueError(f"Source already registered: {metadata.source_key}")
        self._sources[metadata.source_key] = adapter
        self._metadata[metadata.source_key] = metadata

    def get(self, source_key: str) -> object:
        try:
            return self._sources[source_key]
        except KeyError:
            raise KeyError(f"Unknown source: {source_key}") from None

    def metadata(self, source_key: str) -> SourceMetadata:
        try:
            return self._metadata[source_key]
        except KeyError:
            raise KeyError(f"Unknown source: {source_key}") from None
