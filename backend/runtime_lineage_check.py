#!/usr/bin/env python3
"""Lightweight verification for canonical lineage helpers."""

from __future__ import annotations

import json

from runtime_lineage_resolver import build_office_identity, get_server_origin, resolve_runtime_lineage


def main():
    identity = build_office_identity("ses_root_demo", get_server_origin())
    resolved = resolve_runtime_lineage({
        "sessionId": "ses_child_demo",
        "parentRunId": "ses_root_demo",
        "rootSessionIdHint": "ses_root_demo",
        "officeIdHint": identity.get("officeId"),
        "serverOrigin": get_server_origin(),
    })
    assert resolved["rootSessionId"] == "ses_root_demo"
    assert resolved["officeId"] == identity.get("officeId")
    assert resolved["officeLocalId"] == "ses_root_demo"
    assert resolved["lineageConfidence"] in {"provisional", "resolved"}
    print(json.dumps({
        "serverOrigin": resolved.get("serverOrigin"),
        "rootSessionId": resolved.get("rootSessionId"),
        "officeId": resolved.get("officeId"),
        "officeLocalId": resolved.get("officeLocalId"),
        "lineageConfidence": resolved.get("lineageConfidence"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
