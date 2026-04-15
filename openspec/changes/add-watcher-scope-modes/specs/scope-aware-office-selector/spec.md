## ADDED Requirements

### Requirement: 前端必须提供 scope-aware selector 结构
系统 SHALL 在 watcher 扩展模式下提供至少三层导航能力：scope 选择、project/workspace 分组、root-session office 选择。

#### Scenario: 用户切换 watcher scope
- **WHEN** 用户在前端切换 watcher scope
- **THEN** 系统必须更新当前候选 office 集合与分组结构，而不是只切换单一 office 对象

### Requirement: current-project 模式下不得暴露不必要的多层 selector 噪音
系统 SHALL 在 `current-project` scope 下隐藏或弱化不必要的 project/workspace 分组层级，以保持当前默认体验简洁。

#### Scenario: 当前 scope 为 current-project
- **WHEN** 当前 watcher scope 为 `current-project`
- **THEN** 前端必须允许用户直接在 root-session offices 之间切换，而不强制展示冗余的 project/workspace grouping selector

### Requirement: one-server 模式下必须支持 project/workspace 分组
系统 SHALL 在 `one-server` scope 下支持按 `projectID` 或 `directory` 对 root-session offices 进行分组展示。

#### Scenario: 一个 server 中存在多个项目
- **WHEN** 用户切换到 `one-server` scope 且当前 server 中存在多个项目的 root sessions
- **THEN** 前端必须提供 project/workspace 级别的分组或过滤入口

### Requirement: multi-server-aggregate 模式下必须展示 server-origin 语义
系统 SHALL 在 `multi-server-aggregate` scope 下让用户能够识别当前 office 属于哪个 server origin。

#### Scenario: 用户浏览聚合后的 office 列表
- **WHEN** 当前 scope 为 `multi-server-aggregate`
- **THEN** 前端必须在 selector、标签或元数据中显示 office 的 server-origin 归属
