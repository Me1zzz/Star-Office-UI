## MODIFIED Requirements

### Requirement: 系统必须统一按 canonical lineage 归一运行态数据
系统 SHALL 在 runtime adapter 层统一处理 watcher 自动发现、显式 push、以及后续 runtime enrichers 的 lineage / office 归一逻辑，确保所有进入运行态视图的数据都具备一致的 canonical `rootSessionId` 与 `officeId` 语义。

#### Scenario: explicit runtime 仅包含 child sessionId
- **WHEN** 某个显式 pushed runtime 只包含 child `sessionId` 而未直接携带 `rootSessionId`
- **THEN** runtime adapter 必须通过 canonical lineage resolver 将其追溯到正确的 root office

#### Scenario: watcher 与 explicit runtime 信息同时存在
- **WHEN** 系统同时拥有 watcher-derived lineage 事实与显式 runtime payload
- **THEN** runtime adapter 必须以统一 canonical lineage 结果构建运行态，而不是分别输出两个互相冲突的 office 语义

### Requirement: 运行态 detail 必须保留完整 office context
系统 SHALL 让任意运行对象的 detail 响应都带有完整 office context，包括 subject、office summary、lineage relationships 与 canonical identity fields。

#### Scenario: 用户请求 explicit descendant 的 detail
- **WHEN** 用户通过 `selectionKey`、`runId` 或 `sessionId` 选中某个 explicit descendant
- **THEN** detail 响应必须同时返回该对象的 canonical office 归属与 family context，而不是只返回孤立的单对象事件流

#### Scenario: mixed-mode detail 读取 watcher facts
- **WHEN** detail 构建过程中 watcher 已拥有更高置信度的 lineage 事实
- **THEN** runtime adapter 必须优先使用这些 canonical lineage facts，而不是简单保留较弱的 push hint
