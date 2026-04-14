#!/usr/bin/env python3
"""Runtime route helpers to minimize app.py surface area."""

from __future__ import annotations

import os
from datetime import datetime

from agent_runtime_utils import build_runtime_detail, build_runtime_overview, get_runtime_index_snapshot
from opencode_local_watcher import get_local_watcher


def build_status_response(load_state, get_office_name_from_identity, get_opencode_project_id):
    state = load_state()
    office_name = get_office_name_from_identity()
    project_id = get_opencode_project_id()
    if office_name:
        state["officeName"] = office_name
    if project_id:
        state["projectId"] = project_id
    return state


def build_runtime_overview_response(load_state, load_agents_state, get_office_name_from_identity, save_runtime_mappings_snapshot, get_opencode_project_id):
    state = load_state()
    agents = load_agents_state()
    office_name = get_office_name_from_identity()
    project_id = get_opencode_project_id()
    watcher = get_local_watcher()
    synthetic_agents = watcher.get_overview(project_id=project_id, directory=None)
    payload = build_runtime_overview(state, agents, synthetic_agents=synthetic_agents)
    save_runtime_mappings_snapshot(get_runtime_index_snapshot())
    if office_name:
        payload["officeName"] = office_name
    return payload


def build_runtime_detail_response(identifier, load_state, load_agents_state, get_office_name_from_identity, save_runtime_mappings_snapshot, get_opencode_project_id):
    state = load_state()
    agents = load_agents_state()
    project_id = get_opencode_project_id()
    watcher = get_local_watcher()
    watcher_detail = watcher.get_detail(identifier, project_id=project_id, directory=None)
    synthetic_details = {}
    if watcher_detail:
        synthetic_details[identifier] = watcher_detail
        if watcher_detail.get("runId"):
            synthetic_details[watcher_detail.get("runId")] = watcher_detail
        if watcher_detail.get("rootSessionId"):
            synthetic_details[watcher_detail.get("rootSessionId")] = watcher_detail
        if watcher_detail.get("officeId"):
            synthetic_details[watcher_detail.get("officeId")] = watcher_detail
        if watcher_detail.get("agentId"):
            synthetic_details[watcher_detail.get("agentId")] = watcher_detail
    payload = build_runtime_detail(state, agents, identifier, synthetic_details=synthetic_details)
    if not payload:
        return None
    save_runtime_mappings_snapshot(get_runtime_index_snapshot())
    office_name = get_office_name_from_identity()
    if office_name:
        payload["officeName"] = office_name
    return payload


def build_runtime_mappings_response(load_runtime_mappings_snapshot, get_opencode_project_id):
    live_items = get_runtime_index_snapshot()
    file_items = load_runtime_mappings_snapshot()
    watcher = get_local_watcher()
    watcher_state = watcher.get_mappings(project_id=get_opencode_project_id(), directory=None)
    return {
        "ok": True,
        "generatedAt": datetime.now().isoformat(),
        "items": live_items or file_items or watcher_state.get("items") or {},
        "watcher": {
            "enabled": watcher_state.get("enabled"),
            "lastRefreshAt": watcher_state.get("lastRefreshAt"),
            "syntheticCount": watcher_state.get("syntheticCount"),
        },
        "omo": {
            "backgroundOutputEnabled": bool(os.getenv("STAR_OMO_BACKGROUND_OUTPUT", "").strip()),
            "sessionReadEnabled": bool(os.getenv("STAR_OMO_SESSION_READ", "").strip()),
            "sessionInfoEnabled": bool(os.getenv("STAR_OMO_SESSION_INFO", "").strip()),
        },
    }
