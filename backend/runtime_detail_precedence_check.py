#!/usr/bin/env python3
"""Regression check: explicit descendant detail must beat synthetic root alias."""

from __future__ import annotations

from copy import deepcopy

import runtime_routes


ROOT_SESSION_ID = "ses_root_probe"
CHILD_SESSION_ID = "ses_child_probe"
OFFICE_ID = "local.default:ses_root_probe"


class FakeWatcher:
    def get_detail(self, identifier: str, project_id=None, directory=None):
        if identifier not in {ROOT_SESSION_ID, CHILD_SESSION_ID, OFFICE_ID, f"local:{ROOT_SESSION_ID}"}:
            return None
        return {
            "agentId": f"local:{ROOT_SESSION_ID}",
            "agentName": "Synthetic Root",
            "runId": ROOT_SESSION_ID,
            "rootSessionId": ROOT_SESSION_ID,
            "officeLocalId": ROOT_SESSION_ID,
            "officeId": OFFICE_ID,
            "serverOrigin": "local.default",
            "synthetic": True,
            "summary": {
                "selectionKey": f"local:{ROOT_SESSION_ID}",
                "headline": "Synthetic Root",
            },
            "session": {
                "sessionId": ROOT_SESSION_ID,
                "childSessionIds": [CHILD_SESSION_ID],
                "ancestorSessionIds": [],
                "descendantSessionIds": [CHILD_SESSION_ID],
            },
            "backgroundTask": {"taskId": None, "status": None},
            "lineage": {
                "rootSessionId": ROOT_SESSION_ID,
                "officeId": OFFICE_ID,
                "officeLocalId": ROOT_SESSION_ID,
                "lineageDepth": 0,
                "lineageConfidence": "resolved",
                "officeRole": "root",
            },
            "edges": [],
            "events": [],
            "raw": {},
        }


def load_state():
    return {
        "state": "idle",
        "detail": "",
        "updated_at": "2026-04-15T00:00:00",
    }


def load_agents_state():
    return [
        {
            "agentId": "agent_probe",
            "name": "Explicit Descendant",
            "isMain": False,
            "state": "executing",
            "detail": "explicit descendant detail",
            "updated_at": "2026-04-15T00:00:01",
            "runtime": {
                "provider": "opencode",
                "sessionId": CHILD_SESSION_ID,
                "runId": CHILD_SESSION_ID,
                "parentRunId": ROOT_SESSION_ID,
                "rootSessionIdHint": ROOT_SESSION_ID,
                "officeLocalIdHint": ROOT_SESSION_ID,
                "officeIdHint": OFFICE_ID,
                "serverOrigin": "local.default",
                "headline": "Explicit Descendant",
                "detail": "explicit descendant detail",
                "status": "running",
                "phase": "executing",
            },
        }
    ]


def save_runtime_mappings_snapshot(_items):
    return None


def main():
    original = runtime_routes.get_local_watcher
    runtime_routes.get_local_watcher = lambda: FakeWatcher()
    try:
        payload = runtime_routes.build_runtime_detail_response(
            CHILD_SESSION_ID,
            load_state,
            load_agents_state,
            lambda: None,
            save_runtime_mappings_snapshot,
            lambda: None,
        )
    finally:
        runtime_routes.get_local_watcher = original

    assert payload is not None, "expected payload"
    item = payload["item"]
    assert item["agentId"] == "agent_probe", f"expected explicit descendant detail, got {item['agentId']}"
    assert item["runId"] == CHILD_SESSION_ID, f"expected child run id, got {item['runId']}"
    assert item["rootSessionId"] == ROOT_SESSION_ID, f"expected root session id, got {item['rootSessionId']}"
    assert item["officeId"] == OFFICE_ID, f"expected office id, got {item['officeId']}"
    print("runtime detail precedence check: PASS")


if __name__ == "__main__":
    main()
