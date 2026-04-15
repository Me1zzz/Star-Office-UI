## MODIFIED Requirements

### Requirement: 系统必须在像素办公室总览中展示 office-aware 运行对象
系统 SHALL 在像素办公室总览中将运行对象组织为 office-aware 视图，而不是仅将显式 agent 与 synthetic office agents 简单并列。总览必须同时支持 office 级对象、office family 成员对象，以及对当前 watcher scope 下可见 office 的选择与切换。

#### Scenario: 同一 office 下存在 synthetic root 与 explicit descendants
- **WHEN** watcher 自动发现的 synthetic root office 与多个显式 pushed descendants 最终归属于同一个 `rootSessionId`
- **THEN** 总览必须将它们呈现为同一个 office family，而不是拆成多个互不相关的顶层房间对象

#### Scenario: 用户按 office 过滤总览
- **WHEN** 用户选择某个 office
- **THEN** 总览必须展示该 office 的 canonical family members，并保持 selector、列表、画布与 detail 之间的 office 语义一致

### Requirement: 系统必须在总览中保留 descendant 可见性
系统 SHALL 在总览或与总览联动的 family browser 中保留 descendant 可见性，使 child / grandchild / delegated descendants 不再只存在于 raw/timeline 细节中。

#### Scenario: office family 含多个 descendants
- **WHEN** 某个 office family 包含多个 child、grandchild 或 delegated descendants
- **THEN** 总览必须允许用户看到这些 descendants 的存在、层级或角色，而不是仅显示一个 root 对象后将其余成员隐藏在不可见数据中

#### Scenario: descendant 不是当前选中对象
- **WHEN** 某个 descendant 处于当前 office 中但不是当前 detail 选中对象
- **THEN** 总览仍必须允许用户发现并切换到该 descendant 的 detail 视图
