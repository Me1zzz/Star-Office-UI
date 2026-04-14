# OpenCode Watcher 模式操作 SOP

本文档是一份面向实际使用的简化 SOP，适合你在已经完成开发接入后，快速验证和使用 **本机 opencode 自动监听 + 自动生成办公室 agent** 的能力。

适用场景：

- 你已经启动了 Star-Office-UI 后端
- 你希望**不手动 push 每个 agent**
- 你希望系统自动从本机 OpenCode 会话树中生成 office 对象

---

## 一、先理解 watcher 模式到底在做什么

watcher 模式的核心规则是：

- **一个 root session = 一个 office**
- child / grandchild / delegated session 默认留在同一个 office
- `project/workspace` 只负责帮助 watcher 过滤“当前应该看哪些 session”
- 前端里出现的自动对象，叫做 **synthetic office agents**

你可以把它理解成：

> Star-Office-UI 不再等每个 agent 主动上报，而是主动去看本机 OpenCode 会话树，再把每个 root session 物化成一个办公室对象。

### 当前 watcher 的一个重要限制

当前实现里，watcher **默认优先观察当前 Star-Office-UI 这个项目本身对应的 project/workspace**，不会自动跨到另一个完全不同的项目去观察会话。

例如：

- Star-Office-UI 跑在：`C:\project\code\AI\Star-Office-UI`
- 但你真正正在使用 opencode 的项目是：`C:\project\code\AI\any-auto-register`

那么当前 watcher 默认不会自动把 `any-auto-register` 的 session 拉进来。

换句话说，当前版本的 watcher 不是“自动监听你机器上所有项目的全部 OpenCode 会话”，而是：

> **优先监听当前 office 服务所绑定项目的会话树。**

如果你想看另一个项目（例如 `any-auto-register`）的会话，目前有两种方式：

1. **继续用显式 push**：通过 `OFFICE_PROJECT_ID_FILE` / `OFFICE_OPENCODE_DB_PATH` 把那个项目的 runtime 推进当前办公室
2. **后续扩展 watcher 配置**：增加专门的 watcher project/directory override，让 watcher 去看另一个项目

---

## 二、最小启动条件

开始之前，你至少要满足下面 3 个条件：

### 1. Star-Office-UI 后端已经启动

在项目根目录执行：

```powershell
python "backend/app.py"
```

默认地址：

```text
http://127.0.0.1:19000
```

### 2. 本机有 OpenCode 数据

先确认本机是否有 `opencode.db`：

```powershell
Test-Path "$env:USERPROFILE\.local\share\opencode\opencode.db"
```

如果返回 `True`，说明 watcher 至少可以走 DB fallback。

### 3. watcher 没被手动关闭

默认 watcher 是开启的。

如果你之前设置过：

```powershell
$env:STAR_OPENCODE_LOCAL_WATCHER="0"
```

那它就会被关闭。请去掉这个设置，或者重新开一个终端再启动后端。

---

## 三、标准操作步骤（建议照做）

### 第一步：启动 Star-Office-UI 后端

```powershell
python "backend/app.py"
```

### 第二步：浏览器打开办公室页面

```text
http://127.0.0.1:19000
```

如果页面打不开，先别继续，先确认后端是否真的在跑。

### 第三步：确认 watcher 是否真的工作

浏览器打开：

```text
http://127.0.0.1:19000/runtime/mappings
```

你重点看这几个字段：

- `watcher.enabled`
- `watcher.syntheticCount`
- `watcher.lastRefreshAt`
- `watcher.lastSseEventAt`

#### 成功标准

如果你看到：

- `enabled = true`
- `syntheticCount > 0`

说明 watcher 已经发现本机会话，并且生成了 synthetic office agents。

如果你只看到默认的 `star`，没有任何 synthetic office agents，常见原因之一就是：

- 你当前真正运行 opencode 的项目不是 Star-Office-UI 自己
- 但 watcher 仍然只在看 Star-Office-UI 对应的 project/workspace

### 第四步：确认 watcher 发现了哪些 office

浏览器打开：

```text
http://127.0.0.1:19000/runtime/overview
```

重点看返回里每个 item 的：

- `agentId`
- `identityType`
- `synthetic`
- `rootSessionId`
- `officeId`
- `source.provider`

#### 你应该怎么理解

如果某一项类似：

```json
{
  "agentId": "local:ses_xxx",
  "identityType": "synthetic",
  "synthetic": true,
  "rootSessionId": "ses_xxx",
  "officeId": "ses_xxx"
}
```

那就表示：

- watcher 发现了一个 root session
- 它已经被物化成一个 office 对象
- 前端里这个对象就代表一个 office

### 第五步：回到前端页面看 synthetic office agents

回到：

```text
http://127.0.0.1:19000
```

你现在应该能在访客列表里看到自动生成的对象。

它们通常有这些特征：

- 名字旁边带 **“本机会话”** 标记
- 不能手动“离开房间”
- 点击后会进入 inspector

### 第六步：切换不同 office

在 runtime inspector 附近，你会看到一个 **Office 下拉选择器**。

它的作用是：

- 当同一个项目里存在多个 root session 时
- 让你按 root session 切换 office

#### 使用方式

1. 点击下拉框
2. 选择某个 office
3. 访客列表会切到该 office 下的对象
4. 运行检查器也会围绕这个 office 的对象工作

### 第七步：查看某个 office 的详细运行态

点击某个 synthetic office agent 后，重点看 inspector 的：

- `Summary`
- `Timeline`
- `Raw JSON`

#### Summary 里重点看

- `Identity`
- `Office`
- `Root Session`
- `Session`
- `Task`

#### Timeline 里重点看

- child / grandchild / delegated session 的事件
- message / tool / thinking 事件

#### Raw JSON 里重点看

- `raw.opencode`
- `raw.familySessions`
- `session.childSessionIds`
- `edges`

---

## 四、如何区分 synthetic office agent 和显式 push agent

这是 watcher 模式下非常重要的一点。

### synthetic office agent

特点：

- 自动生成
- 来自本机 watcher
- `identityType = synthetic`
- 通常 `agentId` 形如：

```text
local:<rootSessionId>
```

- 列表中会有 **“本机会话”** 标记
- 不能手动 leave

### 显式 push agent

特点：

- 通过 `/join-agent` / `/agent-push` 显式进入办公室
- 是真实 guest member
- 一般有 join key 语义
- 可以走“离开房间”动作

### 一句话区分

- **synthetic** = watcher 自动发现
- **explicit** = 人工或脚本主动 push 进来

---

## 五、如何判断当前看到的是不是“一个 root session 一个 office”

最简单的判断方式是：

### 1. 看 `/runtime/overview`

如果你看到：

- `rootSessionId = ses_abc`
- `officeId = ses_abc`

这就说明当前 office 主键绑定的是 root session。

### 2. 看 inspector Summary

Summary 里如果显示：

- `Office = ses_abc`
- `Root Session = ses_abc`

就说明这个 synthetic office 是按 root session 物化的。

### 3. 看 child session 是否仍留在同一 detail 中

如果 `session.childSessionIds` 里还能看到多个 descendant session，说明：

- 它们没有被拆成新的独立 office
- 而是留在同一个 root office 里

这就是当前设计的预期行为。

---

## 六、最短验证 SOP

如果你只想最快验证 watcher 是否工作，请照下面做：

### 1. 启动后端

```powershell
python "backend/app.py"
```

### 2. 跑 watcher smoke check

```powershell
python "backend/opencode_local_watcher_check.py"
```

#### 成功标准

如果输出里有：

- `enabled: true`
- `count > 0`
- `sampleRootSessionId`
- `sampleOfficeId`

说明 watcher 已经能 materialize synthetic offices。

### 3. 打开 mappings

```text
http://127.0.0.1:19000/runtime/mappings
```

看：

- `syntheticCount`
- `items`
- `rootSessionId`
- `officeId`

### 4. 打开 overview

```text
http://127.0.0.1:19000/runtime/overview
```

确认至少有一条：

- `synthetic = true`
- `identityType = synthetic`

### 5. 打开前端

```text
http://127.0.0.1:19000
```

然后：

1. 找到带“本机会话”标记的对象
2. 点击它
3. 看 Summary / Timeline / Raw JSON

---

## 七、常见问题

### 问题 1：`syntheticCount = 0`

说明 watcher 没发现任何本机会话。

先检查：

```powershell
Test-Path "$env:USERPROFILE\.local\share\opencode\opencode.db"
```

如果数据库不存在，watcher 就没有可读数据。

还有一种很常见的情况是：

- Star-Office-UI 服务跑在当前项目下
- 但你真正活跃的 OpenCode 会话属于另一个项目

这时 watcher 可能不会自动跨项目发现它们，所以 `/runtime/mappings` 里只会看到默认的 `star`。

### 问题 2：watcher 开着，但 `sourceMode = db`

这不一定是问题。

当前逻辑是：

- 如果本机 OpenCode server 可用，优先走 official HTTP/session/message
- 如果不可用，就 fallback 到本机 `opencode.db`

所以：

- `sourceMode = db` = 正常降级
- 不代表 watcher 失效

### 问题 3：`lastSseEventAt = null`

这通常表示：

- 本机 OpenCode server 没开
- 或 project/global SSE 当前不可用

这时 watcher 仍然可以依赖 polling + DB fallback 正常工作。

### 问题 4：前端里没看到 office selector

通常说明当前只发现了一个 root session office，没必要切换。

当 watcher 发现多个 synthetic offices 时，selector 才更有意义。

### 问题 5：为什么 child session 没变成新的办公室小人

这是当前设计故意如此：

- 一个 root session = 一个 office
- child / grandchild session 默认留在同一个 office 中

它们应该主要出现在：

- `edges`
- `Timeline`
- `Raw JSON`

### 问题 6：为什么我明明在别的项目里用 opencode，但这里看不到 synthetic office

这通常说明你遇到的是 **当前 watcher 的项目范围限制**。

例如：

- Star-Office-UI 跑在 `C:\project\code\AI\Star-Office-UI`
- 但你正在 `C:\project\code\AI\any-auto-register` 里使用 opencode

当前 watcher 默认不会自动跨到 `any-auto-register` 去监听。

这时你可以：

1. 先继续用显式 push 方式把那个项目的 runtime 接进来
2. 或者后续扩展 watcher 的 project/directory override 能力

而不是自动拆成一堆新的房间。

---

## 八、如果你想退回旧模式

在启动后端前执行：

```powershell
$env:STAR_OPENCODE_LOCAL_WATCHER="0"
python "backend/app.py"
```

这样系统会回退到旧的显式 push 模式：

- 不自动生成 synthetic office agents
- 只显示主动 join/push 的 agent

---

## 九、一句话总结

watcher 模式下你要记住的只有一句：

> **不是“一个 agent 一个房间”，而是“一个 root session 一个 office”。**

只要理解这一点，你就知道：

- 为什么会出现 synthetic office agents
- 为什么 inspector 里有 `Office / Root Session`
- 为什么 child/grandchild session 不会自动拆成新的独立房间
