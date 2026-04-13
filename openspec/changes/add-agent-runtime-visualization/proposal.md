## Why

Star-Office-UI 当前只能展示 Agent 的粗粒度状态与位置，适合“谁在忙什么”的总览，但无法回答“这个 Agent 现在在想什么、刚刚调用了什么工具、子 Agent 是怎么分叉出来的、这次运行的上下文是什么”等运行态问题。随着项目希望接入 opencode 与 oh-my-openagent，仅靠 `state/detail` 已不足以支撑多 Agent 运行可视化与调试，因此需要把现有像素办公室升级为“总览 + 检查器”的运行态可视化产品。

## What Changes

- 保留现有像素办公室作为全局总览层，并将画面中的 Agent 对象升级为可选中的运行对象。
- 新增 Agent 运行态检查能力，支持查看每个 Agent 的摘要、思考、文本输出、工具调用、时间线与原始结构化数据。
- 新增 opencode + oh-my-openagent 适配层，用于统一采集 session、child session、background task、message parts 与事件流，并归一成前端可消费的运行实体。
- 新增运行关系表达，支持展示父子 Agent、委派链路、handoff/child session 等关系。
- 新增 capability specs，明确总览交互、运行态数据模型与检查器行为的需求边界，为后续实现提供契约。

## Capabilities

### New Capabilities
- `agent-runtime-overview`: 像素办公室中的 Agent 运行对象展示、选中交互与总览刷新行为。
- `agent-runtime-inspector`: Agent 运行态检查器，覆盖摘要、思考、文本、工具、时间线与原始数据视图。
- `agent-runtime-adapter`: 对接 opencode 与 oh-my-openagent 的运行数据适配、归一化与关系映射能力。

### Modified Capabilities
- 无

## Impact

- 前端：`frontend/game.js`、`frontend/index.html`，以及与访客列表、右侧抽屉、画布点击交互相关的页面结构。
- 后端：`backend/app.py` 及新增运行态聚合接口/适配逻辑。
- 集成面：opencode 的 session/message/event 能力，以及 oh-my-openagent 的 task/background/session 检索能力。
- 数据模型：从当前 `state/detail/progress` 快照扩展为 `AgentRun / AgentEvent / AgentEdge` 等运行态实体。
