## MODIFIED Requirements

### Requirement: 办公室总览必须展示可选中的 Agent 运行对象
系统 SHALL 在像素办公室总览中将每个 Agent 渲染为可选中的运行对象；其中既包括显式加入的 agent，也包括 watcher 自动发现的 synthetic office agents，并且该展示必须遵循当前 watcher scope。

#### Scenario: one-server scope 中出现多个项目的 root-session offices
- **WHEN** 当前 scope 为 `one-server` 且发现多个项目的 root-session offices
- **THEN** 总览必须同时展示这些 synthetic offices，并允许前端进一步按 project/workspace 分组或切换

### Requirement: 总览必须支持选中联动与高亮
系统 SHALL 在用户通过画布、列表或 scope-aware selector 选中任意显式 agent 或 synthetic office agent 时，保持总览、列表与检查器之间的一致选中状态。

#### Scenario: 用户在不同 scope 间切换
- **WHEN** 用户切换 watcher scope
- **THEN** 系统必须重建可见 office 列表和当前选中态，而不是保留无效 selectionKey

### Requirement: 总览对象不得按名称拆分 root lineage
系统 SHALL 以 root session lineage 作为 synthetic office object 的归属基础，不得因 child/grandchild session 或跨项目/跨 server 同名对象而拆分或误合并总览对象。

#### Scenario: multi-server 模式下出现同名 office label
- **WHEN** 不同 server 的两个 office 使用相同展示名
- **THEN** 总览必须仍将其视为不同对象，并保持稳定的 identity/origin 区分
