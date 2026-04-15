#!/usr/bin/env python3
"""Local OpenCode watcher that synthesizes root-session offices.

Batch-one goals:
- discover local root sessions from opencode.db
- resolve sessionId -> rootSessionId -> officeId
- materialize synthetic office agents without touching agents-state.json
- expose overview/detail/mapping read models for route merging
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
import re
import sqlite3
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from runtime_lineage_resolver import build_office_identity, get_server_origin


DEFAULT_REFRESH_SECONDS = int(os.getenv("STAR_WATCHER_REFRESH_SECONDS", "5"))
STALE_AFTER_SECONDS = int(os.getenv("STAR_WATCHER_STALE_AFTER_SECONDS", "45"))
EXPIRE_AFTER_SECONDS = int(os.getenv("STAR_WATCHER_EXPIRE_AFTER_SECONDS", "900"))
WATCHER_ENABLED = os.getenv("STAR_OPENCODE_LOCAL_WATCHER", "1").strip().lower() not in {"0", "false", "no", "off"}
DB_ENV_KEYS = ("STAR_OPENCODE_DB_PATH", "OPENCODE_DB_PATH")
OPENCODE_SERVER_URL = (os.getenv("STAR_OPENCODE_SERVER_URL") or os.getenv("OPENCODE_SERVER_URL") or "http://127.0.0.1:4096").rstrip("/")
ENABLE_SSE = os.getenv("STAR_OPENCODE_ENABLE_SSE", "1").strip().lower() not in {"0", "false", "no", "off"}


def _discover_opencode_db_path() -> str | None:
    for key in DB_ENV_KEYS:
        value = (os.environ.get(key) or "").strip()
        if value and os.path.exists(value):
            return value
    candidate = os.path.join(os.path.expanduser("~"), ".local", "share", "opencode", "opencode.db")
    return candidate if os.path.exists(candidate) else None


def _sqlite_fetch_all(db_path: str, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _load_json_text(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return deepcopy(value)
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _millis_to_iso(value: Any) -> str | None:
    if value is None:
        return None
    try:
        raw = int(value)
        if raw <= 0:
            return None
        return datetime.fromtimestamp(raw / 1000).isoformat()
    except Exception:
        return None


def _parse_iso(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _coerce_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    return str(value)


def _normalize_state_from_events(events: list[dict[str, Any]]) -> str:
    if not events:
        return "idle"
    if any(evt.get("kind") == "error" for evt in events):
        return "error"
    if any(evt.get("kind") in {"thinking", "tool_call", "tool_result", "message"} for evt in events):
        return "executing"
    return "idle"


class OpenCodeLocalWatcher:
    def __init__(self):
        self.enabled = WATCHER_ENABLED
        self._lock = threading.Lock()
        self._overview_cache: dict[str, dict[str, Any]] = {}
        self._detail_cache: dict[str, dict[str, Any]] = {}
        self._mappings: dict[str, dict[str, Any]] = {}
        self._last_refresh_at: str | None = None
        self._source_mode: str = "db"
        self._last_sse_event_at: str | None = None
        self._last_sse_event_type: str | None = None
        self._sse_thread_started = False

    def _ensure_sse_thread(self, project_id: str | None = None):
        if not ENABLE_SSE or self._sse_thread_started:
            return
        self._sse_thread_started = True
        threading.Thread(target=self._sse_loop, args=(project_id,), daemon=True).start()

    def _resolve_event_session_id(self, payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None
        for key in ("sessionID", "sessionId"):
            if payload.get(key):
                return _coerce_text(payload.get(key), "").strip() or None
        for key in ("info", "message", "part", "properties"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                value = self._resolve_event_session_id(nested)
                if value:
                    return value
        return None

    def _sse_loop(self, project_id: str | None = None):
        path = "/event"
        if not project_id:
            path = "/global/event"
        url = f"{OPENCODE_SERVER_URL}{path}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                event_type = None
                data_lines: list[str] = []
                for raw in resp:
                    line = raw.decode("utf-8", "ignore").strip()
                    if not line:
                        if data_lines:
                            try:
                                payload = json.loads("\n".join(data_lines))
                            except Exception:
                                payload = {"raw": "\n".join(data_lines)}
                            session_id = self._resolve_event_session_id(payload)
                            if session_id or event_type in {"session.created", "session.updated", "session.deleted", "message.updated", "message.part.updated"}:
                                self._last_sse_event_at = datetime.now().isoformat()
                                self._last_sse_event_type = event_type
                                # Strategy: SSE is an incremental invalidation signal only; rebuild remains through official session/message or DB fallback.
                                self.refresh(project_id=project_id, directory=None)
                        event_type = None
                        data_lines = []
                        continue
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        data_lines.append(line.split(":", 1)[1].strip())
        except Exception:
            # silent fallback: DB/HTTP polling remains authoritative
            self._sse_thread_started = False

    def _http_get_json(self, path: str) -> Any:
        url = f"{OPENCODE_SERVER_URL}{path}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _query_via_server(self, project_id: str | None, directory: str | None) -> tuple[str | None, list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
        try:
            sessions_resp = self._http_get_json("/session")
            sessions = sessions_resp if isinstance(sessions_resp, list) else sessions_resp.get("items") or sessions_resp.get("sessions") or []
            if not isinstance(sessions, list):
                return None, [], {}, {}

            filtered = []
            for row in sessions:
                if not isinstance(row, dict):
                    continue
                if project_id and row.get("projectID") != project_id:
                    continue
                if (not project_id) and directory and row.get("directory") != directory:
                    continue
                filtered.append({
                    "id": row.get("id"),
                    "parent_id": row.get("parentID"),
                    "title": row.get("title"),
                    "project_id": row.get("projectID"),
                    "directory": row.get("directory"),
                    "time_created": None,
                    "time_updated": None,
                })

            by_session_messages: dict[str, list[dict[str, Any]]] = {}
            by_session_parts: dict[str, list[dict[str, Any]]] = {}
            for row in filtered:
                session_id = row.get("id")
                if not session_id:
                    continue
                msg_resp = self._http_get_json(f"/session/{urllib.parse.quote(str(session_id))}/message")
                messages = msg_resp if isinstance(msg_resp, list) else msg_resp.get("items") or msg_resp.get("messages") or []
                if not isinstance(messages, list):
                    messages = []
                normalized_messages = []
                normalized_parts = []
                for msg in messages:
                    if not isinstance(msg, dict):
                        continue
                    normalized_messages.append({
                        "id": msg.get("id"),
                        "session_id": session_id,
                        "time_created": None,
                        "time_updated": None,
                        "data": msg,
                    })
                    for part in msg.get("parts") or []:
                        if not isinstance(part, dict):
                            continue
                        normalized_parts.append({
                            "id": part.get("id"),
                            "message_id": msg.get("id"),
                            "session_id": session_id,
                            "time_created": None,
                            "time_updated": None,
                            "data": part,
                        })
                by_session_messages[session_id] = normalized_messages
                by_session_parts[session_id] = normalized_parts

            self._source_mode = "server"
            return OPENCODE_SERVER_URL, filtered, by_session_messages, by_session_parts
        except Exception:
            return None, [], {}, {}

    def _query_sessions(self, project_id: str | None, directory: str | None) -> tuple[str | None, list[dict[str, Any]]]:
        db_path = _discover_opencode_db_path()
        if not db_path:
            return None, []

        if project_id:
            rows = _sqlite_fetch_all(
                db_path,
                "SELECT id, parent_id, title, project_id, directory, time_created, time_updated FROM session WHERE project_id = ? ORDER BY time_updated DESC",
                (project_id,),
            )
        elif directory:
            rows = _sqlite_fetch_all(
                db_path,
                "SELECT id, parent_id, title, project_id, directory, time_created, time_updated FROM session WHERE directory = ? ORDER BY time_updated DESC",
                (directory,),
            )
        else:
            rows = _sqlite_fetch_all(
                db_path,
                "SELECT id, parent_id, title, project_id, directory, time_created, time_updated FROM session ORDER BY time_updated DESC LIMIT 100",
            )
        return db_path, rows

    def _build_root_index(self, sessions: list[dict[str, Any]]) -> dict[str, str]:
        by_id = {row["id"]: row for row in sessions if row.get("id")}

        def resolve_root(session_id: str) -> str:
            cur = by_id.get(session_id)
            seen = set()
            while cur and cur.get("parent_id") and cur.get("parent_id") in by_id and cur.get("parent_id") not in seen:
                seen.add(cur["id"])
                cur = by_id.get(cur.get("parent_id"))
            return cur["id"] if cur and cur.get("id") else session_id

        return {session_id: resolve_root(session_id) for session_id in by_id.keys()}

    def _query_messages_and_parts(self, db_path: str, session_ids: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not session_ids:
            return [], []
        placeholders = ",".join("?" for _ in session_ids)
        messages = _sqlite_fetch_all(
            db_path,
            f"SELECT id, session_id, time_created, time_updated, data FROM message WHERE session_id IN ({placeholders}) ORDER BY time_created ASC",
            tuple(session_ids),
        )
        parts = _sqlite_fetch_all(
            db_path,
            f"SELECT id, message_id, session_id, time_created, time_updated, data FROM part WHERE session_id IN ({placeholders}) ORDER BY time_created ASC",
            tuple(session_ids),
        )
        return messages, parts

    def _materialize(self, project_id: str | None, directory: str | None):
        server_path, sessions, server_messages, server_parts = self._query_via_server(project_id, directory)
        if server_path and sessions:
            db_path = server_path
        else:
            db_path, sessions = self._query_sessions(project_id, directory)
            server_messages = {}
            server_parts = {}
            self._source_mode = "db"
        if not db_path or not sessions:
            return {}, {}, {}

        root_index = self._build_root_index(sessions)
        by_root: dict[str, list[dict[str, Any]]] = {}
        for row in sessions:
            root_id = _coerce_text(root_index.get(row["id"], row["id"]), "").strip()
            if not root_id:
                continue
            by_root.setdefault(root_id, []).append(row)

        all_session_ids = [row["id"] for row in sessions if row.get("id")]
        if server_messages or server_parts:
            messages_by_session = server_messages
            parts_by_session = server_parts
        else:
            messages, parts = self._query_messages_and_parts(db_path, all_session_ids)
            messages_by_session: dict[str, list[dict[str, Any]]] = {}
            for row in messages:
                messages_by_session.setdefault(row.get("session_id") or "", []).append(row)
            parts_by_session: dict[str, list[dict[str, Any]]] = {}
            for row in parts:
                parts_by_session.setdefault(row.get("session_id") or "", []).append(row)

        overview: dict[str, dict[str, Any]] = {}
        detail: dict[str, dict[str, Any]] = {}
        mappings: dict[str, dict[str, Any]] = {}

        now = datetime.now(timezone.utc)

        for root_id, family_sessions in by_root.items():
            family_sessions_sorted = sorted(family_sessions, key=lambda row: row.get("time_updated") or 0, reverse=True)
            root_row = next((row for row in family_sessions if row.get("id") == root_id), family_sessions_sorted[0])
            child_ids = [row["id"] for row in family_sessions if row.get("parent_id") == root_id and row.get("id")]
            family_session_ids = [row["id"] for row in family_sessions if row.get("id")]

            events: list[dict[str, Any]] = []
            thinking: list[dict[str, Any]] = []
            messages_out: list[dict[str, Any]] = []
            tools: list[dict[str, Any]] = []
            delegated_ids: list[str] = []
            background_task_ids: list[str] = []

            for session_id in family_session_ids:
                for msg in messages_by_session.get(session_id, []):
                    msg_data = _load_json_text(msg.get("data")) if not server_messages else deepcopy(msg.get("data") or {})
                    role = _coerce_text(msg_data.get("role"), "")
                    msg_ts = _millis_to_iso(msg.get("time_created"))
                    if role:
                        events.append({
                            "kind": "status",
                            "title": f"{role} message",
                            "text": _coerce_text(msg_data.get("agent") or msg_data.get("mode") or role),
                            "createdAt": msg_ts,
                            "meta": {"sessionId": session_id, "messageId": msg.get("id"), "role": role},
                        })

                for part in parts_by_session.get(session_id, []):
                    payload = _load_json_text(part.get("data")) if not server_parts else deepcopy(part.get("data") or {})
                    part_type = _coerce_text(payload.get("type"), "message").lower().strip()
                    part_ts = _millis_to_iso(part.get("time_created"))
                    meta = {"sessionId": session_id, "partId": part.get("id")}
                    if part_type == "reasoning":
                        item = {"kind": "thinking", "title": "思考片段", "text": _coerce_text(payload.get("text")), "createdAt": part_ts, "meta": meta}
                        thinking.append(item)
                        events.append(item)
                    elif part_type == "text":
                        item = {"kind": "message", "title": "文本输出", "text": _coerce_text(payload.get("text")), "createdAt": part_ts, "meta": meta}
                        messages_out.append(item)
                        events.append(item)
                    elif part_type == "tool":
                        state = payload.get("state") or {}
                        tool_name = _coerce_text(payload.get("tool"), "tool")
                        metadata = deepcopy((state or {}).get("metadata") or {})
                        delegated_session_id = _coerce_text(metadata.get("sessionId") or metadata.get("session_id"), "").strip()
                        if delegated_session_id and delegated_session_id not in delegated_ids:
                            delegated_ids.append(delegated_session_id)
                        output_payload = _coerce_text((state or {}).get("output"), "")
                        for token in re.findall(r"bg_[a-zA-Z0-9]+", output_payload or ""):
                            if token not in background_task_ids:
                                background_task_ids.append(token)
                        call_item = {
                            "kind": "tool_call",
                            "title": f"工具调用 · {tool_name}",
                            "text": json.dumps(deepcopy((state or {}).get("input") or {}), ensure_ascii=False, indent=2),
                            "createdAt": part_ts,
                            "meta": {**meta, **metadata, "toolName": tool_name},
                        }
                        result_item = {
                            "kind": "tool_result",
                            "title": f"工具结果 · {tool_name}",
                            "text": output_payload or _coerce_text((state or {}).get("status"), "工具执行完成"),
                            "createdAt": part_ts,
                            "meta": {**meta, **metadata, "toolName": tool_name},
                        }
                        tools.extend([call_item, result_item])
                        events.extend([call_item, result_item])

            updated_at = _millis_to_iso(root_row.get("time_updated"))
            updated_dt = _parse_iso(updated_at) if updated_at else None
            age_seconds = (now - updated_dt.astimezone(timezone.utc)).total_seconds() if updated_dt and updated_dt.tzinfo else ((now.replace(tzinfo=None) - updated_dt).total_seconds() if updated_dt else None)

            if age_seconds is None:
                presence = "idle"
            elif age_seconds > EXPIRE_AFTER_SECONDS:
                continue
            elif age_seconds > STALE_AFTER_SECONDS:
                presence = "offline"
            else:
                presence = _normalize_state_from_events(events)

            # fallback correction: if latest visible event is newer than summary update, prefer active/done over stale running assumptions
            latest_event_dt = None
            for evt in events:
                evt_dt = _parse_iso(_coerce_text(evt.get("createdAt"), ""))
                if evt_dt and (latest_event_dt is None or evt_dt > latest_event_dt):
                    latest_event_dt = evt_dt
            if presence == "offline" and latest_event_dt and updated_dt and latest_event_dt >= updated_dt:
                presence = _normalize_state_from_events(events)

            synthetic_id = f"local:{root_id}"
            display_name = _coerce_text(root_row.get("title"), "").strip() or f"OpenCode {root_id[:8]}"
            headline = display_name
            detail_text = messages_out[-1]["text"] if messages_out else _coerce_text(root_row.get("title"), "")
            child_run_ids = [session_id for session_id in child_ids if session_id]
            delegated_run_ids = [sid for sid in delegated_ids if sid]

            office_identity = build_office_identity(root_id, get_server_origin())
            summary = {
                "agentId": synthetic_id,
                "agentName": display_name,
                "runId": root_id,
                "status": presence,
                "phase": presence,
                "headline": headline,
                "detail": detail_text,
                "updatedAt": updated_at,
                "source": {
                    "provider": "opencode-local-watcher",
                    "sessionId": root_id,
                    "backgroundTaskId": background_task_ids[0] if background_task_ids else None,
                },
                "selectionKey": synthetic_id,
                "identityType": "synthetic",
                "synthetic": True,
                "serverOrigin": office_identity.get("serverOrigin"),
                "rootSessionId": root_id,
                "officeLocalId": office_identity.get("officeLocalId"),
                "officeId": office_identity.get("officeId"),
                "officeRole": "root",
                "lineageDepth": 0,
                "lineageConfidence": "resolved",
                "discoverySource": "watcher_db",
            }
            overview[synthetic_id] = summary

            edges = [
                {"fromRunId": root_id, "toRunId": child_id, "kind": "child", "label": "子会话"}
                for child_id in child_run_ids
            ]
            edges.extend(
                {"fromRunId": root_id, "toRunId": delegated_id, "kind": "delegated", "label": "委派"}
                for delegated_id in delegated_run_ids
            )
            if background_task_ids:
                edges.append({"fromRunId": root_id, "toRunId": background_task_ids[0], "kind": "background_task", "label": "后台任务"})

            detail_payload = {
                "runId": root_id,
                "agentId": synthetic_id,
                "agentName": display_name,
                "status": presence,
                "summary": summary,
                "session": {"sessionId": root_id, "childSessionIds": child_run_ids},
                "backgroundTask": {"taskId": background_task_ids[0] if background_task_ids else None, "status": None},
                "edges": edges,
                "events": events,
                "raw": {
                    "rootSession": deepcopy(root_row),
                    "familySessions": deepcopy(family_sessions_sorted),
                        "opencode": {
                            "dbPath": db_path,
                            "sourceMode": self._source_mode,
                            "rootSessionId": root_id,
                            "childSessionIds": child_run_ids,
                            "delegatedSessionIds": delegated_run_ids,
                    },
                },
                "identityType": "synthetic",
                "synthetic": True,
                "serverOrigin": office_identity.get("serverOrigin"),
                "rootSessionId": root_id,
                "officeLocalId": office_identity.get("officeLocalId"),
                "officeId": office_identity.get("officeId"),
                "officeRole": "root",
                "lineageDepth": 0,
                "lineageConfidence": "resolved",
            }
            detail[synthetic_id] = detail_payload
            detail[root_id] = detail_payload

            mappings[synthetic_id] = {
                "agentId": synthetic_id,
                "runId": root_id,
                "sessionId": root_id,
                "serverOrigin": office_identity.get("serverOrigin"),
                "rootSessionId": root_id,
                "syntheticAgentId": synthetic_id,
                "officeLocalId": office_identity.get("officeLocalId"),
                "officeId": office_identity.get("officeId"),
                "backgroundTaskId": background_task_ids[0] if background_task_ids else None,
                "selectionKey": synthetic_id,
            }
            mappings[root_id] = deepcopy(mappings[synthetic_id])
            for session_id in family_session_ids:
                mappings[session_id] = deepcopy(mappings[synthetic_id])

        return overview, detail, mappings

    def refresh(self, project_id: str | None = None, directory: str | None = None):
        if not self.enabled:
            return
        self._ensure_sse_thread(project_id)
        overview, detail, mappings = self._materialize(project_id, directory)
        with self._lock:
            self._overview_cache = overview
            self._detail_cache = detail
            self._mappings = mappings
            self._last_refresh_at = datetime.now().isoformat()

    def get_overview(self, project_id: str | None = None, directory: str | None = None) -> list[dict[str, Any]]:
        self.refresh(project_id, directory)
        with self._lock:
            return [deepcopy(item) for item in self._overview_cache.values()]

    def get_detail(self, identifier: str, project_id: str | None = None, directory: str | None = None) -> dict[str, Any] | None:
        self.refresh(project_id, directory)
        with self._lock:
            if identifier in self._detail_cache:
                return deepcopy(self._detail_cache[identifier])
            mapped = self._mappings.get(identifier)
            synthetic_agent_id = _coerce_text((mapped or {}).get("syntheticAgentId"), "").strip() if isinstance(mapped, dict) else ""
            if synthetic_agent_id and synthetic_agent_id in self._detail_cache:
                return deepcopy(self._detail_cache[synthetic_agent_id])
            return None

    def get_mappings(self, project_id: str | None = None, directory: str | None = None) -> dict[str, Any]:
        self.refresh(project_id, directory)
        with self._lock:
            return {
                "enabled": self.enabled,
                "lastRefreshAt": self._last_refresh_at,
                "lastSseEventAt": self._last_sse_event_at,
                "lastSseEventType": self._last_sse_event_type,
                "syntheticCount": len(self._overview_cache),
                "sourceMode": self._source_mode,
                "items": deepcopy(self._mappings),
            }


_WATCHER_INSTANCE: OpenCodeLocalWatcher | None = None


def get_local_watcher() -> OpenCodeLocalWatcher:
    global _WATCHER_INSTANCE
    if _WATCHER_INSTANCE is None:
        _WATCHER_INSTANCE = OpenCodeLocalWatcher()
    return _WATCHER_INSTANCE
