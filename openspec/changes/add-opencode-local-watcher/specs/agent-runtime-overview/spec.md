## MODIFIED Requirements

### Requirement: 办公室总览必须展示可选中的 Agent 运行对象
系统 SHALL 在像素办公室总览中将每个 Agent 渲染为可选中的运行对象，而不是仅作为不可交互的状态装饰物；其中既包括显式加入的 agent，也包括以 root session 为主键自动发现的 synthetic office agents。

#### Scenario: watcher 自动发现新的 synthetic agent
- **WHEN** 后端 watcher 发现一个新的 synthetic office agent
- **THEN** 系统必须在办公室总览中将其渲染为可选中的运行对象

#### Scenario: 用户点击办公室中的 Agent
- **WHEN** 用户点击画布中的某个 Agent 对象
- **THEN** 系统必须将该对象标记为当前选中运行对象，并触发对应运行态检查器的展示或刷新

### Requirement: 总览必须持续刷新 Agent 运行摘要
系统 SHALL 持续刷新显式 agent 与 synthetic office agents 的位置、状态、名称与摘要信息，以维持“谁在做什么”的全局感知。

#### Scenario: synthetic agent 状态从 running 切换到 offline
- **WHEN** watcher 发现某个 synthetic office agent 从运行中切换为 stale/offline
- **THEN** 办公室总览必须在下一次刷新时更新其状态与摘要信息

### Requirement: 总览必须支持选中联动与高亮
系统 SHALL 在用户通过画布或列表选中任意显式 agent 或 synthetic office agent 时，保持总览、列表与检查器之间的一致选中状态。

#### Scenario: 用户从列表选中 synthetic agent
- **WHEN** 用户在 Agent 列表中选中一个 synthetic office agent
- **THEN** 系统必须在办公室总览中高亮对应对象，并在检查器中展示相同对象的详情

### Requirement: 总览不得承载高密度运行细节
系统 SHALL 将长文本思考、工具调用明细、时间线和原始 JSON 等高密度运行信息放置在检查器层，而不是直接堆叠在 Phaser 画布内。

#### Scenario: synthetic agent 拥有多条 session lineage 事件
- **WHEN** 某个 synthetic office agent 对应的 root session family 拥有大量 child session 与事件
- **THEN** 办公室总览只能展示摘要信息，完整细节必须在检查器中查看

### Requirement: 总览对象不得按名称拆分 root lineage
系统 SHALL 以 root session lineage 作为 synthetic office object 的归属基础，不得因 child/grandchild session 的名称变化而拆分多个总览对象。

#### Scenario: 同一 root lineage 下出现不同 agent 标题
- **WHEN** 某个 root session family 中不同 descendant session 产生不同 agent 标题或显示名
- **THEN** 总览必须仍显示为同一个 synthetic office object，并将名称变化视为展示层更新而非新对象
