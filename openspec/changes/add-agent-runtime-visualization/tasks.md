## 1. 后端运行态适配层

- [ ] 1.1 梳理并实现 `AgentRun`、`AgentEvent`、`AgentEdge`、`AgentSummary` 的后端归一化数据结构
- [ ] 1.2 接入 opencode 的 session、child session、message parts、status 与 event 数据读取能力
- [ ] 1.3 接入 oh-my-openagent 的 `task`、`background_output`、`session_read`、`session_info` 等补充检索能力
- [ ] 1.4 实现 `backgroundTaskId ⇄ sessionId ⇄ childSessionId ⇄ AgentRunId` 的映射与缓存逻辑
- [ ] 1.5 实现后台任务状态与 session 状态不一致时的兜底校验逻辑

## 2. 运行态聚合接口

- [ ] 2.1 设计并实现可供前端消费的 Agent 运行摘要接口
- [ ] 2.2 设计并实现单个 AgentRun 详情接口，返回 Summary、Thinking、Messages、Tools、Timeline、Raw JSON 所需数据
- [ ] 2.3 设计并实现父子运行/委派关系的聚合输出结构
- [ ] 2.4 为事件流或轮询刷新提供统一的后端聚合出口，避免前端直接拼装多来源响应

## 3. 办公室总览交互升级

- [ ] 3.1 在 `frontend/game.js` 中将 Agent 渲染对象升级为可选中的运行对象
- [ ] 3.2 为办公室中的 Agent 增加点击选中、高亮与取消选中交互
- [ ] 3.3 将列表选中与画布选中联动，保持总览、列表与检查器状态一致
- [ ] 3.4 保持总览层只展示摘要信息，避免把高密度运行细节直接渲染进 Phaser 画布

## 4. Agent 运行态检查器

- [ ] 4.1 在现有 DOM 面板结构上新增或改造运行态检查器容器
- [ ] 4.2 实现 `Summary`、`Thinking`、`Messages`、`Tools`、`Timeline`、`Raw JSON` 标签页切换
- [ ] 4.3 实现长内容的折叠/展开展示，覆盖 thinking、tool result、timeline event 与 raw json
- [ ] 4.4 在检查器中展示父运行、子运行与委派关系信息
- [ ] 4.5 为无数据、加载中、状态过期或检索失败等场景补充降级展示

## 5. 验证与收尾

- [ ] 5.1 为后端适配与聚合逻辑补充最小可验证测试或校验脚本
- [ ] 5.2 验证多 Agent 总览刷新、画布点选、列表联动与检查器切换行为
- [ ] 5.3 验证工具调用、thinking、timeline、raw json 等不同数据类型在 inspector 中可正确展示
- [ ] 5.4 记录已知限制、回滚方式与后续扩展点，确保实现结果与 proposal/design/specs 一致
