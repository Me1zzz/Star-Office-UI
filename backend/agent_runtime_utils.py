#!/usr/bin/env python3
"""Runtime aggregation helpers for Star Office UI.

This module normalizes current office state plus optional upstream runtime metadata
into a frontend-friendly runtime model.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
import re
import sqlite3
from typing import Any


RUNTIME_STATUS_ORDER = {"error": 5, "running": 4, "waiting": 3, "idle": 2, "done": 1, "offline": 0}

OPENCODE_DB_ENV_KEYS = ("STAR_OPENCODE_DB_PATH", "OPENCODE_DB_PATH")
_RUNTIME_INDEX_CACHE: dict[str, dict[str, Any]] = {}


def _discover_opencode_db_path() -> str | None:
    for key in OPENCODE_DB_ENV_KEYS:
        value = (os.environ.get(key) or "").strip()
        if value and os.path.exists(value):
            return value

    candidates = [
        os.path.join(os.path.expanduser("~"), ".local", "share", "opencode", "opencode.db"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


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


def _query_session_tree(session_id: str) -> dict[str, Any] | None:
    db_path = _discover_opencode_db_path()
    if not db_path or not session_id:
        return None

    sessions = _sqlite_fetch_all(
        db_path,
        "SELECT id, parent_id, title, project_id, directory, time_created, time_updated FROM session WHERE id = ? OR parent_id = ? ORDER BY time_updated DESC",
        (session_id, session_id),
    )
    if not sessions:
        return None

    session_ids = [row["id"] for row in sessions if row.get("id")]
    placeholders = ",".join("?" for _ in session_ids)
    messages = _sqlite_fetch_all(
        db_path,
        f"SELECT id, session_id, time_created, time_updated, data FROM message WHERE session_id IN ({placeholders}) ORDER BY time_created ASC",
        tuple(session_ids),
    ) if session_ids else []
    parts = _sqlite_fetch_all(
        db_path,
        f"SELECT id, message_id, session_id, time_created, time_updated, data FROM part WHERE session_id IN ({placeholders}) ORDER BY time_created ASC",
        tuple(session_ids),
    ) if session_ids else []

    message_map: dict[str, dict[str, Any]] = {}
    for row in messages:
        data = _load_json_text(row.get("data"))
        message_map[row["id"]] = {
            "id": row["id"],
            "session_id": row.get("session_id"),
            "time_created": row.get("time_created"),
            "time_updated": row.get("time_updated"),
            "data": data,
            "parts": [],
        }

    for row in parts:
        message_id = row.get("message_id")
        if not message_id or message_id not in message_map:
            continue
        message_map[message_id]["parts"].append({
            "id": row.get("id"),
            "session_id": row.get("session_id"),
            "time_created": row.get("time_created"),
            "time_updated": row.get("time_updated"),
            "data": _load_json_text(row.get("data")),
        })

    return {
        "db_path": db_path,
        "sessions": sessions,
        "messages": list(message_map.values()),
    }


def _extract_session_runtime(session_tree: dict[str, Any], root_session_id: str) -> dict[str, Any]:
    sessions = session_tree.get("sessions") or []
    messages = session_tree.get("messages") or []
    root = next((row for row in sessions if row.get("id") == root_session_id), None)
    child_session_ids = [row.get("id") for row in sessions if row.get("parent_id") == root_session_id and row.get("id")]
    edges = [
        {
            "fromRunId": root_session_id,
            "toRunId": child_id,
            "kind": "child",
            "label": "子会话",
        }
        for child_id in child_session_ids
    ]

    events: list[dict[str, Any]] = []
    thinking: list[dict[str, Any]] = []
    text_messages: list[dict[str, Any]] = []
    tools: list[dict[str, Any]] = []
    delegated_run_ids: list[str] = []
    background_task_ids: list[str] = []

    for message in messages:
        message_data = message.get("data") or {}
        message_role = _coerce_text(message_data.get("role"), "")
        message_time = _millis_to_iso(message.get("time_created") or message_data.get("time", {}).get("created"))
        if message_role:
            events.append({
                "kind": "status",
                "title": f"{message_role} message",
                "text": _coerce_text(message_data.get("mode") or message_data.get("agent") or message_data.get("role")),
                "createdAt": message_time,
                "meta": {
                    "messageId": message.get("id"),
                    "sessionId": message.get("session_id"),
                    "role": message_role,
                },
            })

        for part in message.get("parts") or []:
            payload = part.get("data") or {}
            part_type = _coerce_text(payload.get("type"), "message").lower().strip()
            created_at = _millis_to_iso(part.get("time_created")) or _event_timestamp(payload, message_time)
            base_meta = {
                "messageId": message.get("id"),
                "partId": part.get("id"),
                "sessionId": part.get("session_id") or message.get("session_id"),
            }

            if part_type == "reasoning":
                item = {
                    "kind": "thinking",
                    "title": "思考片段",
                    "text": _coerce_text(payload.get("text")),
                    "createdAt": created_at,
                    "meta": deepcopy(base_meta),
                }
                thinking.append(item)
                events.append(item)
            elif part_type == "text":
                item = {
                    "kind": "message",
                    "title": "文本输出",
                    "text": _coerce_text(payload.get("text")),
                    "createdAt": created_at,
                    "meta": deepcopy(base_meta),
                }
                text_messages.append(item)
                events.append(item)
            elif part_type == "tool":
                state = payload.get("state") or {}
                status = _coerce_text((state or {}).get("status"), "")
                tool_name = _coerce_text(payload.get("tool"), "tool")
                input_payload = deepcopy((state or {}).get("input") or {})
                output_payload = _coerce_text((state or {}).get("output"), "")
                metadata_payload = deepcopy((state or {}).get("metadata") or {})
                call_event = {
                    "kind": "tool_call",
                    "title": f"工具调用 · {tool_name}",
                    "text": json.dumps(input_payload, ensure_ascii=False, indent=2) if input_payload else tool_name,
                    "createdAt": created_at,
                    "meta": {**deepcopy(base_meta), "toolName": tool_name, "status": status, **metadata_payload},
                }
                tools.append(call_event)
                events.append(call_event)

                delegated_session_id = _coerce_text(metadata_payload.get("sessionId") or metadata_payload.get("session_id"), "").strip()
                if delegated_session_id and delegated_session_id not in delegated_run_ids:
                    delegated_run_ids.append(delegated_session_id)

                for match in re.findall(r"bg_[a-zA-Z0-9]+", output_payload or ""):
                    if match not in background_task_ids:
                        background_task_ids.append(match)

                if output_payload or status:
                    result_event = {
                        "kind": "tool_result",
                        "title": f"工具结果 · {tool_name}",
                        "text": output_payload or status or "工具执行完成",
                        "createdAt": created_at,
                        "meta": {**deepcopy(base_meta), "toolName": tool_name, "status": status, **metadata_payload},
                    }
                    tools.append(result_event)
                    events.append(result_event)

                if tool_name in {"call_omo_agent", "task"} and delegated_session_id:
                    edges.append({
                        "fromRunId": root_session_id,
                        "toRunId": delegated_session_id,
                        "kind": "delegated",
                        "label": f"{tool_name} 委派",
                    })

    title = _coerce_text((root or {}).get("title"), root_session_id)
    updated_at = _millis_to_iso((root or {}).get("time_updated"))
    headline = title or (text_messages[0]["text"] if text_messages else root_session_id)
    detail = text_messages[0]["text"] if text_messages else title
    return {
        "runId": root_session_id,
        "sessionId": root_session_id,
        "childSessionIds": child_session_ids,
        "headline": headline,
        "detail": detail,
        "summary": title,
        "updatedAt": updated_at,
        "provider": "opencode",
        "events": events,
        "thinking": thinking,
        "messages": text_messages,
        "tools": tools,
        "delegatedRunIds": delegated_run_ids or child_session_ids,
        "childRunIds": child_session_ids,
        "backgroundTaskId": background_task_ids[0] if background_task_ids else None,
        "opencode": {
            "sessions": sessions,
            "messageCount": len(messages),
            "dbPath": session_tree.get("db_path"),
        },
        "edges": edges,
    }


def _merge_omo_runtime(runtime: dict[str, Any]) -> dict[str, Any]:
    omo = deepcopy(runtime.get("omo") or {}) if isinstance(runtime.get("omo"), dict) else {}
    if not omo:
        return runtime

    merged = deepcopy(runtime)
    background_output = omo.get("backgroundOutput") or {}
    session_read = omo.get("sessionRead") or {}
    session_info = omo.get("sessionInfo") or {}

    if omo.get("backgroundTaskId") and not merged.get("backgroundTaskId"):
        merged["backgroundTaskId"] = omo.get("backgroundTaskId")
    if omo.get("backgroundTaskStatus") and not merged.get("backgroundTaskStatus"):
        merged["backgroundTaskStatus"] = omo.get("backgroundTaskStatus")
    if session_info.get("sessionId") and not merged.get("sessionId"):
        merged["sessionId"] = session_info.get("sessionId")
    if session_info.get("parentSessionId") and not merged.get("parentRunId"):
        merged["parentRunId"] = session_info.get("parentSessionId")

    omo_events: list[dict[str, Any]] = []
    for source in (background_output, session_read):
        messages = source.get("messages") or source.get("items") or []
        if not isinstance(messages, list):
            continue
        for item in messages:
            if not isinstance(item, dict):
                continue
            role = _coerce_text(item.get("role"), "assistant")
            text = _coerce_text(item.get("text") or item.get("content") or item.get("summary"), "")
            if not text:
                continue
            omo_events.append({
                "kind": "message" if role != "system" else "status",
                "title": f"OMO {role}",
                "text": text,
                "createdAt": _event_timestamp(item, None),
                "meta": {
                    "source": "omo",
                    "role": role,
                },
            })

    if omo_events:
        merged.setdefault("events", [])
        merged["events"] = omo_events + list(merged.get("events") or [])
        merged.setdefault("messages", [])
        merged["messages"] = omo_events + list(merged.get("messages") or [])

    if session_info.get("childSessionIds") and not merged.get("childSessionIds"):
        merged["childSessionIds"] = list(session_info.get("childSessionIds") or [])
        merged["childRunIds"] = list(session_info.get("childSessionIds") or [])
        merged["delegatedRunIds"] = list(session_info.get("childSessionIds") or [])

    merged["provider"] = merged.get("provider") or "omo"
    return merged


def _enrich_runtime(agent: dict[str, Any], is_main: bool = False) -> dict[str, Any]:
    runtime = deepcopy(agent.get("runtime") or {}) if isinstance(agent.get("runtime"), dict) else {}
    session_id = _coerce_text(runtime.get("sessionId"), "").strip()
    if not session_id and is_main:
        db_path = _discover_opencode_db_path()
        if db_path:
            rows = _sqlite_fetch_all(
                db_path,
                "SELECT id FROM session WHERE project_id = ? AND parent_id IS NULL ORDER BY time_updated DESC LIMIT 1",
                (agent.get("projectId") or "",),
            )
            if rows:
                session_id = _coerce_text(rows[0].get("id"), "").strip()
                runtime["sessionId"] = session_id

    if session_id:
        session_tree = _query_session_tree(session_id)
        if session_tree:
            db_runtime = _extract_session_runtime(session_tree, session_id)
            db_runtime.update(runtime)
            runtime = db_runtime
            runtime["sessionId"] = session_id
            runtime.setdefault("runId", session_id)

    runtime = _merge_omo_runtime(runtime)

    if runtime.get("backgroundTaskStatus") in {"running", "pending"} and runtime.get("sessionId"):
        latest_event_time = None
        for event in runtime.get("events") or []:
            ts = _parse_iso(_coerce_text((event or {}).get("createdAt"), ""))
            if ts and (latest_event_time is None or ts > latest_event_time):
                latest_event_time = ts
        updated_at = _parse_iso(_coerce_text(runtime.get("updatedAt"), ""))
        if latest_event_time and updated_at and latest_event_time >= updated_at:
            runtime["backgroundTaskStatus"] = runtime.get("backgroundTaskStatus") or "completed"

    if runtime.get("backgroundTaskId") and runtime.get("sessionId"):
        _RUNTIME_INDEX_CACHE[str(runtime["backgroundTaskId"])] = {
            "agentId": agent.get("agentId"),
            "runId": runtime.get("runId") or runtime.get("sessionId"),
            "sessionId": runtime.get("sessionId"),
            "backgroundTaskId": runtime.get("backgroundTaskId"),
            "selectionKey": runtime.get("runId") or runtime.get("sessionId") or agent.get("agentId"),
        }
    return runtime


def get_runtime_index_snapshot() -> dict[str, dict[str, Any]]:
    return deepcopy(_RUNTIME_INDEX_CACHE)


def _safe_iso_now() -> str:
    return datetime.now().isoformat()


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


def _normalize_runtime_status(agent: dict[str, Any], runtime: dict[str, Any], state: str) -> str:
    auth_status = _coerce_text(agent.get("authStatus"), "approved").lower().strip()
    upstream_status = _coerce_text(runtime.get("status") or runtime.get("backgroundTaskStatus"), "").lower().strip()

    if auth_status == "offline":
        return "offline"
    if auth_status == "rejected":
        return "error"
    if upstream_status in {"error", "failed"}:
        return "error"
    if state == "error":
        return "error"
    if upstream_status in {"done", "completed", "success", "succeeded", "idle"}:
        return "done"
    if auth_status == "pending":
        return "waiting"
    if state in {"writing", "researching", "executing", "syncing"}:
        return "running"
    if upstream_status in {"running", "busy", "retry", "working"}:
        return "running"
    return "idle"


def _event_timestamp(event: dict[str, Any], fallback: str | None = None) -> str | None:
    for key in ("createdAt", "created_at", "updatedAt", "updated_at", "timestamp", "ts"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return fallback


def _normalize_event(run_id: str, index: int, event: Any, fallback_time: str | None = None) -> dict[str, Any]:
    if isinstance(event, str):
        return {
            "eventId": f"{run_id}:evt:{index}",
            "runId": run_id,
            "kind": "message",
            "title": "运行输出",
            "text": event,
            "createdAt": fallback_time,
            "meta": {},
        }

    if not isinstance(event, dict):
        return {
            "eventId": f"{run_id}:evt:{index}",
            "runId": run_id,
            "kind": "message",
            "title": "运行输出",
            "text": _coerce_text(event),
            "createdAt": fallback_time,
            "meta": {},
        }

    kind = _coerce_text(event.get("kind") or event.get("type"), "message").lower().strip()
    if kind not in {"thinking", "message", "tool_call", "tool_result", "status", "error"}:
        kind = "message"

    title = _coerce_text(event.get("title"), "")
    if not title:
        title_map = {
            "thinking": "思考片段",
            "message": "文本输出",
            "tool_call": "工具调用",
            "tool_result": "工具结果",
            "status": "状态变更",
            "error": "异常",
        }
        title = title_map.get(kind, "运行事件")

    text = _coerce_text(event.get("text") or event.get("content") or event.get("summary"), "")
    meta = deepcopy(event.get("meta") or {}) if isinstance(event.get("meta"), dict) else {}
    for key in ("toolName", "tool_name", "sessionId", "messageId", "partId", "status"):
        if key in event and key not in meta:
            meta[key] = event.get(key)

    event_id = _coerce_text(event.get("eventId") or event.get("id"), f"{run_id}:evt:{index}")
    created_at = _event_timestamp(event, fallback_time)
    return {
        "eventId": event_id,
        "runId": run_id,
        "kind": kind,
        "title": title,
        "text": text,
        "createdAt": created_at,
        "meta": meta,
    }


def _build_edges(runtime: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    parent_run_id = _coerce_text(runtime.get("parentRunId"), "").strip()
    if parent_run_id:
        edges.append({
            "fromRunId": parent_run_id,
            "toRunId": run_id,
            "kind": "child",
            "label": "父子运行",
        })

    for child_id in runtime.get("childRunIds") or []:
        child_run_id = _coerce_text(child_id, "").strip()
        if not child_run_id:
            continue
        edges.append({
            "fromRunId": run_id,
            "toRunId": child_run_id,
            "kind": "child",
            "label": "子运行",
        })

    delegated_to = runtime.get("delegatedRunIds") or []
    for child_id in delegated_to:
        delegated_run_id = _coerce_text(child_id, "").strip()
        if not delegated_run_id:
            continue
        edges.append({
            "fromRunId": run_id,
            "toRunId": delegated_run_id,
            "kind": "delegated",
            "label": "委派",
        })

    background_task_id = _coerce_text(runtime.get("backgroundTaskId"), "").strip()
    if background_task_id:
        edges.append({
            "fromRunId": run_id,
            "toRunId": background_task_id,
            "kind": "background_task",
            "label": "后台任务",
        })
    return edges


def _build_runtime_summary(agent: dict[str, Any]) -> dict[str, Any]:
    runtime = _enrich_runtime(agent, bool(agent.get("isMain")))
    agent_id = _coerce_text(agent.get("agentId"), "")
    agent_name = _coerce_text(agent.get("name"), agent_id or "Unknown")
    state = _coerce_text(agent.get("state"), "idle").strip() or "idle"
    updated_at = _coerce_text(agent.get("updated_at") or runtime.get("updatedAt"), "") or None
    run_id = _coerce_text(runtime.get("runId") or runtime.get("sessionId"), "").strip() or None
    status = _normalize_runtime_status(agent, runtime, state)
    phase = _coerce_text(runtime.get("phase") or state, state)
    headline = _coerce_text(runtime.get("headline") or runtime.get("summary"), "").strip()
    detail = _coerce_text(runtime.get("detail") or agent.get("detail"), "").strip()
    if not headline:
        if detail:
            headline = detail
        else:
            headline = f"{agent_name} 当前处于 {phase}"

    source_provider = _coerce_text(runtime.get("provider") or runtime.get("sourceProvider"), "none")
    session_id = _coerce_text(runtime.get("sessionId"), "").strip() or None
    background_task_id = _coerce_text(runtime.get("backgroundTaskId"), "").strip() or None
    selection_key = run_id or agent_id
    return {
        "agentId": agent_id,
        "agentName": agent_name,
        "runId": run_id,
        "status": status,
        "phase": phase,
        "headline": headline,
        "detail": detail,
        "updatedAt": updated_at,
        "source": {
            "provider": source_provider or "none",
            "sessionId": session_id,
            "backgroundTaskId": background_task_id,
        },
        "selectionKey": selection_key,
    }


def _build_runtime_detail(agent: dict[str, Any]) -> dict[str, Any]:
    runtime = _enrich_runtime(agent, bool(agent.get("isMain")))
    summary = _build_runtime_summary(agent)
    run_id = summary["runId"] or summary["selectionKey"] or summary["agentId"]
    child_session_ids = []
    for value in runtime.get("childSessionIds") or []:
        child_id = _coerce_text(value, "").strip()
        if child_id:
            child_session_ids.append(child_id)

    events_src = []
    raw_events = runtime.get("events") or []
    if isinstance(raw_events, list):
        events_src.extend(raw_events)

    for item in runtime.get("thinking") or runtime.get("latestThinking") or []:
        if isinstance(item, dict):
            event = deepcopy(item)
            event.setdefault("kind", "thinking")
        else:
            event = {"kind": "thinking", "text": _coerce_text(item)}
        events_src.append(event)

    for item in runtime.get("messages") or runtime.get("latestMessages") or []:
        if isinstance(item, dict):
            event = deepcopy(item)
            event.setdefault("kind", "message")
        else:
            event = {"kind": "message", "text": _coerce_text(item)}
        events_src.append(event)

    for item in runtime.get("tools") or runtime.get("latestTools") or []:
        if isinstance(item, dict):
            event = deepcopy(item)
            event.setdefault("kind", event.get("result") and "tool_result" or "tool_call")
        else:
            event = {"kind": "tool_result", "text": _coerce_text(item)}
        events_src.append(event)

    if not events_src and summary.get("detail"):
        events_src = [
            {
                "kind": "status",
                "title": "当前状态说明",
                "text": summary.get("detail") or summary.get("headline") or "",
                "createdAt": summary.get("updatedAt"),
            }
        ]
    normalized_events = [
        _normalize_event(run_id, idx, event, summary.get("updatedAt"))
        for idx, event in enumerate(events_src)
    ]
    normalized_events.sort(
        key=lambda item: _parse_iso(item.get("createdAt")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    raw = {
        "agent": deepcopy(agent),
        "runtime": deepcopy(runtime),
        "opencode": deepcopy(runtime.get("opencode") or {}),
        "omo": deepcopy(runtime.get("omo") or {}),
    }

    return {
        "runId": run_id,
        "agentId": summary["agentId"],
        "agentName": summary["agentName"],
        "status": summary["status"],
        "summary": summary,
        "session": {
            "sessionId": _coerce_text(runtime.get("sessionId"), "").strip() or None,
            "childSessionIds": child_session_ids,
        },
        "backgroundTask": {
            "taskId": _coerce_text(runtime.get("backgroundTaskId"), "").strip() or None,
            "status": _coerce_text(runtime.get("backgroundTaskStatus"), "").strip() or None,
        },
        "edges": _build_edges(runtime, run_id),
        "events": normalized_events,
        "raw": raw,
    }


def _stable_sort_key(item: dict[str, Any]) -> tuple[int, str, str]:
    status = _coerce_text(item.get("status"), "idle")
    status_rank = RUNTIME_STATUS_ORDER.get(status, 0)
    updated_at = _coerce_text(item.get("updatedAt"), "")
    return (-status_rank, updated_at, _coerce_text(item.get("agentName"), ""))


def build_runtime_overview(main_state: dict[str, Any], agents: list[dict[str, Any]], synthetic_agents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    main_agent = next((a for a in agents if a.get("isMain")), None)
    main_agent_name = _coerce_text((main_agent or {}).get("name"), "Star")
    synthetic_main = deepcopy(main_agent or {})
    synthetic_main.update({
        "agentId": synthetic_main.get("agentId") or "star",
        "name": main_agent_name,
        "isMain": True,
        "projectId": main_state.get("projectId") or synthetic_main.get("projectId"),
        "state": main_state.get("state") or synthetic_main.get("state") or "idle",
        "detail": main_state.get("detail") or synthetic_main.get("detail") or "",
        "updated_at": main_state.get("updated_at") or synthetic_main.get("updated_at") or _safe_iso_now(),
        "area": synthetic_main.get("area") or "breakroom",
        "runtime": deepcopy(synthetic_main.get("runtime") or {}),
    })

    items = [_build_runtime_summary(synthetic_main)]
    for agent in agents:
        if agent.get("isMain"):
            continue
        items.append(_build_runtime_summary(agent))
    for synthetic in synthetic_agents or []:
        items.append(deepcopy(synthetic))
    items.sort(key=_stable_sort_key)
    _RUNTIME_INDEX_CACHE.clear()
    for item in items:
        index_payload = {
            "agentId": item.get("agentId"),
            "runId": item.get("runId"),
            "sessionId": (item.get("source") or {}).get("sessionId"),
            "backgroundTaskId": (item.get("source") or {}).get("backgroundTaskId"),
            "selectionKey": item.get("selectionKey"),
            "rootSessionId": item.get("rootSessionId"),
            "officeId": item.get("officeId"),
            "syntheticAgentId": item.get("agentId") if item.get("synthetic") else None,
        }
        for key in (item.get("selectionKey"), item.get("runId"), item.get("agentId"), (item.get("source") or {}).get("sessionId"), item.get("rootSessionId"), item.get("officeId")):
            if key:
                _RUNTIME_INDEX_CACHE[str(key)] = deepcopy(index_payload)
    return {
        "ok": True,
        "generatedAt": _safe_iso_now(),
        "items": items,
    }


def build_runtime_detail(main_state: dict[str, Any], agents: list[dict[str, Any]], identifier: str, synthetic_details: dict[str, dict[str, Any]] | None = None) -> dict[str, Any] | None:
    identifier = _coerce_text(identifier, "").strip()
    if not identifier:
        return None

    if synthetic_details:
        if identifier in synthetic_details:
            detail = deepcopy(synthetic_details[identifier])
            mapping = {
                "agentId": detail.get("agentId"),
                "runId": detail.get("runId"),
                "sessionId": (detail.get("session") or {}).get("sessionId"),
                "backgroundTaskId": (detail.get("backgroundTask") or {}).get("taskId"),
                "selectionKey": (detail.get("summary") or {}).get("selectionKey"),
                "rootSessionId": detail.get("rootSessionId"),
                "officeId": detail.get("officeId"),
                "syntheticAgentId": detail.get("agentId") if detail.get("synthetic") else None,
            }
            for key in (mapping.get("selectionKey"), mapping.get("runId"), mapping.get("agentId"), mapping.get("sessionId"), mapping.get("backgroundTaskId"), mapping.get("rootSessionId"), mapping.get("officeId")):
                if key:
                    _RUNTIME_INDEX_CACHE[str(key)] = deepcopy(mapping)
            return {"ok": True, "generatedAt": _safe_iso_now(), "item": detail}

    main_agent = next((a for a in agents if a.get("isMain")), None)
    synthetic_main = deepcopy(main_agent or {})
    synthetic_main.update({
        "agentId": synthetic_main.get("agentId") or "star",
        "name": synthetic_main.get("name") or "Star",
        "isMain": True,
        "projectId": main_state.get("projectId") or synthetic_main.get("projectId"),
        "state": main_state.get("state") or synthetic_main.get("state") or "idle",
        "detail": main_state.get("detail") or synthetic_main.get("detail") or "",
        "updated_at": main_state.get("updated_at") or synthetic_main.get("updated_at") or _safe_iso_now(),
        "runtime": deepcopy(synthetic_main.get("runtime") or {}),
    })
    candidates = [synthetic_main] + [a for a in agents if not a.get("isMain")]

    for agent in candidates:
        summary = _build_runtime_summary(agent)
        if identifier in {summary.get("selectionKey"), summary.get("runId"), summary.get("agentId")}:
            detail = _build_runtime_detail(agent)
            for key in (summary.get("selectionKey"), summary.get("runId"), summary.get("agentId"), (detail.get("session") or {}).get("sessionId"), (detail.get("backgroundTask") or {}).get("taskId")):
                if key:
                    _RUNTIME_INDEX_CACHE[str(key)] = {
                        "agentId": detail.get("agentId"),
                        "runId": detail.get("runId"),
                        "sessionId": (detail.get("session") or {}).get("sessionId"),
                        "backgroundTaskId": (detail.get("backgroundTask") or {}).get("taskId"),
                        "selectionKey": summary.get("selectionKey"),
                    }
            return {
                "ok": True,
                "generatedAt": _safe_iso_now(),
                "item": detail,
            }
    return None
