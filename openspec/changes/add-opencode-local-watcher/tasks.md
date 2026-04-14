## 1. Watcher 数据摄取层

- [x] 1.1 设计并实现本机 opencode watcher 服务入口，支持项目级过滤与轮询/订阅调度
- [x] 1.2 接入 OpenCode 官方 session/message/children 读取面作为 watcher 首选数据源
- [x] 1.3 保留并整合本机 `opencode.db` 读取能力，作为 watcher 的增强/兜底数据源
- [x] 1.4 设计并实现 project/global SSE 的本地过滤策略，确保事件先解析 `sessionId` 再归并到 root session
- [x] 1.5 设计 overview 高频刷新与 detail 低频/按需重算的双层节奏

## 2. Synthetic Office Agent 物化

- [x] 2.1 实现 `sessionId -> rootSessionId -> officeId` 解析逻辑，生成稳定的 synthetic office identity
- [x] 2.2 实现 child session / delegation / background task 到 edge/detail 的映射逻辑
- [x] 2.3 实现 synthetic office agent 的命名、状态推断与展示摘要规则
- [x] 2.4 实现 stale/offline/grace 回收规则，避免 synthetic agent 抖动

## 3. Room 隔离与缓存模型

- [x] 3.1 实现基于 `project_id` / `directory` 的 discovery/filter guard，并以 `rootSessionId` 作为最终 office 主键
- [x] 3.2 实现 watcher 读模型缓存，不将 synthetic agents 写入 `agents-state.json`
- [x] 3.3 扩展运行态映射缓存，支持 `backgroundTaskId ⇄ sessionId ⇄ childSessionId ⇄ rootSessionId ⇄ syntheticAgentId`
- [x] 3.4 实现状态不一致兜底校验，统一修正 watcher 与会话状态差异

## 4. 后端 API 与现有适配层融合

- [x] 4.1 扩展 runtime adapter，使其同时支持显式 push 与 watcher 自动发现双通道输入，并统一按 root session 路由
- [x] 4.2 扩展 `/runtime/overview` 与相关读路径，合并显式 agent 与 synthetic office agents
- [x] 4.3 扩展 `/runtime/agents/<identifier>`，确保 synthetic office agents 也能进入完整 detail 视图
- [x] 4.4 扩展 watcher/mappings/diagnostics 输出，支持问题排查与前端调试

## 5. 前端总览与检查器适配

- [x] 5.1 在总览列表和办公室画面中展示 synthetic office agents，并与显式 agent 做可视区分
- [x] 5.2 保持 synthetic office agents 与现有 inspector 的选中、高亮与详情联动
- [x] 5.3 在前端 UI 中明确 office = root session、project/workspace = filter guard 的语义，降低“按名称或项目直接分房间”的歧义
- [x] 5.4 评估并实现 root-session office selector 或同项目多 office 切换入口（如设计确认需要）

## 6. 验证、文档与回滚准备

- [x] 6.1 为 watcher 与 synthetic materialization 增加最小可验证脚本或测试用例
- [x] 6.2 验证多 root session、child session、grandchild session、delegation、stale/offline 等关键场景
- [x] 6.3 验证“同一 root lineage 下 descendant 名称变化”不会拆分为多个 office 对象
- [x] 6.4 更新用户手册与实现说明，补充 watcher 模式、隔离语义和排障方式
- [x] 6.5 记录 watcher 模式的开关、回滚方式与已知限制，确保可安全降级回显式 push 模式
