# Runtime Family Completion Design

## Summary

This design completes the remaining OpenSpec work for all changes except `add-watcher-scope-modes`.

The implementation will:

- fully close `show-full-root-session-family-in-office`
- preserve and structurally improve `add-opencode-local-watcher`
- preserve and structurally improve `add-agent-runtime-visualization`
- keep `/runtime/overview`, `/runtime/agents/<identifier>`, and `/runtime/mappings` strongly backward compatible
- improve readability, maintainability, and extensibility so that future watcher scope modes can be added without redefining office identity semantics

## Confirmed Constraints

- Do **not** implement `add-watcher-scope-modes` in this work.
- Use a **medium refactor** rather than a minimal patch or a large rewrite.
- Prefer **code/script validation** over heavy new frontend test infrastructure.
- Keep runtime API payloads **strongly compatible**.

## Problem Statement

The repository already contains most of the core runtime lineage and office-family model, but the current implementation is uneven across the three relevant changes.

- `add-opencode-local-watcher` is functionally implemented, but watcher materialization is too monolithic.
- `add-agent-runtime-visualization` is implemented, but the frontend still consumes family data through a mixture of summary fields, raw payloads, and ad-hoc list derivation.
- `show-full-root-session-family-in-office` is largely implemented, but two important expectations remain open:
  1. mixed watcher + explicit push must never split one root family into multiple offices
  2. descendants must be visible and selectable in the office family view, not only observable in raw/timeline data

The structural issue underneath all three is that office identity, runtime normalization, watcher materialization, and UI consumption are still too entangled in a few oversized modules.

## Goals

1. Finish `show-full-root-session-family-in-office` completely.
2. Preserve the completed behavior of `add-opencode-local-watcher` and `add-agent-runtime-visualization` while reducing structural debt.
3. Separate internal concerns into clearer layers so future work can evolve safely.
4. Make future `add-watcher-scope-modes` implementation easier by isolating **scope visibility** from **office identity**.
5. Keep current endpoint names and primary payload contracts stable.

## Non-Goals

- Do not implement `current-project`, `one-server`, or `multi-server-aggregate` scope modes now.
- Do not introduce a large new frontend testing framework.
- Do not replace current runtime endpoints with a new API family.
- Do not redefine office identity away from canonical root-family lineage.

## Architectural Direction

The implementation will adopt a four-layer internal structure while preserving external API shape.

### 1. Lineage Resolution Layer

Responsibility: determine canonical office identity.

- `backend/runtime_lineage_resolver.py` remains the only canonical lineage truth source.
- It is responsible for `serverOrigin`, `rootSessionId`, `officeLocalId`, `officeId`, `officeRole`, `lineageDepth`, `lineageConfidence`, ancestor sets, and descendant sets.
- Future watcher scope modes must not modify this layer's semantics; they may only affect which offices are discovered or visible.

### 2. Runtime Normalization Layer

Responsibility: convert raw explicit runtime data and watcher-derived runtime data into a consistent internal run model.

- The current responsibilities packed into `backend/agent_runtime_utils.py` should be split into smaller helpers or modules.
- Explicit push, OMO enrichment, and watcher-derived runs should all pass through consistent normalized-run shaping before projection.
- The normalized representation should be internal-first, not a public API contract.

### 3. Office Projection Layer

Responsibility: generate office-aware views from normalized runs.

The projection layer should generate three internal views:

- **Normalized Run**: runtime-centric representation
- **Office Member**: how a run appears inside an office family
- **Office Aggregate**: office selector and office-level summary data

This layer should also produce detail-friendly family sections so descendants become first-class view objects rather than raw-only evidence.

### 4. API Adapter Layer

Responsibility: preserve strong compatibility while serving richer data.

- `backend/runtime_routes.py` remains thin.
- Existing endpoints remain unchanged.
- Existing fields stay available wherever practical.
- Richer internal structures may be adapted into compatibility payloads for current frontend consumers.

## File-Level Refactor Plan

### Backend

#### `backend/agent_runtime_utils.py`

Reduce this file's responsibility by extracting:

- event normalization helpers
- runtime summary/detail builders
- office overview aggregation helpers
- runtime index/mapping shaping helpers

Goal: this file should stop acting as the project's all-in-one runtime engine.

#### `backend/opencode_local_watcher.py`

Refactor `_materialize()` into smaller responsibilities:

- session-family discovery and grouping
- message/part collection
- family event extraction
- synthetic office projection
- detail/mapping assembly

The watcher should remain the source of watcher-derived family discovery, but not the place where every downstream projection concern is fused together.

#### `backend/runtime_routes.py`

Keep route handlers thin and compatibility-focused. They should orchestrate calls to lineage, normalization, and projection helpers instead of encoding business logic directly.

### Frontend

#### `frontend/runtime-inspector.js`

Refactor the summary/family rendering path so it consumes structured family data instead of reconstructing relationships from mixed sources.

Required outcome:

- descendants appear in structured family sections
- descendants are selectable from the family view
- office member rendering no longer depends on raw/timeline-only presence

#### `frontend/runtime-game-bridge.js`

Keep bridge behavior simple, but align it with office member selection rules rather than ad-hoc overview filtering.

### Push Path

#### `office-agent-push.py`

Preserve lineage hints, but keep them hints only. The server remains authoritative. This path only needs adjustments required to complete the mixed-mode validation and maintain canonical behavior.

## Per-Change Completion Plan

### `add-opencode-local-watcher`

Status target: remain complete, but reduce structural debt.

What this work changes:

- keep watcher behavior intact
- split watcher materialization into smaller internal units
- ensure watcher-derived family data is easier to reuse in office projection
- avoid baking future scope-mode assumptions deeper into watcher internals

What this work does not change:

- no new scope modes
- no shift away from root session family as office identity

### `add-agent-runtime-visualization`

Status target: remain complete, but improve internal clarity.

What this work changes:

- align inspector consumption with structured office/family data
- preserve tab behavior and existing user-facing runtime inspection model
- reduce dependence on raw payloads for normal family browsing

What this work does not change:

- no product rewrite of the runtime inspector
- no incompatible endpoint redesign

### `show-full-root-session-family-in-office`

Status target: fully complete.

This work must finish the two remaining closure points.

#### A. Mixed-mode canonical office validation

Add verification for the scenario where watcher-derived lineage and explicit push coexist for the same root family.

Required result:

- one root family always resolves to one canonical office
- watcher and explicit push paths do not create separate office aggregates for the same family
- mappings and overview remain consistent

#### B. Descendant visibility and selection

Add structured family visibility so descendants are:

- visible in the office family view
- discoverable without reading raw JSON or timeline only
- selectable into runtime detail view

Required result:

- the inspector family view becomes a real browsing surface, not just a diagnostics surface

## Validation Strategy

Validation is primarily code/script-based, with targeted UI behavior checks.

### Backend-focused validation

Add or extend script/test coverage for these scenarios:

1. watcher-only root family
2. push-only root family
3. mixed watcher + explicit push for same root family
4. child/grandchild/delegated descendants appear under one canonical office
5. mappings keep canonical office identity stable

### Frontend-focused validation

Keep frontend verification lightweight but meaningful:

- office family sections render descendants from structured data
- selecting a descendant loads its detail payload
- office member and selected subject states stay consistent with current inspector behavior

### Completion criteria

This work is only complete when:

- `show-full-root-session-family-in-office` can be marked fully complete
- the three maintained changes still work with strong endpoint compatibility
- backend validations pass
- no new type/lint/runtime errors are introduced in touched files

## Future-Proofing for `add-watcher-scope-modes`

This design deliberately prepares, but does not implement, scope modes.

The key boundary is:

- **canonical office identity** answers what an office is
- **scope visibility** will later answer which offices are shown

That means future `add-watcher-scope-modes` should be able to extend:

- source discovery policy
- server aggregation policy
- office visibility filtering

without needing to redefine:

- `officeId`
- `rootSessionId`
- `serverOrigin`
- family membership semantics
- descendant visibility semantics

## Risks and Mitigations

### Risk: refactor breaks existing consumers

Mitigation: keep endpoint names and primary payload shape stable; confine most change to internal layers.

### Risk: watcher and explicit push still diverge subtly

Mitigation: add mixed-mode validation as a first-class completion gate, not as an optional script.

### Risk: descendant UI remains cosmetic

Mitigation: require selectable family members and detail navigation, not just extra labels in summary cards.

### Risk: future scope modes re-entangle identity and visibility

Mitigation: hold the architectural boundary firmly in code organization and naming.

## Recommended Implementation Order

1. Extract backend helpers to reduce oversized runtime and watcher functions.
2. Stabilize normalized run and office projection flow under strong compatibility.
3. Add mixed-mode canonical office validation.
4. Add structured descendant visibility and selection in the inspector path.
5. Re-run compatibility and verification scripts.
6. Mark the remaining OpenSpec tasks complete.

## Decision

Proceed with the medium-refactor, strong-compatibility plan described above.
