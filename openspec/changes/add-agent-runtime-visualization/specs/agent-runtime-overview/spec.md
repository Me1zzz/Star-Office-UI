## ADDED Requirements

### Requirement: 办公室总览必须展示可选中的 Agent 运行对象
系统 SHALL 在像素办公室总览中将每个 Agent 渲染为可选中的运行对象，而不是仅作为不可交互的状态装饰物。

#### Scenario: 用户点击办公室中的 Agent
- **WHEN** 用户点击画布中的某个 Agent 对象
- **THEN** 系统必须将该对象标记为当前选中运行对象，并触发对应运行态检查器的展示或刷新

### Requirement: 总览必须持续刷新 Agent 运行摘要
系统 SHALL 持续刷新 Agent 的位置、状态、名称与摘要信息，以维持“谁在做什么”的全局感知。

#### Scenario: Agent 状态从 working 切换到 error
- **WHEN** 某个 Agent 的聚合状态从工作中切换为异常
- **THEN** 办公室总览必须在下一次刷新时更新其区域、视觉状态和摘要信息

### Requirement: 总览必须支持选中联动与高亮
系统 SHALL 在用户通过画布或列表选中 Agent 运行对象时，保持总览、列表与检查器之间的一致选中状态。

#### Scenario: 用户从列表选中 Agent
- **WHEN** 用户在 Agent 列表中选中某个运行对象
- **THEN** 系统必须在办公室总览中高亮对应对象，并在检查器中展示相同对象的详情

### Requirement: 总览不得承载高密度运行细节
系统 SHALL 将长文本思考、工具调用明细、时间线和原始 JSON 等高密度运行信息放置在检查器层，而不是直接堆叠在 Phaser 画布内。

#### Scenario: Agent 存在多条 thinking 与 tool 调用
- **WHEN** 某个 Agent 拥有多条思考片段与工具调用记录
- **THEN** 办公室总览只能展示简要摘要或状态提示，完整细节必须在检查器中查看
