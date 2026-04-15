# Agent Runtime Visualization 使用手册（含操作 SOP 与问题排查）

本文档用于指导你从零开始启动 Star-Office-UI 的 Agent Runtime Visualization 功能，并实际查看 agent 的运行态信息。

文档包含以下内容：

- 启动前准备
- 启动 Star-Office-UI
- 打开办公室页面
- 让 agent 接入办公室
- 查看 runtime 可视化
- 后端 API 如何直接使用
- 当前数据来源说明
- 详细操作 SOP
- 常见问题与排查方法

---

## 1. 启动前准备

### 1.1 确认项目根目录

项目根目录应为：

```powershell
C:\project\code\AI\Star-Office-UI
```

后续所有命令默认都在此目录执行。

### 1.2 安装 Python 依赖

项目后端至少依赖：

- `flask`
- `pillow`

安装方式：

```powershell
python -m pip install -r "backend/requirements.txt"
```

如果你用 `py` 启动 Python：

```powershell
py -3 -m pip install -r "backend/requirements.txt"
```

### 1.3 可选：确认 opencode CLI 可用

本项目的真实运行态数据会优先尝试读取本机 `opencode.db`。

先确认 `opencode` 已安装：

```powershell
opencode --version
```

如果能输出版本号，说明本机 `opencode` CLI 可用。

### 1.4 可选：确认仓库已绑定 opencode project

仓库通常包含：

```powershell
.git\opencode
```

查看内容：

```powershell
Get-Content ".git\opencode"
```

该值通常是当前项目对应的 `project_id`，后端会用它自动推断当前项目最近的根 session。

---

## 2. 启动 Star-Office-UI

### 2.1 启动后端服务

在项目根目录执行：

```powershell
python "backend/app.py"
```

或者：

```powershell
py -3 "backend/app.py"
```

启动成功后，Flask 服务会开始监听端口。默认通常是：

```text
http://127.0.0.1:19000
```

### 2.2 如果启动时报 `No module named 'flask'`

执行：

```powershell
python -m pip install flask pillow
```

然后重新启动：

```powershell
python "backend/app.py"
```

---

## 3. 打开办公室页面

浏览器打开：

```text
http://127.0.0.1:19000
```

你会看到：

- 中间：像素办公室主画面
- 下方或右侧：访客列表
- 新增：运行检查器（Runtime Inspector）

即使还没有外部 agent 接入，你通常也能先看到主办公室和检查器框架。

---

## 4. 让 agent 接入办公室

有两种方式：

- 方式 A：手动 join
- 方式 B：使用 `office-agent-push.py` 自动 join 并持续 push

推荐优先使用 **方式 B**，因为它会自动附带 runtime 元数据。

### 4.1 方式 A：手动 join

#### 第一步：打开 join 页面

```text
http://127.0.0.1:19000/join
```

#### 第二步：填写信息

你需要填写：

- 名字
- join key

#### 第三步：点击加入

加入成功后，这个 agent 会进入办公室。

注意：

- 这种方式主要是“注册进入办公室”
- 真正持续同步状态与 runtime，仍建议后续用 push 脚本

### 4.2 方式 B：使用 `office-agent-push.py`

这是更推荐的方式。

#### 第一步：设置环境变量

在 PowerShell 中设置：

```powershell
$env:OFFICE_URL="http://127.0.0.1:19000"
$env:OFFICE_AGENT_NAME="Demo-Agent"
$env:OFFICE_JOIN_KEY="你的 join key"
```

#### 第二步：运行推送脚本

```powershell
python "office-agent-push.py"
```

这个脚本会自动：

1. join 办公室
2. 读取本地状态
3. 尝试从本机 `opencode.db` 发现最近 session
4. 把 runtime 元数据一起推送到后端

通常会上报以下信息（如果本机能识别到）：

- `sessionId`
- `runId`
- `parentRunId`
- `projectId`

#### 第三步：回到办公室页面观察

回到：

```text
http://127.0.0.1:19000
```

你应该能看到：

- 访客列表里出现该 agent
- 办公室画面里出现该对象
- 运行检查器可以查看其运行态

---

## 5. 查看 runtime 可视化

### 5.1 从访客列表查看

#### 第一步：找到访客列表

每个 agent 卡片会显示：

- 名字
- 授权状态
- 当前 state
- 一行 runtime 摘要

#### 第二步：点击某个 agent

点击后会发生三件事：

1. 列表项进入选中状态
2. 办公室中的对应 agent 高亮
3. 运行检查器加载该对象的详情

### 5.2 从画面中的 agent 对象查看

在主页面 `index.html` 路径里，你也可以直接点击办公室中的 agent 对象。

点击后会：

- 选中该 agent
- 高亮对应对象
- 同步打开/刷新运行检查器

### 5.3 `game.js` 路径里的行为

如果你使用的是 `frontend/game.js` 对应的独立路径，则该路径提供的是：

- 点击对象
- 高亮
- runtime tooltip

它是“最小运行态支持”，不像主页面那样有完整 DOM inspector。

---

## 6. 运行检查器怎么用

运行检查器包含以下 6 个标签页：

- `Summary`
- `Thinking`
- `Messages`
- `Tools`
- `Timeline`
- `Raw JSON`

### 6.1 Summary

显示内容包括：

- Agent 名字
- Selection Key
- Run ID
- Session ID
- Task ID
- 更新时间
- 摘要文本
- 运行关系（父子 / 委派 / 后台任务）

### 6.2 Thinking

显示：

- reasoning 片段
- thinking 类型事件

这些通常来自：

- `runtime.thinking`
- opencode `part.type = reasoning`
- OMO 补充检索结果

### 6.3 Messages

显示：

- 文本输出
- message 类事件
- 部分 status / error 类消息

### 6.4 Tools

显示：

- 工具调用
- 工具结果

### 6.5 Timeline

按事件流显示：

- thinking
- message
- tool_call
- tool_result
- status
- error

适合按时间顺序理解一次 agent 运行。

### 6.6 Raw JSON

显示原始聚合数据，包括：

- agent 原始信息
- runtime 原始结构
- opencode 聚合结果
- OMO 补充结构

这个标签最适合调试。

---

## 6.1 watcher 模式与 office 切换怎么用

当 `STAR_OPENCODE_LOCAL_WATCHER=1`（默认开启）时，系统会尝试自动扫描本机 opencode 会话，并把每个 **root session** 物化成一个 synthetic office。

你在前端里会看到几个变化：

- 访客列表中，自动发现的对象会显示 **“本机会话”** 标记
- 这些对象不是显式 join 的 guest，所以不会显示真正可用的“离开房间”动作
- 运行检查器 Summary 中会显示：
  - `Identity`
  - `Office`
  - `Root Session`
- 检查器顶部会出现 **Office 下拉选择器**，用于在多个 root session office 之间切换
- 现在 selector 优先消费后端返回的 `offices`，而不是再由前端从 `items` 临时推断 office

### 当前 office 语义

在 watcher 模式下：

- **一个 root session = 一个 office**
- child / grandchild / delegated session 默认留在同一个 office 中
- `project/workspace` 只用于 watcher 的 discovery/filter guard
- office 的正式主键现在允许带 `serverOrigin` 命名空间，因此你可能会看到形如 `local.default:ses_xxx` 的 `officeId`

### 如果你想关闭 watcher，退回显式 push 模式

在启动后端前设置：

```powershell
$env:STAR_OPENCODE_LOCAL_WATCHER="0"
python "backend/app.py"
```

关闭后：

- synthetic office agents 不再自动生成
- 页面只显示显式加入或主动 push 的 agent

---

## 7. 后端 API 怎么直接使用

### 7.1 查看总览

```text
GET /runtime/overview
```

本地地址：

```text
http://127.0.0.1:19000/runtime/overview
```

返回内容包括：

- `offices`
- 全部 agent 的 runtime summary
- selectionKey
- runId
- rootSessionId
- officeLocalId
- officeId
- serverOrigin
- phase
- headline
- detail
- provider
- sessionId
- backgroundTaskId

### 7.2 查看单个 agent / run 详情

```text
GET /runtime/agents/<identifier>
```

例如：

```text
http://127.0.0.1:19000/runtime/agents/ses_xxx
```

或：

```text
http://127.0.0.1:19000/runtime/agents/agent_demo
```

返回中通常包含：

- `subject`
- `office`
- `lineage`
- `summary`
- `session`
- `backgroundTask`
- `edges`
- `events`
- `raw`

### 7.3 查看当前映射缓存

```text
GET /runtime/mappings
```

本地地址：

```text
http://127.0.0.1:19000/runtime/mappings
```

它会返回当前后端维护的映射，例如：

- `backgroundTaskId`
- `sessionId`
- `runId`
- `selectionKey`
- `rootSessionId`
- `officeId`
- `lineageBySessionId`

这个接口特别适合排查“为什么某个 task 没有映射到对应 session”。

---

## 8. 当前数据来源说明

当前运行态数据的优先级是：

1. agent 通过 `/join-agent` / `/agent-push` 上报的 `runtime`
2. 本机 `opencode.db` 中与 `runtime.sessionId` 对应的真实 session/message/part 数据
3. 现有 `state/detail` 快照兜底

也就是说：

- push 决定“谁对应哪个运行对象”
- canonical lineage resolver 决定“它最终属于哪个 office family”
- opencode.db / watcher / session tree 决定“这个运行对象里面发生了什么”

如果你想尽量显示真实 opencode 数据，需要：

### 条件 1：本机有 `opencode.db`

常见路径：

```text
%USERPROFILE%\.local\share\opencode\opencode.db
```

### 条件 2：agent 上报时携带 `sessionId`

最简单的方式就是使用：

```powershell
python "office-agent-push.py"
```

因为它已经会自动尝试发现本地 session 并附带上报。

---

## 8.1 如何把 opencode 接进 Star-Office-UI

这一节专门讲“怎么把 opencode 接进来”。如果你希望办公室里看到的不是简单的 `state/detail`，而是更真实的 session、thinking、tools、timeline，那么需要把本机的 opencode 运行数据接到办公室后端。

当前项目已经支持一条最简单的接法：

- `office-agent-push.py` 负责让 agent 加入办公室并持续 push 状态
- 它会自动尝试读取本机 `opencode.db`
- 后端会根据 `sessionId` 聚合 session / child session / message / part
- 前端 inspector 再把这些运行态展示出来

### 当前限制：watcher 默认不会自动跨项目观察

如果你使用的是 watcher 模式，需要特别注意：

- 当前 watcher 默认优先观察 **当前 Star-Office-UI 服务所绑定项目** 的会话树
- 它不会自动扫描你机器上其他完全不同项目的 OpenCode 会话

例如：

- Star-Office-UI 跑在 `C:\project\code\AI\Star-Office-UI`
- 但你真正正在使用 opencode 的项目是 `C:\project\code\AI\any-auto-register`

那当前 watcher 默认不会自动把 `any-auto-register` 的 session 拉进当前办公室。

这时更稳的做法是：

1. 继续用显式 push，把 `any-auto-register` 的 runtime 接进来
2. 或者后续扩展 watcher 的 project/directory override 能力

你可以按下面步骤操作。

### 第一步：确认本机安装了 opencode

执行：

```powershell
opencode --version
```

如果能输出版本号，说明 opencode CLI 可用。

### 第二步：确认本机存在 `opencode.db`

默认路径通常是：

```text
%USERPROFILE%\.local\share\opencode\opencode.db
```

你可以检查：

```powershell
Test-Path "$env:USERPROFILE\.local\share\opencode\opencode.db"
```

如果返回 `True`，说明数据库存在。

### 第三步：确认当前项目绑定了 opencode project

通常仓库里应有：

```text
.git\opencode
```

查看内容：

```powershell
Get-Content ".git\opencode"
```

这个值通常就是当前项目的 `project_id`。`office-agent-push.py` 会用它去 `opencode.db` 中找当前项目最近的 session。

### 第四步：如果默认路径不对，手动指定路径

如果你的 `opencode.db` 不在默认位置，或者 `.git/opencode` 的位置不标准，可以在运行前设置：

```powershell
$env:OFFICE_OPENCODE_DB_PATH="你的 opencode.db 绝对路径"
$env:OFFICE_PROJECT_ID_FILE="你的 .git\opencode 文件绝对路径"
```

例如：

```powershell
$env:OFFICE_OPENCODE_DB_PATH="C:\Users\你的用户名\.local\share\opencode\opencode.db"
$env:OFFICE_PROJECT_ID_FILE="C:\project\code\AI\Star-Office-UI\.git\opencode"
```

### 第五步：启动 Star-Office-UI 后端

```powershell
python "backend/app.py"
```

默认访问地址：

```text
http://127.0.0.1:19000
```

### 第六步：运行 `office-agent-push.py`

```powershell
$env:OFFICE_URL="http://127.0.0.1:19000"
$env:OFFICE_AGENT_NAME="Demo-Agent"
$env:OFFICE_JOIN_KEY="你的 join key"
python "office-agent-push.py"
```

脚本会自动做这些事：

1. 调用 `/join-agent`
2. 读取本地状态（优先 state.json，其次本地 `/status`）
3. 尝试读取本机 `opencode.db`
4. 根据 `.git/opencode` 的 `project_id` 找到最近 session
5. 把以下 runtime 元数据一起推送给办公室后端：

- `provider`
- `sessionId`
- `runId`
- `parentRunId`
- `rootSessionIdHint`
- `officeIdHint`
- `serverOrigin`
- `projectId`
- `headline`
- `updatedAt`

### 第七步：在办公室页面验证是否真的接上了 opencode

浏览器打开：

```text
http://127.0.0.1:19000
```

然后点击访客列表中的 agent，重点观察：

- Summary 里是否出现 `Session ID`
- Summary 里是否出现 `Office Local / Server / Root Session`
- Raw JSON 里是否出现 `opencode`
- Timeline / Thinking / Tools 是否开始出现真实事件

### 第八步：直接验证后端聚合是否吃到了 opencode 数据

先访问：

```text
http://127.0.0.1:19000/runtime/overview
```

重点看：

- `source.provider`
- `source.sessionId`

然后再访问：

```text
http://127.0.0.1:19000/runtime/agents/<你的selectionKey或sessionId>
```

重点看：

- `events`
- `session.childSessionIds`
- `lineage`
- `office`
- `edges`
- `raw.opencode`

### 第九步：如果接上了，但看不到真实事件

按下面顺序排查：

1. `opencode --version` 是否可用
2. `opencode.db` 是否存在
3. `.git\opencode` 是否存在且内容正确
4. `office-agent-push.py` 是否真的在推送
5. `/runtime/overview` 里该 agent 是否有 `sessionId`
6. `/runtime/agents/<id>` 里是否有 `raw.opencode`

### 第十步：推荐的 opencode 接入最小 SOP

如果你只想最快接上 opencode，照下面做：

```powershell
# 1. 确认 opencode CLI
opencode --version

# 2. 确认数据库存在
Test-Path "$env:USERPROFILE\.local\share\opencode\opencode.db"

# 3. 查看项目 project_id
Get-Content ".git\opencode"

# 4. 启动后端
python "backend/app.py"

# 5. 推送 agent + runtime
$env:OFFICE_URL="http://127.0.0.1:19000"
$env:OFFICE_AGENT_NAME="Demo-Agent"
$env:OFFICE_JOIN_KEY="你的 join key"
python "office-agent-push.py"
```

然后去浏览器里打开：

```text
http://127.0.0.1:19000
```

点击 agent，查看 Summary / Timeline / Raw JSON。

---

## 9. 详细操作 SOP（建议照做）

下面是一套推荐的、从零开始的操作 SOP。

### 9.1 第一个终端：安装依赖

```powershell
python -m pip install -r "backend/requirements.txt"
```

### 9.2 第一个终端：启动后端

```powershell
python "backend/app.py"
```

### 9.3 浏览器：打开办公室

```text
http://127.0.0.1:19000
```

### 9.4 第二个终端：设置 agent 环境变量

```powershell
$env:OFFICE_URL="http://127.0.0.1:19000"
$env:OFFICE_AGENT_NAME="Demo-Agent"
$env:OFFICE_JOIN_KEY="你的 join key"
```

### 9.5 第二个终端：运行推送脚本

```powershell
python "office-agent-push.py"
```

### 9.6 浏览器：点击访客列表中的 agent

看到以下现象则表示成功：

1. 列表项高亮
2. 办公室里的对象高亮
3. 运行检查器出现 Summary 内容

### 9.7 浏览器：切换标签页

依次点击：

- Summary
- Thinking
- Messages
- Tools
- Timeline
- Raw JSON

如果都能正常显示，不报错，就说明基础运行态可视化已经正常。

### 9.8 浏览器：直接验证 API

分别打开：

```text
http://127.0.0.1:19000/runtime/overview
http://127.0.0.1:19000/runtime/mappings
```

如果 overview 中能看到 agent，mappings 中能看到 selectionKey/sessionId/taskId 映射，就说明后端聚合层已工作正常。

### 9.9 命令行：运行 adapter 校验脚本

```powershell
python "backend/runtime_adapter_check.py"
```

如果能输出类似以下字段，则说明核心 adapter 正常：

- `overview_count`
- `detail_run_id`
- `detail_event_count`
- `edge_count`

---

## 10. 常见问题与排查

### 问题 1：页面能打开，但 inspector 一直显示“请选择一个 Agent”

说明当前没有选中的运行对象。

处理方法：

1. 点击访客列表中的某个 agent
2. 或先运行 `office-agent-push.py`
3. 或确认 `/runtime/overview` 是否有返回数据

### 问题 2：有 agent，但没有 Thinking / Tools / Timeline

常见原因：

- 当前 agent 没有上报 `runtime`
- `runtime.sessionId` 没带上来
- 本机 `opencode.db` 找不到对应 session
- 当前 session 本身没有 reasoning/tool parts

排查方式：

先访问：

```text
http://127.0.0.1:19000/runtime/overview
```

重点检查该 agent 是否有：

- `source.sessionId`
- `source.provider`

### 问题 3：`office-agent-push.py` 跑了，但页面没变化

按顺序检查：

1. 后端是否正常启动
2. `OFFICE_URL` 是否正确
3. `OFFICE_JOIN_KEY` 是否正确
4. agent 是否 join 成功
5. `/agents` 是否能看到该 agent

### 问题 4：启动后端时报 Flask 缺失

执行：

```powershell
python -m pip install flask pillow
```

### 问题 5：为什么 `game.js` 页面没有完整 inspector

这是当前设计决定：

- `index.html` 路径：完整 runtime inspector
- `game.js` 路径：最小 tooltip / 高亮支持

如果你要查看完整运行态，请优先使用主页面。

### 问题 6：为什么 `runtime/mappings` 返回为空或不完整

可能原因：

- 当前还没有触发 runtime overview/detail 聚合
- 还没有 agent 携带 `runtime` 上报
- 后端刚重启，尚未建立新的映射缓存

解决方式：

1. 先访问一次 `/runtime/overview`
2. 再点击一次 agent
3. 再查看 `/runtime/mappings`

### 问题 7：为什么看不到真实 opencode 会话内容

常见原因：

- 本机没有 `opencode.db`
- 仓库没有 `.git/opencode`
- 上报的 `sessionId` 与本地数据库不匹配

建议检查：

```powershell
opencode --version
Get-Content ".git\opencode"
```

---

## 11. 推荐的实际使用流程

如果你是第一次使用，建议严格按以下顺序：

1. 安装依赖

```powershell
python -m pip install -r "backend/requirements.txt"
```

2. 启动后端

```powershell
python "backend/app.py"
```

3. 打开页面

```text
http://127.0.0.1:19000
```

4. 第二个终端运行：

```powershell
$env:OFFICE_URL="http://127.0.0.1:19000"
$env:OFFICE_AGENT_NAME="Demo-Agent"
$env:OFFICE_JOIN_KEY="你的 join key"
python "office-agent-push.py"
```

5. 回到页面，点击访客列表里的 agent

6. 在 inspector 中先看：

- Summary
- Timeline
- Raw JSON

7. 如果要验证真实 runtime，再看：

```text
http://127.0.0.1:19000/runtime/overview
http://127.0.0.1:19000/runtime/mappings
```

---

## 12. 与实现说明文档的关系

如果你关心“系统是怎么做出来的”，请看：

```text
docs/AGENT_RUNTIME_VISUALIZATION_IMPLEMENTATION.md
```

如果你关心“怎么实际用”，请优先看本文档。
