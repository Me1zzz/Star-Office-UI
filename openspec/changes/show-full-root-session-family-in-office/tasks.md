## 1. Canonical lineage 与读模型基础设施

- [x] 1.1 设计并实现统一的后端 canonical lineage resolver，收束 watcher、session tree、push hint、runtime mappings 等来源
- [x] 1.2 设计并实现 normalized run / office member / office aggregate 三层读模型结构
- [x] 1.3 统一定义 `serverOrigin`、`officeId`、`officeLocalId`、`rootSessionId`、`officeRole`、`lineageDepth`、`lineageConfidence` 等 canonical 字段
- [x] 1.4 设计 lineage unresolved / provisional / resolved 的状态与纠正机制

## 2. watcher 与 explicit push 的统一归一

- [x] 2.1 将 `backend/opencode_local_watcher.py` 中的 root lineage 解析逻辑迁移或复用到统一 resolver/source 层
- [x] 2.2 扩展显式 push 路径，使 `/join-agent` / `/agent-push` / `office-agent-push.py` 支持 canonical lineage hints 但不承担最终归属裁定
- [x] 2.3 升级 `backend/agent_runtime_utils.py`，让 explicit runtime summary/detail 统一补齐 canonical `rootSessionId` 与 `officeId`
- [x] 2.4 解决 explicit path 当前只查一层 child session 的问题，支持 full descendant lineage 追溯与 family 聚合

## 3. API 与 mappings 升级

- [x] 3.1 扩展 `/runtime/overview`，输出 office-aware 的 `offices` 与成员级 items
- [x] 3.2 扩展 `/runtime/agents/<identifier>`，输出 `subject + office + lineage + events + raw` 结构
- [x] 3.3 升级 `/runtime/mappings` 与 `runtime-mappings.json` 为 canonical identity snapshot，而不是简单优先级回退 map
- [x] 3.4 保持旧字段兼容，并为 mixed-mode / provisional lineage 提供清晰的诊断输出

## 4. Office family 前端可见性

- [x] 4.1 升级前端 office selector，使其消费 office aggregates 而不是从 items 中自行推断 office
- [x] 4.2 升级 guest list / office occupants 渲染，使当前 office 内的 family members 真正可见
- [x] 4.3 升级 runtime inspector，新增 office family、ancestors、descendants、delegated lineage 等结构化视图
- [x] 4.4 升级画布桥接与渲染逻辑，明确 active members、family browser 与当前选中对象之间的联动规则

## 5. 兼容、验证与文档

- [x] 5.1 为 watcher-only、push-only、mixed-mode、grandchild lineage、delegation、multi-server namespace 等关键场景补齐验证脚本或测试
- [ ] 5.2 验证同一 root family 在 watcher 与 explicit push 并存时不会被拆分成多个 office
- [ ] 5.3 验证 descendants 不再只存在于 raw/timeline，而能在 office family 视图中被发现与选中
- [x] 5.4 更新实现文档、SOP 与用户手册，明确 canonical office identity、scope 语义、serverOrigin namespace 与回滚策略
