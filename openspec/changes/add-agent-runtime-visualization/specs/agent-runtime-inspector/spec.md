## ADDED Requirements

### Requirement: 系统必须提供 Agent 运行态检查器
系统 SHALL 为当前选中的 Agent 运行对象提供专用检查器，用于查看该运行对象的结构化运行态详情。

#### Scenario: 用户选中一个 Agent 运行对象
- **WHEN** 用户选中任意 Agent 运行对象
- **THEN** 系统必须展示该对象的运行态检查器，而不是只显示静态名片信息

### Requirement: 检查器必须提供固定的运行态标签页
系统 SHALL 至少提供 `Summary`、`Thinking`、`Messages`、`Tools`、`Timeline` 与 `Raw JSON` 六类检查视图，以保证不同粒度的信息可预测地访问。

#### Scenario: 用户切换到 Tools 标签
- **WHEN** 用户打开某个 Agent 的 Tools 标签
- **THEN** 系统必须展示该运行对象关联的工具调用与结果，而不是仅显示摘要文本

### Requirement: 检查器必须支持父子关系与委派上下文展示
系统 SHALL 在检查器中展示当前运行对象与父运行、子运行或委派链路的关系信息。

#### Scenario: 当前 Agent 由父 Agent 委派产生
- **WHEN** 当前 AgentRun 存在父运行或委派来源
- **THEN** 检查器必须显示其来源关系，并允许用户识别该运行对象在多 Agent 链路中的位置

### Requirement: 检查器必须支持渐进展开
系统 SHALL 对 thinking、tool result、timeline event 与 raw json 等高噪声内容提供折叠/展开或分段展示能力，以保证可读性。

#### Scenario: Agent 拥有大量时间线事件
- **WHEN** 当前运行对象包含大量 timeline 记录
- **THEN** 检查器必须默认以摘要或折叠形式展示，并允许用户按需展开查看详细内容

### Requirement: 检查器必须允许查看原始结构化数据
系统 SHALL 允许用户查看当前运行对象的原始结构化运行数据，以支持调试和交叉验证。

#### Scenario: 用户打开 Raw JSON 标签
- **WHEN** 用户切换到 Raw JSON 标签
- **THEN** 系统必须展示与当前运行对象关联的原始结构化数据快照或事件聚合结果
