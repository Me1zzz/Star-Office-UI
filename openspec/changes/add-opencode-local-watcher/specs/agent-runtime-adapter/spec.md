## MODIFIED Requirements

### Requirement: 系统必须归一化外部运行态数据源
系统 SHALL 将 opencode 与 oh-my-openagent 提供的会话、事件、消息分片、后台任务和关系信息归一化为统一的运行态实体模型，并支持 watcher 自动发现的本地 session family 作为输入来源。

#### Scenario: watcher 自动发现新的本地 session family
- **WHEN** watcher 发现与当前项目相关的本地 session family
- **THEN** 系统必须将其归一化为统一的内部运行实体，而不是要求前端直接处理原始 session/message/part 数据

### Requirement: 系统必须维护任务与会话的关联关系
系统 SHALL 维护 `backgroundTaskId`、`sessionId`、`childSessionId`、`rootSessionId` 与内部运行对象标识之间的映射关系，用于支撑多 Agent 关系展示与检查。

#### Scenario: synthetic agent 对应的 child session 新增 delegation
- **WHEN** 某个 synthetic office agent 对应的 session family 产生新的 delegated child session
- **THEN** 系统必须更新其内部映射关系，并允许前端追踪该关系

#### Scenario: 事件仅携带 descendant sessionId
- **WHEN** watcher 接收到一个仅携带 descendant `sessionId` 的事件或更新
- **THEN** 系统必须先将其解析到 `rootSessionId`，再映射到正确的 office 与 synthetic agent

### Requirement: 系统必须输出可驱动总览与检查器的聚合视图
系统 SHALL 提供既可用于总览渲染，也可用于检查器展示的聚合运行视图，而不是要求前端自行拼装所有原始来源；该聚合视图必须同时覆盖显式 agent 与 watcher 自动发现的 synthetic office agents。

#### Scenario: 前端请求 synthetic agent 的运行摘要
- **WHEN** 前端请求某个 synthetic office agent 的运行摘要
- **THEN** 系统必须返回足以驱动总览与检查器初始状态的聚合结构

### Requirement: 系统必须对状态不一致进行兜底校验
系统 SHALL 在后台任务状态、会话状态或 watcher 发现状态出现延迟或不一致时，采用补充检索机制校验当前运行对象的真实状态。

#### Scenario: background task 显示 running 但 session family 已无后续更新
- **WHEN** synthetic office agent 的后台任务状态仍为 running，但 session lineage 显示更晚的完成性事件
- **THEN** 系统必须据此纠正聚合状态，而不是持续展示过期状态

### Requirement: 系统必须支持事件级运行态表达
系统 SHALL 将 thinking、text、tool_call、tool_result、status、error 等事件表达为统一事件类型，以支撑时间线与分类检查视图，并支持从 watcher 自动发现路径进入相同的事件模型。

#### Scenario: watcher 从本地 part 数据中识别 reasoning 与 tool 事件
- **WHEN** watcher 从本地 opencode parts 中发现 reasoning 和 tool 执行信息
- **THEN** 系统必须将其映射为统一事件类型，供前端按 Thinking、Messages、Tools 或 Timeline 视图消费

### Requirement: 系统不得依赖未文档化的 session 级 SSE 过滤作为唯一主路径
系统 SHALL 以官方已文档化的 session/children/message 与 project/global SSE 数据面为主路径；任何 session 级 SSE 过滤能力只能作为 opportunistic 优化，而不能成为唯一依赖。

#### Scenario: session 级 SSE 过滤不可用
- **WHEN** 当前环境中不存在稳定可用的 session 级 SSE 过滤能力
- **THEN** 系统仍必须通过 project/global SSE 与本地 session lineage 解析完成 `sessionId -> rootSessionId -> office` 路由
