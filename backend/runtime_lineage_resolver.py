#!/usr/bin/env python3
"""Canonical runtime lineage helpers."""

from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
import json
import os
import sqlite3
from typing import Any
from urllib.parse import urlparse


DB_ENV_KEYS = ("STAR_OPENCODE_DB_PATH", "OPENCODE_DB_PATH")


def discover_opencode_db_path() -> str | None:
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


def _coerce_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    return str(value)


def get_server_origin() -> str:
    explicit = (os.environ.get("STAR_OPENCODE_SERVER_ORIGIN") or "").strip()
    if explicit:
        return explicit
    raw_url = (os.environ.get("STAR_OPENCODE_SERVER_URL") or os.environ.get("OPENCODE_SERVER_URL") or "").strip()
    if not raw_url:
        return "local.default"
    try:
        parsed = urlparse(raw_url)
        if parsed.netloc:
            return parsed.netloc.lower()
        return raw_url.rstrip("/").lower() or "local.default"
    except Exception:
        return raw_url.rstrip("/").lower() or "local.default"


def build_office_identity(root_session_id: str | None, server_origin: str | None = None) -> dict[str, Any]:
    root = (root_session_id or "").strip() or None
    origin = (server_origin or get_server_origin()).strip() or "local.default"
    return {
        "serverOrigin": origin,
        "rootSessionId": root,
        "officeLocalId": root,
        "officeId": f"{origin}:{root}" if root else None,
    }


def _all_sessions(db_path: str) -> list[dict[str, Any]]:
    return _sqlite_fetch_all(
        db_path,
        "SELECT id, parent_id, title, project_id, directory, time_created, time_updated FROM session ORDER BY time_updated DESC",
    )


def resolve_runtime_lineage(runtime: dict[str, Any] | None, db_path: str | None = None, server_origin: str | None = None) -> dict[str, Any]:
    runtime = deepcopy(runtime or {})
    origin = (server_origin or runtime.get("serverOrigin") or runtime.get("serverOriginHint") or get_server_origin()).strip() or "local.default"
    session_id = _coerce_text(runtime.get("sessionId"), "").strip() or None
    parent_run_id = _coerce_text(runtime.get("parentRunId"), "").strip() or None
    root_hint = _coerce_text(runtime.get("rootSessionId"), "").strip() or _coerce_text(runtime.get("rootSessionIdHint"), "").strip() or None
    office_local_hint = _coerce_text(runtime.get("officeLocalId"), "").strip() or _coerce_text(runtime.get("officeLocalIdHint"), "").strip() or None
    office_hint = _coerce_text(runtime.get("officeId"), "").strip() or _coerce_text(runtime.get("officeIdHint"), "").strip() or None
    anchor_id = session_id or parent_run_id or root_hint or office_local_hint or (office_hint.split(":", 1)[1] if office_hint and ":" in office_hint else office_hint)
    root_session_id = None
    lineage_path: list[str] = []
    family_session_ids: list[str] = []
    child_session_ids: list[str] = []
    descendant_session_ids: list[str] = []
    lineage_confidence = "unresolved"
    lineage_source = "none"

    resolved_db_path = db_path or discover_opencode_db_path()
    if resolved_db_path and anchor_id:
        try:
            sessions = _all_sessions(resolved_db_path)
        except Exception:
            sessions = []
        if sessions:
            by_id = {row["id"]: row for row in sessions if row.get("id")}
            children_by_parent: dict[str, list[str]] = defaultdict(list)
            for row in sessions:
                parent_id = _coerce_text(row.get("parent_id"), "").strip()
                child_id = _coerce_text(row.get("id"), "").strip()
                if parent_id and child_id:
                    children_by_parent[parent_id].append(child_id)

            cur = anchor_id if anchor_id in by_id else None
            reversed_path: list[str] = []
            seen_up: set[str] = set()
            while cur and cur in by_id and cur not in seen_up:
                reversed_path.append(cur)
                seen_up.add(cur)
                parent_id = _coerce_text(by_id[cur].get("parent_id"), "").strip() or None
                if not parent_id:
                    break
                cur = parent_id

            if reversed_path:
                root_session_id = reversed_path[-1]
                lineage_path = list(reversed(reversed_path))
                queue = deque([root_session_id])
                seen_down = {root_session_id}
                while queue:
                    current = queue.popleft()
                    family_session_ids.append(current)
                    for child_id in children_by_parent.get(current, []):
                        if child_id in seen_down:
                            continue
                        seen_down.add(child_id)
                        queue.append(child_id)
                child_session_ids = list(children_by_parent.get(anchor_id or root_session_id, []))
                descendant_session_ids = [sid for sid in family_session_ids if sid != (anchor_id or root_session_id)]
                lineage_confidence = "resolved"
                lineage_source = "session-parent-chain"

    if not root_session_id and root_hint:
        root_session_id = root_hint
        lineage_path = [sid for sid in ([root_hint] if anchor_id in {None, root_hint} else [root_hint, anchor_id]) if sid]
        lineage_confidence = "provisional"
        lineage_source = "root-hint"
    elif not root_session_id and office_local_hint:
        root_session_id = office_local_hint
        lineage_path = [sid for sid in ([office_local_hint] if anchor_id in {None, office_local_hint} else [office_local_hint, anchor_id]) if sid]
        lineage_confidence = "provisional"
        lineage_source = "office-local-hint"
    elif not root_session_id and office_hint:
        local_part = office_hint.split(":", 1)[1] if ":" in office_hint else office_hint
        local_part = local_part.strip() or None
        if local_part:
            root_session_id = local_part
            lineage_path = [sid for sid in ([local_part] if anchor_id in {None, local_part} else [local_part, anchor_id]) if sid]
            lineage_confidence = "provisional"
            lineage_source = "office-hint"

    office = build_office_identity(root_session_id, origin)
    current_session_id = session_id or anchor_id
    lineage_depth = None
    if current_session_id and lineage_path and current_session_id in lineage_path:
        lineage_depth = lineage_path.index(current_session_id)
    elif current_session_id and root_session_id and current_session_id == root_session_id:
        lineage_depth = 0

    ancestors = []
    if current_session_id and lineage_path and current_session_id in lineage_path:
        ancestors = [sid for sid in lineage_path if sid != current_session_id]

    office_role = "unresolved"
    if root_session_id:
        office_role = "root" if current_session_id in {None, root_session_id} else "descendant"

    return {
        **office,
        "sessionId": current_session_id,
        "parentRunId": parent_run_id,
        "lineagePath": lineage_path,
        "ancestorSessionIds": ancestors,
        "lineageDepth": lineage_depth,
        "lineageConfidence": lineage_confidence,
        "lineageSource": lineage_source,
        "officeRole": office_role,
        "familySessionIds": family_session_ids,
        "childSessionIds": child_session_ids,
        "descendantSessionIds": descendant_session_ids,
    }


def query_session_family(session_id: str | None, db_path: str | None = None, server_origin: str | None = None) -> dict[str, Any] | None:
    anchor = _coerce_text(session_id, "").strip()
    if not anchor:
        return None
    resolved_db_path = db_path or discover_opencode_db_path()
    if not resolved_db_path:
        return None
    lineage = resolve_runtime_lineage({"sessionId": anchor}, resolved_db_path, server_origin)
    family_ids = list(lineage.get("familySessionIds") or [])
    root_session_id = lineage.get("rootSessionId")
    if not family_ids or not root_session_id:
        return None

    sessions = _all_sessions(resolved_db_path)
    by_id = {row["id"]: row for row in sessions if row.get("id")}
    family_sessions = [deepcopy(by_id[sid]) for sid in family_ids if sid in by_id]
    if not family_sessions:
        return None

    placeholders = ",".join("?" for _ in family_ids)
    messages = _sqlite_fetch_all(
        resolved_db_path,
        f"SELECT id, session_id, time_created, time_updated, data FROM message WHERE session_id IN ({placeholders}) ORDER BY time_created ASC",
        tuple(family_ids),
    ) if family_ids else []
    parts = _sqlite_fetch_all(
        resolved_db_path,
        f"SELECT id, message_id, session_id, time_created, time_updated, data FROM part WHERE session_id IN ({placeholders}) ORDER BY time_created ASC",
        tuple(family_ids),
    ) if family_ids else []

    message_map: dict[str, dict[str, Any]] = {}
    for row in messages:
        payload = row.get("data")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        elif not isinstance(payload, dict):
            payload = {}
        message_map[row["id"]] = {
            "id": row["id"],
            "session_id": row.get("session_id"),
            "time_created": row.get("time_created"),
            "time_updated": row.get("time_updated"),
            "data": deepcopy(payload),
            "parts": [],
        }

    for row in parts:
        message_id = row.get("message_id")
        if not message_id or message_id not in message_map:
            continue
        payload = row.get("data")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        elif not isinstance(payload, dict):
            payload = {}
        message_map[message_id]["parts"].append({
            "id": row.get("id"),
            "session_id": row.get("session_id"),
            "time_created": row.get("time_created"),
            "time_updated": row.get("time_updated"),
            "data": deepcopy(payload),
        })

    return {
        "db_path": resolved_db_path,
        "serverOrigin": lineage.get("serverOrigin"),
        "rootSessionId": root_session_id,
        "subjectSessionId": anchor,
        "lineage": lineage,
        "sessions": family_sessions,
        "messages": list(message_map.values()),
    }
