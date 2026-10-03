# Persona+

![:name](https://count.getloli.com/@astrbot_plugin_persona_plus?name=astrbot_plugin_persona_plus&theme=miku&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

Persona+ 是一个 AstrBot 人格管理增强插件。此 fork 在原有人格管理基础上加入一次性临时委托与安全的双人格定时轮班。

> [!tip]
> 1.3.2 版本对配置文件进行了较大改动。升级后如果遇到配置无法保存的情况，请清除本插件配置文件并重载插件。

## 功能概览

| 能力 | 说明 |
| --- | --- |
| 人格管理 | 支持创建、更新、删除、查看人格 |
| 快捷切换 | 保留 `pp <人格ID>` 作为管理员调试/故障恢复入口，不向 LLM 暴露永久切换能力 |
| 临时委托 | 当前人格可把一次任务交给另一人格处理，并以明确说话人标记显示；不会改变正式值班人格 |
| 临时前台 | 被叫出的角色可在短时间内继续回答后续追问，默认 120 秒 / 3 轮 |
| 定时轮班 | 按可配置时间范围选择值班人格，并通过空闲冷却与最长宽限避免在连续对话中生硬换人 |
| 会话隔离 | 所有动态人格状态按 unified_msg_origin + conversation_id 隔离，群 A 不会影响群 B 或私聊 |
| 文件夹路径 | 支持使用 `文件夹/人格ID` 定位人格 |
| 关键词切换 | 根据消息关键词自动切换到指定人格 |
| 上下文控制 | 切换人格后可自动清空当前对话上下文 |
| 文件导出 | 支持将人格 System Prompt 导出为 `.md` 文件发送 |
| QQ 资料同步 | 切换人格时可同步 QQ 昵称、群名片和头像（仅适配 NapCat） |
| 函数工具 | 可向 LLM 暴露人格管理工具，支持完整创建/更新人格和独立头像管理 |

## 使用方式

Persona+ 提供两类入口：

| 入口 | 适用场景 | 能力范围 |
| --- | --- | --- |
| 指令 | 日常手动管理，追求简单直接 | 创建/更新 System Prompt、查看、导出、删除、头像、切换 |
| 函数工具 | 让 LLM 通过自然语言管理人格 | 支持导出文件、预设对话、函数工具/MCP 工具、Skills、自定义错误回复和独立头像管理 |

指令入口刻意保持简单，不暴露工具和 Skills 配置；如需调整人格可用工具、MCP 工具或 Skills，请使用 WebUI，或启用函数工具后通过自然语言让 LLM 处理。

## 指令

命令组：`persona_plus`

别名：`pp`、`persona+`

| 指令 | 说明 |
| --- | --- |
| `pp` | 查看当前会话使用的人格，并提示常用帮助入口 |
| `pp <人格ID>` | 管理员手动切换当前会话人格，仅用于调试/故障恢复 |
| `pp <文件夹/人格ID>` | 管理员使用文件夹路径手动切换人格 |
| `pp switch <文件夹/人格ID>` | 管理员显式切换人格；适合人格 ID 与子命令同名时使用 |
| `pp help` | 显示帮助与命令说明 |
| `pp list [文件夹路径]` | 列出全部人格，或列出指定文件夹下的人格树 |
| `pp view <文件夹/人格ID>` | 查看指定人格详情 |
| `pp export <文件夹/人格ID>` | 将指定人格的 System Prompt 导出为 `.md` 文件发送 |
| `pp create <文件夹/人格ID>` | 创建新人格，随后发送文本或 `.txt` / `.md` 文件作为 System Prompt |
| `pp update <文件夹/人格ID>` | 更新现有人格，随后发送文本或 `.txt` / `.md` 文件作为新的 System Prompt |
| `pp avatar <文件夹/人格ID>` | 上传或更新人格头像，随后发送图片 |
| `pp delete <文件夹/人格ID>` | 删除指定人格 |

### 路径与序号

- 人格路径使用 `/` 分隔，例如 `测试人格/女仆`。
- 大多数情况下可以只写人格 ID，不必带文件夹路径。
- 序号为全局编号，可直接用于 `view`、`export`、`update`、`avatar`、`delete` 和快捷切换。
- `pp list [文件夹路径]` 也会显示全局编号；因此指定文件夹下的序号可能不是连续的，但含义始终一致。
- 如果人格 ID 与 `help`、`list`、`view` 等子命令同名，请使用 `pp switch <人格ID>` 显式切换。
- `create` 指令中的文件夹不存在时会自动创建。

## 函数工具

函数工具由配置项 `llm_tool_options` 控制，默认不暴露。v1.6 起不再向 LLM 暴露 `persona_switch`；跨人格交流统一通过一次性的 `persona_delegate` 完成。

| 配置值 | 暴露工具 | 能力 |
| --- | --- | --- |
| `list` | `persona_list` | 查询人格列表 |
| `delegate` | `persona_delegate` | 临时委托另一人格处理一次任务，不改变当前会话人格 |
| `view` | `persona_view` | 查看人格详情 |
| `create` | `persona_create` | 创建人格，支持完整字段 |
| `update` | `persona_update` | 更新人格，支持按字段修改 |
| `avatar` | `persona_avatar` | 读取、设置或移除指定人格的头像 |
| `export` | `persona_export` | 导出人格 System Prompt 文件 |
| `delete` | `persona_delete` | 删除人格 |

### 临时委托人格

启用 `llm_tool_options` 中的 `delegate` 后，当前人格可以调用 `persona_delegate`，让另一人格临时处理一次任务。

`persona_delegate` 参数：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `persona_reference` | 是 | 目标人格 ID，或 `文件夹/人格ID` 路径 |
| `task` | 是 | 要交给目标人格完成的具体任务 |

委托会使用目标人格自己的 System Prompt，并按照目标人格的工具白名单构建一次独立 Agent 调用。Persona+ 自身的人格管理工具会从被委托 Agent 中移除，避免递归委托或意外切换人格。

委托前后的正式 `conversation.persona_id` 不会被修改，因此适合“值班人格 + 临时叫另一人格帮忙”的场景。v1.7 起，初次临时出场会显示 `【Plana｜临时插话】` 这样的说话人标记；被叫出的角色还可以在一个短暂的临时前台窗口内继续回答后续追问，而正式值班人格仍保持不变。

推荐配置：

```text
llm_tool_options:
  - delegate
```

v1.6 起不再提供 LLM 永久切换人格的工具。正式值班由轮班调度器决定；`pp switch` 仅作为管理员调试/故障恢复命令保留。

### 临时前台与“中间插话”

默认配置下，被 `persona_delegate` 叫出的角色会：

1. 首次回复带 `【人格ID｜临时插话】` 标记；
2. 在之后 120 秒内继续保持临时前台；
3. 最多继续回答 3 条后续消息；
4. 每次续答显示 `【人格ID】`；
5. 超时、轮数耗尽、正式值班人格被点名，或临时角色已经成为正式值班人格时自动退出。

例如白班正式值班是 Arona：

```text
老师：让 Plana 说句话

【Plana｜临时插话】
在，老师。我还在什亭之匣。

老师：那你姐姐要吃醋了怎么办？

【Plana】
……我认为阿洛娜前辈不会因为这种事情生气，老师。
```

这期间正式值班仍然是 Arona；临时前台只是决定“当前几句话由谁直接回答”。

人格 ID 自然语言引用采用大小写宽容匹配，因此 `plana` 可以唯一解析到数据库中的 `Plana`。

### 完整创建/更新字段

`persona_create` 与 `persona_update` 支持以下字段：

| 字段 | 创建 | 更新 | 说明 |
| --- | --- | --- | --- |
| `persona_reference` | 必填 | 必填 | 人格 ID，或 `文件夹/人格ID` 路径 |
| `system_prompt` | 必填 | 可选 | 人格 System Prompt 文本；更新时省略表示不修改 |
| `begin_dialogs` | 可选 | 可选 | 预设对话数组，需按“用户、助手、用户、助手”的顺序填写，数量必须为偶数；更新时传 `[]` 可清空，省略则不修改 |
| `tools` | 可选 | 可选 | 人格可用函数工具名列表，MCP 工具同样填写工具名 |
| `skills` | 可选 | 可选 | 人格可用 Skills 名称列表 |
| `custom_error_message` | 可选 | 可选 | 此人格请求失败时发送给用户的自定义错误回复；更新时传空字符串可清空，省略则不修改 |

### 头像管理

`persona_avatar` 通过 `operation` 管理任意已存在人格的头像，不依赖当前会话附件。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `operation` | 是 | `get` 返回头像本地文件路径，`set` 设置头像，`remove` 移除头像 |
| `persona_reference` | 是 | 人格 ID，或 `文件夹/人格ID` 路径 |
| `image_source` | 仅 `set` | 图片 HTTP(S) URL、本地绝对路径、`file://` URI、`base64://` 或 `data:image/...;base64,...` 数据 |

### `tools` / `skills` 取值语义

| 取值 | 创建时含义 | 更新时含义 |
| --- | --- | --- |
| `null` | 使用全部工具 / Skills | 改为使用全部工具 / Skills |
| `[]` | 禁用全部工具 / Skills | 改为禁用全部工具 / Skills |
| `["a", "b"]` | 仅启用指定工具 / Skills | 改为仅启用指定工具 / Skills |
| 省略字段 | 等同 `null` | 保持原配置不变 |

### 自然语言示例

- “创建一个叫 `绘图/海报助手` 的人格，提示词是……，只允许使用 `generate_image` 和 `web_search` 工具。”
- “把 `客服助手` 的 Skills 改成只使用 `faq_search`，并把错误回复改为：当前服务繁忙，请稍后再试。”
- “更新 `测试人格`，禁用所有函数工具，但保留全部 Skills。”
- “用 `https://example.com/avatar.png` 作为 `客服助手` 的头像。”
- “读取 `客服助手` 当前的头像文件路径。”
- “移除 `绘图/海报助手` 的头像。”
- “把 `客服助手` 的人设导出成文件发给我。”

## 会话级隔离

此 fork 强制所有人格切换使用 `conversation` scope。运行时状态的键由：

```text
unified_msg_origin + conversation_id
```

共同组成。

因此：

- 群 A 的 Arona/Plana 轮班不会改变群 B；
- 群聊不会改变私聊；
- 同一会话中新建不同 conversation 时，轮班冷却和临时前台状态也彼此独立；
- 不再允许通过配置把人格切换扩散到 session 或 global。

管理员的 `pp switch` 也只修改当前 conversation。

## 定时轮班

开启 `enable_shift_schedule` 后，Persona+ 会按照一个可配置时间范围决定当前 conversation 的值班人格。

典型的 Arona / Plana 配置：

```text
enable_shift_schedule: true
shift_primary_persona: arona
shift_secondary_persona: plana
shift_start_time: "07:00"
shift_end_time: "19:00"
handover_idle_seconds: 60
handover_grace_seconds: 300
```

含义为：07:00（含）到 19:00（不含）由 `arona` 值班，其他时间由 `plana` 值班。开始时间晚于结束时间时自动视为跨午夜时段，例如 19:00 到 07:00。

### 轮班检查不会增加 LLM 花销

插件不会用模型判断当前应该由谁值班。每次收到消息时只进行本地时间和状态比较；大多数消息只涉及几个整数/时间戳比较。只有真正需要交班时才更新一次当前 conversation 的 `persona_id`，不会产生额外 token 或模型请求。

### 交班冷却

为了避免老师正和旧人格连续讨论时突然换人，交班只发生在消息轮次之间：

- 当前 Agent 仍在执行时绝不交班，旧人格会完整做完当前任务。
- 到达轮班边界后，如果上一轮结束后已经空闲至少 `handover_idle_seconds`，下一条消息由新人格接手。
- 如果持续对话一直没有达到空闲时间，最多延迟 `handover_grace_seconds`；超过最长宽限后，正在执行的轮次仍会完成，但下一轮必须交班。
- 插件启动或重载后没有可延续的活动轮次记录时，会在下一条普通消息到来时直接校准到当前计划人格。

例如 19:00 应由 Arona 交给 Plana，而 Arona 在 18:59 接到一个长任务，她会先完整回答；如果老师紧接着追问且仍处于空闲冷却期，则继续由 Arona 处理。出现自然停顿，或者最长宽限到期后，下一轮才由 Plana 接手。

### 时区

`shift_timezone` 留空时跟随 AstrBot 当前会话的 `timezone`；也可以显式填写 IANA 时区，例如 `Asia/Shanghai`、`Asia/Tokyo`。

### 与其他切换机制的关系

定时轮班启用时，旧版关键词自动切换自动停用，避免关键词直接覆盖值班人格。人格之间临时点名另一位处理当前任务，应使用 `persona_delegate`；管理员仍可用 `pp switch` 临时调试，但下一条普通消息会再次接受轮班规则校准。

## 关键词自动切换

仅在未开启定时轮班时，`enable_keyword_switching` 才会根据 `keyword_mappings` 执行旧版关键词人格切换。轮班模式下此功能自动停用。

| 配置示例 | 说明 |
| --- | --- |
| `女仆:女仆` | 消息包含“女仆”时切换到 `女仆` 人格 |
| `画图:绘图/海报助手` | 消息包含“画图”时切换到 `绘图/海报助手` 人格 |

如果配置了自动切换提示模板，模板中可使用 `{persona_id}` 占位符。

## QQ 昵称与头像同步

QQ 资料同步仅适配 NapCat / OneBot 链路。

| 配置项 | 说明 |
| --- | --- |
| `sync_nickname_on_switch` | 切换人格时同步昵称或群名片 |
| `nickname_sync_mode` | 控制昵称同步模式 |
| `sync_avatar_on_switch` | 切换人格时同步头像 |
| `nickname_template` | 昵称/群名片模板，支持 `{persona_id}` |

### 昵称同步模式

| 模式 | 说明 |
| --- | --- |
| `profile` | 修改 QQ 昵称，群聊和私聊都会修改 QQ 昵称 |
| `group_card` | 群聊中只修改群名片，私聊不修改 |
| `hybrid` | 群聊中修改群名片，私聊中修改 QQ 昵称 |

## 配置项

| 配置项 | 类型/可选值 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `enable_shift_schedule` | bool | `false` | 启用定时双人格轮班 |
| `shift_primary_persona` | string | `arona` | 设定时间范围内的人格 ID |
| `shift_secondary_persona` | string | `plana` | 设定时间范围外的人格 ID |
| `shift_start_time` | `HH:MM` | `07:00` | 时段开始，包含该时刻 |
| `shift_end_time` | `HH:MM` | `19:00` | 时段结束，不包含该时刻；支持跨午夜 |
| `shift_timezone` | string | 空 | 留空跟随 AstrBot 时区，或填写 IANA 时区 |
| `handover_idle_seconds` | int | `60` | 到点后需要的连续对话空闲时间 |
| `handover_grace_seconds` | int | `300` | 连续对话允许旧人格延迟交班的最长时间 |
| `enable_foreground_continuation` | bool | `true` | 是否启用临时角色连续发言 |
| `foreground_ttl_seconds` | int | `120` | 临时角色每次发言后保持前台的最长秒数 |
| `foreground_followup_turns` | int | `3` | 初次临时插话后最多继续回答的后续消息数 |
| `enable_keyword_switching` | bool | `true` | 兼容旧版关键词切换；轮班开启时自动停用 |
| `keyword_mappings` | list | `["关键词:人格"]` | 关键词与人格映射；仅在轮班关闭时生效 |
| `auto_switch_scope` | `conversation` | `conversation` | v1.7 起强制 conversation 级隔离；旧配置中的 session/global 会被忽略 |
| `manage_wait_timeout_seconds` | int | `60` | 创建、更新人格或上传头像时等待用户内容的最长时间 |
| `admin_commands` | list | 含 `switch` | `switch` 始终仅允许管理员，用作调试/故障恢复 |
| `llm_tool_options` | list | `[]` | 向 LLM 暴露的人格函数工具；不再包含 `switch` |
| `enable_auto_switch_announce` | bool | `true` | 仅影响兼容的手动/关键词切换；定时轮班静默交接 |
| `clear_context_on_switch` | bool | `false` | 仅影响兼容切换；定时轮班始终保留上下文 |
| `sync_nickname_on_switch` | bool | `true` | 切换人格时是否同步修改 QQ 昵称或群名片 |
| `nickname_sync_mode` | `profile` / `group_card` / `hybrid` | `group_card` | QQ 昵称/群名片同步模式 |
| `sync_avatar_on_switch` | bool | `false` | 切换人格时是否同步修改 QQ 头像 |
| `nickname_template` | string | `[B0T]{persona_id}` | QQ 昵称模板 |

