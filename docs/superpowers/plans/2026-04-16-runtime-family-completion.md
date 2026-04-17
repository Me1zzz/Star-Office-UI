# Runtime Family Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete all OpenSpec changes except `add-watcher-scope-modes`, finish the remaining `show-full-root-session-family-in-office` work, and refactor runtime/watcher code for better readability, maintainability, and future scope-mode extensibility while preserving strong runtime API compatibility.

**Architecture:** Keep `runtime_lineage_resolver.py` as the canonical office-identity source, split oversized runtime/watcher responsibilities into smaller helpers, and serve the same public runtime endpoints through a thinner adapter layer. The refactor should separate lineage resolution, runtime normalization, office projection, and API compatibility shaping so future scope visibility work can extend discovery/filtering without redefining office identity.

**Tech Stack:** Python 3.10+, Flask backend, vanilla JS frontend, OpenSpec task files, existing runtime validation scripts.

---

## File Structure

### Existing files to modify

- `backend/agent_runtime_utils.py`
  - Shrink responsibility by extracting event shaping, summary/detail projection, office overview aggregation, and mapping/index helpers.
- `backend/opencode_local_watcher.py`
  - Split `_materialize()` into smaller helpers for family grouping, event extraction, and synthetic projection.
- `backend/runtime_routes.py`
  - Keep compatibility routing thin while switching to refactored helpers.
- `backend/runtime_lineage_check.py`
  - Extend to validate mixed watcher + explicit push canonical office behavior.
- `backend/runtime_adapter_check.py`
  - Extend to validate overview/detail compatibility and office family projections.
- `backend/runtime_detail_precedence_check.py`
  - Adjust if detail shape changes internally but remains externally compatible.
- `backend/opencode_local_watcher_check.py`
  - Extend to validate descendant visibility inputs and watcher projection invariants.
- `frontend/runtime-inspector.js`
  - Consume structured family data and make descendants selectable.
- `frontend/runtime-game-bridge.js`
  - Align bridge selection with structured office member behavior.
- `openspec/changes/show-full-root-session-family-in-office/tasks.md`
  - Mark remaining tasks complete when verified.

### New files to create

- `backend/runtime_projection.py`
  - Focused helpers for summary/detail/office aggregate shaping.
- `backend/runtime_events.py`
  - Shared event normalization helpers reused by runtime adapter and watcher projection.
- `backend/runtime_index.py`
  - Runtime mapping/index cache shaping helpers.
- `backend/runtime_family_view.py`
  - Helpers that build structured family sections for descendants, ancestors, and office members.

> If code review shows one of these helpers fits better as a section inside an existing file, prefer smaller focused files over enlarging `agent_runtime_utils.py` further.

### Primary verification commands

- `python -m py_compile backend/*.py`
- `python backend/runtime_lineage_check.py`
- `python backend/runtime_adapter_check.py`
- `python backend/runtime_detail_precedence_check.py`
- `python backend/opencode_local_watcher_check.py`

---

## Task 1: Baseline verification before refactor

**Files:**
- Modify: none
- Test: `backend/runtime_lineage_check.py`, `backend/runtime_adapter_check.py`, `backend/runtime_detail_precedence_check.py`, `backend/opencode_local_watcher_check.py`

- [ ] **Step 1: Record current OpenSpec target state**

Read and note the remaining unchecked tasks in:

```text
openspec/changes/show-full-root-session-family-in-office/tasks.md
```

Success condition: you can explicitly name the two remaining unchecked tasks before changing code.

- [ ] **Step 2: Run current verification scripts and capture baseline**

Run:

```bash
python backend/runtime_lineage_check.py
python backend/runtime_adapter_check.py
python backend/runtime_detail_precedence_check.py
python backend/opencode_local_watcher_check.py
```

Expected: identify which current checks already pass and whether any script lacks mixed-mode/family-selection coverage.

- [ ] **Step 3: Run Python syntax validation over backend runtime files**

Run:

```bash
python -m py_compile backend/agent_runtime_utils.py backend/opencode_local_watcher.py backend/runtime_routes.py backend/runtime_lineage_resolver.py
```

Expected: success. If this fails before any edits, document as a pre-existing issue and stop.

---

## Task 2: Extract shared runtime event and projection helpers

**Files:**
- Create: `backend/runtime_events.py`
- Create: `backend/runtime_projection.py`
- Create: `backend/runtime_index.py`
- Modify: `backend/agent_runtime_utils.py`
- Test: `backend/runtime_adapter_check.py`

- [ ] **Step 1: Write a failing compatibility-oriented check for runtime overview/detail**

Add or extend a check in `backend/runtime_adapter_check.py` to assert:

```python
assert overview["ok"] is True
assert isinstance(overview["items"], list)
assert isinstance(overview["offices"], list)
assert detail["ok"] is True
assert "subject" in detail
assert "office" in detail
assert "lineage" in detail
```

Run:

```bash
python backend/runtime_adapter_check.py
```

Expected: fail once you add stronger assertions that the current refactor target does not yet provide through shared helpers, or at minimum fail on missing structured family sections if you add those assertions here.

- [ ] **Step 2: Create `backend/runtime_events.py` with event-focused helpers**

Move or introduce focused helpers for logic currently embedded in `agent_runtime_utils.py`, such as:

```python
def event_timestamp(event: dict[str, Any], fallback: str | None = None) -> str | None: ...
def normalize_event(run_id: str, index: int, event: dict[str, Any], fallback_time: str | None) -> dict[str, Any]: ...
```

Keep behavior unchanged.

- [ ] **Step 3: Create `backend/runtime_projection.py` with summary/detail/office projection helpers**

Introduce focused functions such as:

```python
def build_runtime_summary(agent: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]: ...
def build_runtime_detail(agent: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]: ...
def build_runtime_overview_payload(items: list[dict[str, Any]]) -> dict[str, Any]: ...
```

These names may differ, but the intent is mandatory: projection logic leaves `agent_runtime_utils.py`.

- [ ] **Step 4: Create `backend/runtime_index.py` for mapping/index shaping**

Extract the `_RUNTIME_INDEX_CACHE` mutation logic behind helper functions so item/detail/index mapping behavior is easier to test independently.

- [ ] **Step 5: Rewire `backend/agent_runtime_utils.py` to use the new helpers**

Keep public functions and return values compatible:

```python
def build_runtime_overview(...): ...
def build_runtime_detail(...): ...
def get_runtime_index_snapshot(): ...
```

The compatibility requirement is strict: callers should not need to change.

- [ ] **Step 6: Re-run runtime adapter verification**

Run:

```bash
python backend/runtime_adapter_check.py
python -m py_compile backend/agent_runtime_utils.py backend/runtime_projection.py backend/runtime_events.py backend/runtime_index.py
```

Expected: pass.

---

## Task 3: Split watcher materialization into smaller units

**Files:**
- Modify: `backend/opencode_local_watcher.py`
- Test: `backend/opencode_local_watcher_check.py`

- [ ] **Step 1: Strengthen watcher verification before refactor**

Add or extend watcher checks so they assert stable synthetic office identity fields:

```python
assert summary["officeId"]
assert summary["rootSessionId"]
assert detail["lineageConfidence"] == "resolved"
assert isinstance(detail["events"], list)
```

Run:

```bash
python backend/opencode_local_watcher_check.py
```

Expected: pass or fail only for the new stronger expectations you are about to implement.

- [ ] **Step 2: Extract family-grouping helpers from `_materialize()`**

Create focused private helpers inside `backend/opencode_local_watcher.py`, for example:

```python
def _group_sessions_by_root(self, sessions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]: ...
def _build_message_indexes(...): ...
```

Goal: remove raw grouping/index-building detail from the main orchestration flow.

- [ ] **Step 3: Extract family event/tool/message shaping helpers**

Create private helpers that return structured family event collections instead of inlining all extraction logic in one loop.

- [ ] **Step 4: Extract synthetic summary/detail/mapping projection helpers**

Create helpers that build:

- synthetic office summary
- synthetic detail payload
- watcher mapping entries

Keep the same external fields and semantics.

- [ ] **Step 5: Reduce `_materialize()` to orchestration**

Target shape:

```python
def _materialize(...):
    sessions = ...
    grouped = ...
    for root_id, family in grouped.items():
        family_inputs = ...
        summary, detail, mappings = ...
```

The exact code can differ, but the function should read as orchestration rather than implementation soup.

- [ ] **Step 6: Re-run watcher verification**

Run:

```bash
python backend/opencode_local_watcher_check.py
python -m py_compile backend/opencode_local_watcher.py
```

Expected: pass.

---

## Task 4: Add structured family view support for descendants

**Files:**
- Create: `backend/runtime_family_view.py`
- Modify: `backend/runtime_projection.py`
- Modify: `backend/agent_runtime_utils.py`
- Modify: `frontend/runtime-inspector.js`
- Modify: `frontend/runtime-game-bridge.js`
- Test: `backend/runtime_adapter_check.py`

- [ ] **Step 1: Write a failing check for descendant visibility in detail payload**

Add or extend a backend check asserting that detail data exposes structured family sections, not just raw arrays:

```python
family = detail["subject"].get("family") or detail.get("family")
assert family is not None
assert isinstance(family.get("members"), list)
assert isinstance(family.get("descendants"), list)
```

Run:

```bash
python backend/runtime_adapter_check.py
```

Expected: fail before implementation.

- [ ] **Step 2: Create `backend/runtime_family_view.py`**

Add helper(s) that shape structured family sections from runtime lineage and office member data, for example:

```python
def build_family_view(summary: dict[str, Any], runtime: dict[str, Any], office_members: list[dict[str, Any]]) -> dict[str, Any]: ...
```

Required output concepts:

- members
- ancestors
- descendants
- selected subject metadata

- [ ] **Step 3: Include family sections in detail payloads**

Update runtime detail shaping so descendants are available in structured form for normal UI consumption, not only through `raw`, `events`, or bare lineage arrays.

- [ ] **Step 4: Update `frontend/runtime-inspector.js` to render selectable family members**

Implement family rendering using structured detail data.

Required behavior:

- descendants are visible in summary/family view
- clicking a family member selects it via existing runtime detail flow
- current summary, tabs, and compatibility behavior remain intact

- [ ] **Step 5: Update `frontend/runtime-game-bridge.js` only as needed**

Keep the bridge simple; only adjust selection glue if structured family/member behavior requires it.

- [ ] **Step 6: Re-run adapter verification**

Run:

```bash
python backend/runtime_adapter_check.py
python -m py_compile backend/agent_runtime_utils.py backend/runtime_projection.py backend/runtime_family_view.py
```

Expected: pass.

---

## Task 5: Add mixed watcher + explicit push canonical-office validation

**Files:**
- Modify: `backend/runtime_lineage_check.py`
- Modify: `backend/runtime_adapter_check.py`
- Modify: `backend/runtime_projection.py` or `backend/agent_runtime_utils.py` as needed
- Test: `backend/runtime_lineage_check.py`, `backend/runtime_adapter_check.py`

- [ ] **Step 1: Write a failing mixed-mode office assertion**

Add or extend a check that constructs/uses equivalent watcher-derived and explicit runtime inputs for the same root family and asserts:

```python
assert watcher_summary["officeId"] == explicit_summary["officeId"]
assert watcher_summary["rootSessionId"] == explicit_summary["rootSessionId"]
assert len({item["officeId"] for item in office_items if item["rootSessionId"] == root_id}) == 1
```

Run:

```bash
python backend/runtime_lineage_check.py
```

Expected: fail until mixed-mode handling is made robust.

- [ ] **Step 2: Fix any projection or mapping divergence exposed by the new check**

If watcher and explicit paths currently shape office identity differently, resolve that in shared projection/normalization code rather than with route-layer patches.

- [ ] **Step 3: Ensure `/runtime/mappings` remains canonical and compatible**

Preserve current mappings behavior while making sure mixed-mode aliases still collapse to one canonical office identity.

- [ ] **Step 4: Re-run mixed-mode validation**

Run:

```bash
python backend/runtime_lineage_check.py
python backend/runtime_adapter_check.py
```

Expected: pass.

---

## Task 6: Verify strong compatibility and complete OpenSpec tasks

**Files:**
- Modify: `openspec/changes/show-full-root-session-family-in-office/tasks.md`
- Test: all runtime verification scripts

- [ ] **Step 1: Run the full verification set**

Run:

```bash
python backend/runtime_lineage_check.py
python backend/runtime_adapter_check.py
python backend/runtime_detail_precedence_check.py
python backend/opencode_local_watcher_check.py
python -m py_compile backend/agent_runtime_utils.py backend/opencode_local_watcher.py backend/runtime_routes.py backend/runtime_projection.py backend/runtime_events.py backend/runtime_index.py backend/runtime_family_view.py
```

Expected: all pass.

- [ ] **Step 2: Confirm the two remaining OpenSpec tasks are satisfied by evidence**

Map evidence explicitly:

- `5.2` mixed watcher + explicit push does not split one office → passing mixed-mode validation script
- `5.3` descendants visible and selectable in family view → structured detail payload + frontend interaction path

- [ ] **Step 3: Mark the remaining OpenSpec tasks complete**

Update:

```text
openspec/changes/show-full-root-session-family-in-office/tasks.md
```

Change:

```markdown
- [ ] 5.2 ...
- [ ] 5.3 ...
```

to:

```markdown
- [x] 5.2 ...
- [x] 5.3 ...
```

- [ ] **Step 4: Sanity-check no accidental scope-mode implementation slipped in**

Confirm the work did not introduce explicit support for:

- `current-project`
- `one-server`
- `multi-server-aggregate`

If any of those appear as completed product behavior, revert that part before finishing.

---

## Task 7: Final review and handoff

**Files:**
- Modify: optional docs only if behavior changed materially
- Test: repo status + targeted file review

- [ ] **Step 1: Review all touched files for responsibility boundaries**

Check that:

- watcher logic is more modular
- runtime projection is more modular
- route layer stayed thin
- family visibility is structured rather than raw-only

- [ ] **Step 2: Review compatibility-sensitive payload fields**

Spot-check that these still exist where expected:

```python
"items"
"offices"
"subject"
"office"
"lineage"
"selectionKey"
"officeId"
"rootSessionId"
```

- [ ] **Step 3: Summarize completion evidence**

Prepare a final implementation summary covering:

- files added/changed
- verification commands run
- which OpenSpec tasks were closed
- why the refactor makes future `add-watcher-scope-modes` easier

---

## Spec Coverage Check

- Complete `show-full-root-session-family-in-office` → covered by Tasks 4, 5, and 6.
- Preserve and improve `add-opencode-local-watcher` → covered by Task 3.
- Preserve and improve `add-agent-runtime-visualization` → covered by Tasks 2 and 4.
- Strong compatibility for runtime APIs → covered by Tasks 2, 5, 6, and 7.
- Prepare for future `add-watcher-scope-modes` without implementing it → covered by File Structure, Tasks 2–3, and Task 6 Step 4.

## Placeholder Scan

No `TODO`, `TBD`, or deferred “implement later” placeholders should remain during execution. If a helper file name changes during implementation, update the plan execution notes and keep the responsibility split intact.

## Execution Choice

Plan complete and saved to `docs/superpowers/plans/2026-04-16-runtime-family-completion.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
