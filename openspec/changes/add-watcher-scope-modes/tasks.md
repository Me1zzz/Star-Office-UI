## 1. Scope 模型与配置基础

- [ ] 1.1 设计并实现 watcher scope 配置结构，支持 `current-project`、`one-server`、`multi-server-aggregate`
- [ ] 1.2 明确默认 scope 为 `current-project`，并补充开关/回滚语义
- [ ] 1.3 将 scope 配置贯穿 watcher、runtime routes 与前端 selector 的基础状态模型

## 2. One-Server 模式实现

- [ ] 2.1 将当前 watcher 从 `current-project` 过滤扩展为可选的 `one-server` 发现模式
- [ ] 2.2 在 `one-server` 模式下保留 `rootSessionId -> office` 不变，并增加 project/workspace grouping 读模型
- [ ] 2.3 验证 `one-server` 模式下同一 server 中多个项目的 root sessions 不会被错误合并
- [ ] 2.4 扩展前端 selector，支持在 `one-server` 模式下按 project/workspace 分组与 root-session office 切换

## 3. Multi-Server Aggregate 设计与基础设施

- [ ] 3.1 定义 multi-server aggregate 的 `serverOrigin` 命名空间模型
- [ ] 3.2 设计并实现 server registry / connection model，用于登记多个 OpenCode server 来源
- [ ] 3.3 设计多 server `/session` 快照与 `/global/event` 流的聚合输入层
- [ ] 3.4 设计 `serverOrigin + project/workspace + rootSessionId` 的冲突隔离与 UI key 规则

## 4. Scope-Aware Runtime 与 UI 融合

- [ ] 4.1 扩展 runtime overview/detail/mappings，使其显式暴露当前 scope 与 origin 语义
- [ ] 4.2 实现前端三层导航：scope selector、project/workspace grouping、office selector
- [ ] 4.3 在 `current-project` 模式下隐藏不必要的 grouping 复杂度，保持当前体验简洁
- [ ] 4.4 在 `multi-server-aggregate` 模式下展示 serverOrigin 归属，避免跨 server 混淆

## 5. 验证、文档与迁移

- [ ] 5.1 验证三种 scope 下的 office 可见性与隔离语义
- [ ] 5.2 验证同名 project/path/session 在 multi-server 模式下不会发生冲突合并
- [ ] 5.3 更新 watcher SOP、用户手册与实现说明，明确三档 scope 的含义与限制
- [ ] 5.4 记录 default scope、升级路径与回滚方式，确保从 current-project 平滑迁移
