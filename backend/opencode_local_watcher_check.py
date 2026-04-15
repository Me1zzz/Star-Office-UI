#!/usr/bin/env python3
"""Smoke verification for local watcher materialization."""

from __future__ import annotations

import json
from opencode_local_watcher import get_local_watcher


def main():
    watcher = get_local_watcher()
    overview = watcher.get_overview()
    mappings = watcher.get_mappings()
    sample = overview[0] if overview else {}
    print(json.dumps({
        "enabled": watcher.enabled,
        "count": len(overview),
        "sourceMode": mappings.get("sourceMode"),
        "sampleAgentId": sample.get("agentId"),
        "sampleRootSessionId": sample.get("rootSessionId"),
        "sampleOfficeLocalId": sample.get("officeLocalId"),
        "sampleOfficeId": sample.get("officeId"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
