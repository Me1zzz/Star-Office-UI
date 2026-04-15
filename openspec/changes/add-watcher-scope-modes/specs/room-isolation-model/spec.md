## MODIFIED Requirements

### Requirement: room 边界必须以 root session 为主键
系统 SHALL 以 `rootSessionId` 作为 watcher-derived office 的 canonical identity，并仅将 project/workspace 作为 discovery/filter guard，而不是作为最终房间主键。

#### Scenario: 当前 scope 为 current-project
- **WHEN** watcher 运行在 `current-project` scope
- **THEN** 系统必须在当前项目范围内按 `rootSessionId` 生成 office，而不是按项目本身直接生成单一房间

#### Scenario: 当前 scope 为 one-server
- **WHEN** watcher 运行在 `one-server` scope 且发现多个项目的 root sessions
- **THEN** 系统必须仍然按各自 `rootSessionId` 生成多个 office，而不是按 server 或 project 合并成单一房间

### Requirement: visible office agent 边界必须以 root session family 为主
系统 SHALL 默认以 root session family 作为 synthetic office agent 的归属边界，child session 仅作为关系和细节补充展示。

#### Scenario: child session 只是 delegated work hop
- **WHEN** child session 仅作为 root session 的 delegation hop 出现
- **THEN** 系统必须默认将其作为 root family 的 edge/detail 展示，而不是独立房间

### Requirement: 系统不得按 agent 名称或标题决定 office 归属
系统 SHALL NOT 使用 agent 显示名、session title、tool 名称或其他展示层字段作为 office 分组或切换的 canonical key。

#### Scenario: scope 扩展后出现不同项目的同名 agent
- **WHEN** 更高 scope 下出现不同项目或不同 server 的同名 agent/session title
- **THEN** 系统不得因此误合并 office，而必须继续按 root session lineage 与 origin 规则划分
