"""Prompt history: finished request traces, appended to a local JSON-lines file.

A file lets the command line and the service share one history. It holds users' questions, so it
lives in an ignored local folder and is read only by the admin routes. Reads take the newest
`max_entries` records within the retention period; older lines are dropped when the file is
compacted. Storage problems are logged and never fail the request being recorded.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptStore:
    def __init__(self, path: Path, max_entries: int, retention_days: int):
        self.path = path
        self.max_entries = max_entries
        self.retention_days = retention_days
        self._lock = threading.Lock()

    def append(self, record: dict) -> None:
        try:
            line = json.dumps(record, ensure_ascii=False, default=str)
            with self._lock:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as file:
                    file.write(line + "\n")
                self._compact_if_needed()
        except OSError:
            logger.exception("prompt history could not be written")

    def records(self) -> list[dict]:
        """Newest first, within the retention period and the entry limit."""
        try:
            with self._lock:
                lines = self.path.read_text(encoding="utf-8").splitlines() if self.path.exists() else []
        except OSError:
            logger.exception("prompt history could not be read")
            return []
        cutoff = time.time() - self.retention_days * 86400
        records = []
        for line in reversed(lines):
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("started", 0) >= cutoff:
                records.append(record)
            if len(records) >= self.max_entries:
                break
        return records

    def find(self, request_id: str) -> dict | None:
        return next((record for record in self.records() if record.get("id") == request_id), None)

    def _compact_if_needed(self) -> None:
        # Rewrite the file once it holds twice the limit, so it never grows without bound.
        lines = self.path.read_text(encoding="utf-8").splitlines()
        if len(lines) > 2 * self.max_entries:
            self.path.write_text("\n".join(lines[-self.max_entries :]) + "\n", encoding="utf-8")
