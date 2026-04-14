## ADDED Requirements

### Requirement: 系统必须自动发现本机 opencode session family
系统 SHALL 在不依赖手动 push 的前提下，自动发现与当前工作区/项目相关的本机 opencode session family，并将其纳入运行态读模型。

#### Scenario: 本机存在与当前项目相关的 root session
- **WHEN** watcher 检测到与当前项目 `project_id` 或目录匹配的 root session
- **THEN** 系统必须将该 session family 纳入本地 runtime 发现结果

### Requirement: 系统必须支持 session lineage 增量跟踪
系统 SHALL 跟踪 root session、child session、delegation 与相关事件变化，并支持以增量方式刷新 watcher 结果。

#### Scenario: root session 产生新的 child session
- **WHEN** 某个 root session 新增 child session
- **THEN** 系统必须在下一轮 watcher 刷新中识别该 lineage 变化并更新对应读模型

### Requirement: 系统必须提供 watcher 读模型与诊断输出
系统 SHALL 暴露 watcher 发现结果、映射状态与基础诊断信息，以便前端展示和问题排查。

#### Scenario: 用户查看 watcher 诊断状态
- **WHEN** 客户端请求 watcher 相关读模型或诊断信息
- **THEN** 系统必须返回当前已发现的 session family、synthetic identity、状态摘要及必要的 watcher 元数据
