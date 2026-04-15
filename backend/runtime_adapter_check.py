#!/usr/bin/env python3
"""Lightweight verification for runtime adapter aggregation."""

from __future__ import annotations

import json
from agent_runtime_utils import build_runtime_detail, build_runtime_overview
from runtime_lineage_resolver import build_office_identity, get_server_origin


def main():
    main_state = {
        "state": "writing",
        "detail": "正在汇总运行态",
        "updated_at": "2026-04-13T20:00:00",
        "projectId": None,
    }
    agents = [
        {
            "agentId": "star",
            "name": "Star",
            "isMain": True,
            "state": "writing",
            "detail": "正在汇总运行态",
            "updated_at": "2026-04-13T20:00:00",
            "runtime": {
                "sessionId": None,
            },
        },
        {
            "agentId": "agent_demo",
            "name": "Demo Agent",
            "state": "executing",
            "detail": "执行中",
            "updated_at": "2026-04-13T20:00:00",
            "runtime": {
                "sessionId": "ses_demo",
                "runId": "ses_demo",
                "rootSessionIdHint": "ses_root_demo",
                "officeIdHint": build_office_identity("ses_root_demo", get_server_origin()).get("officeId"),
                "headline": "Demo run",
                "detail": "正在处理 demo 流程",
                "backgroundTaskStatus": "running",
                "thinking": ["先检查输入", "再决定下一步"],
                "messages": ["输出一", "输出二"],
                "tools": [{"toolName": "bash", "kind": "tool_result", "text": "ok"}],
                "childSessionIds": ["ses_child_demo"],
                "delegatedRunIds": ["ses_child_demo"],
                "backgroundTaskId": "bg_demo123",
                "omo": {
                    "backgroundTaskId": "bg_demo123",
                    "backgroundTaskStatus": "running",
                    "sessionInfo": {
                        "sessionId": "ses_demo",
                        "childSessionIds": ["ses_child_demo"]
                    },
                    "sessionRead": {
                        "messages": [
                            {"role": "assistant", "text": "OMO fallback message", "createdAt": "2026-04-13T20:00:01"}
                        ]
                    }
                }
            },
        },
    ]

    overview = build_runtime_overview(main_state, agents)
    assert overview["ok"] is True
    assert len(overview["items"]) >= 2
    assert overview["offices"]
    agent_item = next(item for item in overview["items"] if item.get("agentId") == "agent_demo")
    assert agent_item["rootSessionId"] == "ses_root_demo"
    assert agent_item["officeId"] == build_office_identity("ses_root_demo", get_server_origin()).get("officeId")

    detail = build_runtime_detail(main_state, agents, "ses_demo")
    assert detail and detail["ok"] is True
    item = detail["item"]
    assert item["runId"] == "ses_demo"
    assert item["rootSessionId"] == "ses_root_demo"
    assert item["backgroundTask"]["taskId"] == "bg_demo123"
    assert any(evt["kind"] == "thinking" for evt in item["events"])
    assert any(evt["kind"] in {"tool_call", "tool_result"} for evt in item["events"])
    assert any(evt["text"] == "OMO fallback message" for evt in item["events"])
    print(json.dumps({
        "overview_count": len(overview["items"]),
        "office_count": len(overview["offices"]),
        "detail_run_id": item["runId"],
        "detail_root_session_id": item["rootSessionId"],
        "detail_event_count": len(item["events"]),
        "edge_count": len(item["edges"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
