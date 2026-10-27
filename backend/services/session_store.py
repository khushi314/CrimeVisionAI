"""
Disk-backed and in-memory SessionStore for forensic analysis persistence.
Implements Milestone 5 Activity 5.2 session serialization (`session_{uuid}.json`).
"""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from backend.config import SESSIONS_DIR
    from backend.utils.logger import setup_logger
except ImportError:
    from config import SESSIONS_DIR
    from utils.logger import setup_logger

logger = setup_logger("session_store")


class SessionStore:
    """Persists multimodal forensic context to JSON files on disk with in-memory caching."""

    def __init__(self, sessions_dir: Optional[Path] = None) -> None:
        self._sessions_dir = Path(sessions_dir or SESSIONS_DIR)
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self._store: Dict[str, Dict[str, Any]] = {}

    def create_session(self, data: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """Save forensic context to memory and `session_{id}.json` on disk."""
        sid = session_id or str(uuid.uuid4())
        entry = {
            "session_id": sid,
            "data": data,
            "timestamp": time.time(),
        }
        self._store[sid] = entry

        session_path = os.path.join(str(self._sessions_dir), f"session_{sid}.json")
        with open(session_path, "w", encoding="utf-8") as handle:
            json.dump(entry, handle, indent=2, ensure_ascii=False)

        logger.info("Persisted forensic session %s", sid)
        return sid

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve forensic context dictionary for `session_id`, loading from disk if needed."""
        if not session_id:
            return None

        if session_id in self._store:
            return self._store[session_id]["data"]

        # Sanitize ID before disk lookup
        safe_id = "".join(ch for ch in session_id if ch.isalnum() or ch in "-_")
        session_path = self._sessions_dir / f"session_{safe_id}.json"
        if not session_path.exists():
            return None

        try:
            with open(session_path, "r", encoding="utf-8") as handle:
                entry = json.load(handle)
            self._store[safe_id] = entry
            return entry.get("data")
        except Exception as exc:
            logger.error("Failed reading session %s: %s", safe_id, exc)
            return None

    def update_session(self, session_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        """Merge additional modality findings into an existing case session."""
        existing = self.get_session(session_id) or {}
        merged = {**existing, **patch}
        self.create_session(merged, session_id=session_id)
        return merged

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent persisted forensic sessions sorted newest-first."""
        records: List[Dict[str, Any]] = []
        for path in sorted(self._sessions_dir.glob("session_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            try:
                entry = json.loads(path.read_text(encoding="utf-8"))
                data = entry.get("data", {})
                records.append({
                    "session_id": entry.get("session_id", path.stem.replace("session_", "")),
                    "timestamp": entry.get("timestamp", path.stat().st_mtime),
                    "mode": data.get("mode", "unknown"),
                    "summary": data.get("visual_summary") or data.get("ai_summary") or "Forensic session",
                })
            except Exception:
                continue
        return records


session_store = SessionStore()
