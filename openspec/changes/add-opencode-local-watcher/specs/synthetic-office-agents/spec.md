## ADDED Requirements

### Requirement: 系统必须将本地 session family 物化为 synthetic office agents
系统 SHALL 将本机自动发现的 root session family 物化为办公室中的 synthetic office agents，而无需显式 `/join-agent` 或 `/agent-push`。

#### Scenario: watcher 发现新的 root session family
- **WHEN** watcher 发现一个新的 root session family
- **THEN** 系统必须在办公室总览中生成一个对应的 synthetic office agent

### Requirement: synthetic office agents 必须使用稳定主键
系统 SHALL 为 synthetic office agents 使用稳定且可复算的 identity key，并保证该 identity 不依赖瞬时展示名称。

#### Scenario: session title 改变但 lineage 未变
- **WHEN** 同一个 root session family 的展示名称发生变化
- **THEN** 系统不得创建新的 synthetic office agent，而必须沿用原有 identity

#### Scenario: descendant agent 标签变化
- **WHEN** 同一个 root session family 下的 child/grandchild session 使用不同的 agent 标签或标题
- **THEN** 系统不得据此创建新的 synthetic office agent，而必须继续映射到同一个 root-session-based identity

### Requirement: synthetic office agents 必须支持状态回收与降级
系统 SHALL 为自动发现的 synthetic office agents 提供 stale/offline/grace 规则，避免对象闪烁或过早回收。

#### Scenario: 某个 synthetic agent 暂时停止更新
- **WHEN** synthetic office agent 在短时间内没有新的 session/event 更新
- **THEN** 系统必须先将其降级为 stale/offline 状态，并在 grace period 后再考虑回收
