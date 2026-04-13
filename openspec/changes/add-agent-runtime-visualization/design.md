## Context

Star-Office-UI 当前是一个 Flask + HTML/Phaser 驱动的像素办公室产品，核心能力是通过 `/status` 与 `/agents` 轮询展示 Agent 的位置、状态与简要说明。现有前端擅长表达“总览感知”，但并不具备完整的运行态检查能力；现有后端也主要围绕 `state/detail/progress` 快照工作，而非围绕 session、事件流、工具调用或子 Agent 关系工作。

与此同时，opencode 已经提供了 session、child session、message parts、status 与 SSE event 等运行时数据面，oh-my-openagent 则在此基础上增加了 `task`、`background_output`、`session_read`、`session_info` 等面向委派与后台执行的编排能力。这意味着项目不需要重新发明一套独立的 tracing 平台，而应在 Star-Office-UI 现有可视化壳之上增加一层运行态适配与检查器结构。

本设计需要同时满足三个约束：
- 保留 Star-Office-UI 现有“像素办公室总览”的产品识别度。
- 提供足够高密度的运行态细节，支持查看 thinking、tools、text、timeline、raw json。
- 在不把前端整体重写为新框架的前提下，最小化对现有 Phaser/HTML 架构的破坏。

## Goals / Non-Goals

**Goals:**
- 将办公室中的 Agent 从“静态状态对象”升级为“可选中的运行对象”，支持总览与检查联动。
- 建立统一的运行态数据模型，将 opencode session/event/message parts 与 OMO background task/session 检索结果归一为前端可消费实体。
- 提供基于 DOM 的运行态检查器，支持摘要、思考、文本、工具、时间线与原始数据视图。
- 支持父子 Agent、委派链路与 child session 关系的表达，避免多 Agent 运行被压扁成单一状态点。

**Non-Goals:**
- 不在本次设计中将 Star-Office-UI 全量迁移为 React、Vue 或其他 SPA 架构。
- 不在本次设计中替代 opencode 或 oh-my-openagent 的原生运行与存储逻辑。
- 不在本次设计中实现完整的“图编辑器”或可视 DAG 编排器。
- 不把所有运行态细节直接渲染进 Phaser 画布；画布只负责总览与选中入口。

## Decisions

### 1. 采用“双层 UI”：Phaser 总览 + DOM 检查器

**决策**：保留 `frontend/game.js` 中的 Phaser 办公室场景作为全局总览层，将 Agent 在办公室中的存在、位置与选中状态继续放在画布中；把高密度运行态信息放入 DOM 面板中，复用现有 `#guest-agent-panel`、`#asset-drawer` 或新增同级 inspector drawer/panel。

**原因**：
- Phaser 适合表达空间关系、状态区域与“谁在忙什么”的全局感知，但不适合承载长文本、折叠区、时间线、原始 JSON 与工具调用明细。
- `frontend/index.html` 已经具备成熟的抽屉、卡片、折叠与列表样式，可低成本复用于 inspector。
- 这条路径能在保持像素办公室品牌特征的同时，降低前端架构级重写成本。

**备选方案与放弃原因**：
- **方案 A：全部细节都做进 Phaser 气泡或浮层**：信息密度不足，交互复杂且移动端体验差。
- **方案 B：新建独立页面或独立前端应用**：实现清晰，但会割裂总览与检查体验，也增加维护成本。

### 2. 以 OpenCode 运行数据为主真相源，以 OMO 为编排补充层

**决策**：运行态主数据以 opencode 的 session、child session、messages、parts、status、event 为核心；oh-my-openagent 的 `task`、`background_output`、`session_read`、`session_info` 用于补充后台任务、委派关系和聚合后的会话输出。

**原因**：
- OpenCode 已经有更底层、更原生的运行面模型，适合作为统一的 runtime data plane。
- OMO 的优势在于多 agent 编排与后台任务抽象，但其状态可能存在延迟或需要结合 session 工具交叉校验。
- 用 OpenCode 做真相源、OMO 做编排补充，可以减少对上层格式化输出的依赖，并保留实时性。

**备选方案与放弃原因**：
- **方案 A：只依赖 OMO `background_output`**：对于最终 UI 足够直观，但粒度和稳定性不足，且不适合作为全部运行态真相源。
- **方案 B：只依赖 OpenCode，不引入 OMO 概念**：会丢失对委派 agent、后台任务与 orchestration 元数据的直接表达。

### 3. 新增 Star-Office 运行态适配层，统一归一化实体

**决策**：在 Star-Office-UI 后端新增运行态适配层，将外部数据归一化为以下实体：
- `AgentRun`：单个 agent 或子 agent 的一次运行实例
- `AgentEvent`：thinking、text、tool_call、tool_result、status、error 等事件
- `AgentEdge`：父子运行、委派、handoff 等关系边
- `AgentSummary`：用于画布与列表快速展示的聚合信息

**原因**：
- 当前项目的数据模型只够表达 presence，不够表达 runtime lineage。
- 前端需要稳定结构，而不是直接消费多个异构来源的响应格式。
- 统一实体能支持总览、检查器、时间线与原始视图之间的一致跳转。

**备选方案与放弃原因**：
- **方案 A：前端直接分别请求 opencode/OMO 各自接口**：会把归一、兜底、缓存和降级逻辑压到前端，增加耦合。
- **方案 B：只存聚合快照，不保留事件层**：无法支持 timeline、tool 明细与 thinking 逐步展开。

### 4. 将“选中对象”定义为运行对象，而非仅角色对象

**决策**：前端画布点击不只表示“选中某个角色”，而是选中该角色当前绑定的 `AgentRun`。若该 agent 当前存在父/子运行、后台任务或 child session，则 inspector 展示运行上下文与关系信息，而不仅是头像和状态说明。

**原因**：
- 用户要查看的是运行态，而不是单纯的角色名片。
- 这样可以自然承接 Timeline、Tools、Thinking 等 inspector tab。

**备选方案与放弃原因**：
- **方案 A：角色详情页只展示静态 agent 信息**：无法满足目标场景。

### 5. Inspector 采用固定标签页结构，支持渐进展开

**决策**：Inspector 最少包含以下标签：`Summary`、`Thinking`、`Messages`、`Tools`、`Timeline`、`Raw JSON`。默认打开 `Summary`，其余标签按需切换；工具结果、thinking 片段与 timeline 行支持折叠/展开。

**原因**：
- 外部参考表明，多 Agent / 多工具运行极易产生噪音，需要渐进披露。
- 固定标签有利于前后端契约与测试覆盖。

**备选方案与放弃原因**：
- **方案 A：单滚动面板塞入所有内容**：可实现但可读性差，无法形成稳定信息结构。

## Risks / Trade-offs

- **[风险] 外部运行态来源存在多套 ID 与状态口径** → **缓解**：适配层统一维护 `backgroundTaskId ⇄ sessionId ⇄ childSessionId ⇄ AgentRunId` 的映射，并对状态做归一。
- **[风险] OMO `background_output` 状态可能滞后于真实完成状态** → **缓解**：以 `session_info` / `session_read` 作为补充校验源，不把单一任务状态作为唯一事实。
- **[风险] 事件流可能只提供全局 SSE，缺少 session 级订阅** → **缓解**：后端先做基于 `sessionId` 的事件过滤与缓存，再暴露给前端。
- **[风险] 当前前端是无框架架构，高复杂度状态渲染容易失控** → **缓解**：把高复杂度状态集中在后端聚合与单一 inspector 状态对象，避免在 Phaser 场景里做复杂数据编排。
- **[风险] Thinking / tool output 内容较长，直接渲染可能影响性能与可读性** → **缓解**：默认只展示摘要与最近片段，完整内容通过折叠或分页加载展开。

## Migration Plan

1. 在后端新增运行态适配与聚合接口，但不影响现有 `/status` 与 `/agents` 能力。
2. 在前端先增加“Agent 可点击 + 当前选中状态”，仍保留现有办公室总览行为。
3. 接入基础 inspector，先消费聚合摘要，再逐步增加 thinking、tools、timeline 与 raw json 标签。
4. 在确保新 inspector 可用后，再补充父子关系、child session 展示与后台任务映射。
5. 如需回滚，可关闭新接口与新面板入口，恢复到仅使用现有 `/status` 与 `/agents` 的总览模式。

## Open Questions

- 是否需要在首版中同时提供“画布点选”和“列表选中”两种入口，还是先以列表驱动画布高亮为主？
- Thinking 内容是否需要额外做脱敏/权限控制，避免把敏感推理直接暴露在 UI 中？
- Timeline 首版是否展示全量事件，还是只展示关键事件（状态切换、tool call、tool result、error）？
- Inspector 是复用现有 `#asset-drawer`，还是独立新增 `runtime-drawer`，以避免与装修功能耦合？
