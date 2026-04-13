## ADDED Requirements

### Requirement: 系统必须归一化外部运行态数据源
系统 SHALL 将 opencode 与 oh-my-openagent 提供的会话、事件、消息分片、后台任务和关系信息归一化为统一的运行态实体模型。

#### Scenario: 运行数据来自多个外部来源
- **WHEN** 系统同时接收到 opencode session 数据与 OMO background task 数据
- **THEN** 系统必须将其归并为统一的内部运行实体，而不是直接把异构结构暴露给前端

### Requirement: 系统必须维护任务与会话的关联关系
系统 SHALL 维护 `backgroundTaskId`、`sessionId`、`childSessionId` 与内部运行对象标识之间的映射关系，用于支撑多 Agent 关系展示与检查。

#### Scenario: 子 Agent 在新 session 中运行
- **WHEN** 某个委派 Agent 产生新的 child session
- **THEN** 系统必须能够将该 child session 关联到对应父运行对象，并为前端提供可追踪的关系信息

### Requirement: 系统必须输出可驱动总览与检查器的聚合视图
系统 SHALL 提供既可用于总览渲染，也可用于检查器展示的聚合运行视图，而不是要求前端自行拼装所有原始来源。

#### Scenario: 前端请求当前 Agent 运行摘要
- **WHEN** 前端请求某个 Agent 的当前运行摘要
- **THEN** 系统必须返回足以驱动总览与检查器初始状态的聚合结构

### Requirement: 系统必须对状态不一致进行兜底校验
系统 SHALL 在后台任务状态、会话状态或消息事件出现延迟或不一致时，采用补充检索机制校验当前运行对象的真实状态。

#### Scenario: background task 仍显示 running 但 session 已完成
- **WHEN** 后台任务状态与 session 检索结果不一致
- **THEN** 系统必须根据补充检索结果纠正当前运行对象的聚合状态，而不是持续展示过期状态

### Requirement: 系统必须支持事件级运行态表达
系统 SHALL 将 thinking、text、tool_call、tool_result、status、error 等事件表达为统一事件类型，以支撑时间线与分类检查视图。

#### Scenario: 外部来源返回消息分片与工具输出
- **WHEN** 系统接收到消息文本片段和工具输出结果
- **THEN** 系统必须将其映射到统一事件类型，并允许前端按 Thinking、Messages、Tools 或 Timeline 视图消费
