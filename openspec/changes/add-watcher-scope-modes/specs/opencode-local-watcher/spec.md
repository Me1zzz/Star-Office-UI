## MODIFIED Requirements

### Requirement: 系统必须自动发现本机 opencode session family
系统 SHALL 根据当前 watcher scope 自动发现本机或配置来源中的相关 opencode session family，并将其纳入运行态读模型。

#### Scenario: watcher 运行在 current-project scope
- **WHEN** watcher 运行在 `current-project` scope
- **THEN** 系统必须仅发现与当前项目 `project_id` 或 `directory` 匹配的 session family

#### Scenario: watcher 运行在 one-server scope
- **WHEN** watcher 运行在 `one-server` scope
- **THEN** 系统必须发现当前连接 server 中可见的 root session families，而不局限于当前项目

#### Scenario: watcher 运行在 multi-server-aggregate scope
- **WHEN** watcher 运行在 `multi-server-aggregate` scope
- **THEN** 系统必须从多个配置来源中发现 root session families，并保留 server-origin 维度

### Requirement: 系统必须支持 session lineage 增量跟踪
系统 SHALL 跟踪 root session、child session、delegation 与相关事件变化，并支持以增量方式刷新 watcher 结果。

#### Scenario: one-server scope 中收到非当前项目事件
- **WHEN** watcher 运行在 `one-server` scope 且接收到属于其他项目的事件
- **THEN** 系统必须根据 scope 规则保留该事件并正确归并到对应 root session

### Requirement: 系统必须提供 watcher 读模型与诊断输出
系统 SHALL 暴露 watcher 发现结果、映射状态与基础诊断信息，以便前端展示和问题排查，并能反映当前 watcher scope 与 server-origin 语义。

#### Scenario: 客户端查看 watcher 诊断状态
- **WHEN** 客户端请求 watcher 相关读模型或诊断信息
- **THEN** 系统必须返回当前 scope、发现结果、synthetic identity、以及必要的 origin/scope 元数据
