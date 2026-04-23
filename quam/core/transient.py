from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Hashable

MISSING = object()


def _path_for(obj: Any, suffix: str | None = None) -> str:
    try:
        base = obj.get_reference()
    except Exception:
        base = obj.__class__.__name__

    if suffix is None:
        return base

    if base.endswith("/"):
        return f"{base}{suffix}"
    return f"{base}/{suffix}"


def _clear_parent(value: Any) -> None:
    if _is_quam_base(value):
        value.parent = None


def _restore_parent(parent: Any, value: Any) -> None:
    if _is_quam_base(value) and value.parent is None:
        value.parent = parent


def _is_quam_base(value: Any) -> bool:
    try:
        from quam.core.quam_classes import QuamBase
    except ImportError:
        return False

    return isinstance(value, QuamBase)


def _added_items(current: list[Any], snapshot: list[Any]) -> list[Any]:
    remaining = list(snapshot)
    added = []

    for item in current:
        for index, original in enumerate(remaining):
            if item is original:
                remaining.pop(index)
                break
        else:
            added.append(item)

    return added


@dataclass(slots=True)
class _AttrRecord:
    obj: Any
    attr: str
    original: Any

    def describe(self) -> dict[str, Any]:
        return {
            "path": _path_for(self.obj, self.attr),
            "original": self.original,
            "transient": getattr(self.obj, self.attr, MISSING),
        }

    def revert(self) -> None:
        current = getattr(self.obj, self.attr, MISSING)

        if self.original is MISSING:
            if current is not MISSING:
                _clear_parent(current)
                object.__delattr__(self.obj, self.attr)
            return

        if current is not MISSING and current is not self.original:
            _clear_parent(current)

        object.__setattr__(self.obj, self.attr, self.original)
        _restore_parent(self.obj, self.original)


@dataclass(slots=True)
class _DictRecord:
    obj: Any
    key: Any
    original: Any

    def describe(self) -> dict[str, Any]:
        return {
            "path": _path_for(self.obj, str(self.key)),
            "original": self.original,
            "transient": self.obj.data.get(self.key, MISSING),
        }

    def revert(self) -> None:
        current = self.obj.data.get(self.key, MISSING)

        if self.original is MISSING:
            if current is not MISSING:
                _clear_parent(current)
                del self.obj.data[self.key]
            return

        if current is not MISSING and current is not self.original:
            _clear_parent(current)

        self.obj.data[self.key] = self.original
        _restore_parent(self.obj, self.original)


@dataclass(slots=True)
class _ListRecord:
    obj: Any
    snapshot: list[Any]

    def describe(self) -> dict[str, Any]:
        return {
            "path": _path_for(self.obj),
            "original": list(self.snapshot),
            "transient": list(self.obj.data),
        }

    def revert(self) -> None:
        for item in _added_items(list(self.obj.data), self.snapshot):
            _clear_parent(item)

        self.obj.data[:] = self.snapshot
        for item in self.snapshot:
            _restore_parent(self.obj, item)


class TransientState:
    def __init__(self):
        self._is_recording = False
        self._records: list[tuple[tuple[int, Hashable], Any]] = []
        self._seen: set[tuple[int, Hashable]] = set()

    def record(self, record: Any, lookup_key: Hashable):
        token = (id(record.obj), lookup_key)
        if not self._is_recording or token in self._seen:
            return token

        self._seen.add(token)
        self._records.append((token, record))
        return token

    def remove(self, token: tuple[int, Hashable]) -> None:
        if token not in self._seen:
            return

        self._seen.remove(token)
        self._records = [
            (existing_token, record)
            for existing_token, record in self._records
            if existing_token != token
        ]

    def describe(self) -> list[dict[str, Any]]:
        return [record.describe() for _, record in self._records]

    def revert(self) -> None:
        self._is_recording = False
        try:
            for _, record in reversed(self._records):
                record.revert()
        finally:
            self._records.clear()
            self._seen.clear()
            self._is_recording = False
