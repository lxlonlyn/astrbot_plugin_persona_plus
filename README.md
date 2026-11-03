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
| 说话人身份保护 | 正式回复持久化为 `【Arona】` / `【Plana】`，每轮动态锚定当前 speaker，防止另一人格的大量历史措辞侵占当前身份 |
| 定时轮班 | 按可配置时间范围选择值班人格，并通过空闲冷却与最长宽限避免在连续对话中生硬换人 |
| 会话隔离 | 所有动态人格状态按 config_id + unified_msg_origin + conversation_id 隔离，群 A 不会影响群 B 或私聊 |
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

## 共享上下文与身份保护

v1.9 在启用的配置文件中继续使用同一个 conversation 共享上下文，不在交班时清空历史，也不自动调用 LLM 总结。这样老师在轮班边界尚未问完的问题可以被下一位秘书完整承接。

为避免长期共享历史导致人格被另一角色的大量用语侵占，插件增加三层身份保护：

1. 正式值班回复必须带明确的说话人标签，例如 `【Arona】`、`【Plana】`；临时首次插话使用 `【Plana｜临时插话】`。
2. 每次 LLM 请求都会通过 AstrBot 的临时 `extra_user_content_parts` 注入很短的 runtime identity anchor，明确 `current_speaker`、`formal_on_duty` 和 `speaker_mode`。该内容使用 `.mark_as_temp()`，不会写入 conversation 历史，也不会修改稳定的 System Prompt。
3. 真正完成正式交班时，只在共享历史中加入一个轻量 `[PERSONA_HANDOVER from=... to=...]` 边界，说明值班者变化但当前话题和未完成任务继续；不会生成摘要。

旧版本已经写入历史、但没有说话人标签的 assistant 消息无法可靠追溯究竟是谁说的。v1.8 不会猜测或重写数据库中的旧历史，而是在每次送入 LLM 时临时标成：

```text
[SPEAKER=legacy-unattributed]
```

模型会被明确告知这些旧消息只能作为内容参考，不能据此判断“自己是谁”。随着后续新消息都带 speaker 标签，旧的未标注历史会逐渐退出上下文窗口。

例如共享历史可以自然变成：

```text
【Arona】
老师——这个问题先看这里！

[PERSONA_HANDOVER from="Arona" to="Plana"]

【Plana】
已确认，老师。沿用阿洛娜前辈刚才的条件，第二种情况是……
```

这里没有拆 conversation，因此任务连续性保留；同时每句话的身份归属也明确。

## 会话级隔离

此 fork 强制所有人格切换使用 `conversation` scope。运行时状态的键由：

```text
config_id + unified_msg_origin + conversation_id
```

共同组成。

因此：

- 未列入 `shift_profile_rules` 的 AstrBot 配置文件完全不被自动接管；
- 不同配置文件可以使用不同时间表和人格；
- 群 A 的 Arona/Plana 轮班不会改变群 B；
- 群聊不会改变私聊；
- 同一会话中新建不同 conversation 时，轮班冷却和临时前台状态也彼此独立；
- 不再允许通过配置把人格切换扩散到 session 或 global。

管理员的 `pp switch` 也只修改当前 conversation。

## 按 AstrBot 配置文件独立轮班（v1.9）

**旧版全局 `enable_shift_schedule` 等字段已经停用。** 升级后不会将旧的 Arona/Plana 轮班自动套用到所有 Bot；`shift_profile_rules` 默认为空，所有配置文件都不会被自动接管。

在需要管理的 Bot、群或私聊发送管理员指令 `/pp`，找到回复中的 `配置文件 ID`。它来自 AstrBot `get_conf_info(UMO)['id']`（UUID 或 `default`），不是 WebUI 中的显示名称。

在 Persona+ 插件配置的 `shift_profile_rules`（「按 AstrBot 配置文件 ID 独立启用 Persona+」）中新增一条「配置文件独立人格规则」，准确填写该 ID。每条规则有启用开关、`mode`（`shift` 为定时双人格；`keyword` 为旧关键词模式）、轮班人格、时间、时区、冷却及是否接管已有对话。保存后重新加载插件，再用 `/pp` 检查 `自动管理：shift/keyword`。

示例（两个规则互不干扰；没有列出的 Bot 完全不会自动切换）：

```json
{"shift_profile_rules": [
  {"__template_key": "two_persona", "config_id": "default",
   "enabled": true, "mode": "shift", "primary_persona": "Arona",
   "secondary_persona": "Plana", "start_time": "07:00",
   "end_time": "19:00", "timezone": "Asia/Shanghai",
   "idle_seconds": 60, "grace_seconds": 300,
   "takeover_existing_conversations": false},
  {"__template_key": "two_persona", "config_id": "另一配置文件UUID",
   "enabled": true, "mode": "shift", "primary_persona": "PersonaX",
   "secondary_persona": "PersonaY", "start_time": "09:00",
   "end_time": "22:00", "timezone": "Asia/Tokyo"}
]}
```

在任何自动处理前，插件都按真实配置文件 ID 做白名单校验。未列入的配置文件不会被创建或更新 conversation、注入身份锚点、强制加说话人标签或执行自动关键词切换。Persona+ 的 LLM 工具即使在全局工具表中可见，也会拒绝未授权配置的调用。

**保护已有对话**：`takeover_existing_conversations=false`（默认）时，如果已有会话绑定了不属于当前规则两位值班人格的其他人格，轮班不会擅自接管。新会话、未绑定人格的会话及已使用其中一位人格的会话可以正常轮班。明确需要覆盖第三方人格时才开启该选项。

轮班支持跨午夜，沿用不打断正在执行的 Agent、`idle_seconds` 空闲冷却、`grace_seconds` 最长宽限和共享上下文。`timezone` 留空时使用当前 AstrBot 配置的时区；时间检查仅在收到消息时执行，不额外消耗 LLM token。重复 ID、通配符、非法时区和无效时间都会被拒绝，保证失败时不接管。

**迁移提醒**：升级前请备份 AstrBot 数据库及 Persona+ 插件配置。旧版已经写入的 `conversation.persona_id` 不会因为修复作用范围而自动复原；需要由管理员确认并恢复正确的人格，不能用 `update_conversation(persona_id=None)` 当作清空操作。移除规则也不会删除已有会话的人格绑定。

## 关键词自动切换

只有显式配置 `mode=keyword`，并且全局 `enable_keyword_switching=true` 的配置文件，才会按 `keyword_mappings` 切换人格。`mode=shift` 和未启用的配置文件都不会执行关键词切换。

| 配置示例 | 说明 |
| --- | --- |
| `女仆:女仆` | 消息包含“女仆”时切换到 `女仆` 人格 |
| `画图:绘图/海报助手` | 消息包含“画图”时切换到 `绘图/海报助手` 人格 |

## QQ 昵称与头像同步

QQ 资料同步仅适配 NapCat / OneBot 链路。注意 `profile`/`hybrid` 可能修改 QQ 账号本身的全局昵称，同一 QQ 账号下不同配置文件仍会共享账号资料；推荐 `group_card`。

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
| `shift_profile_rules` | `template_list` | `[]` | 按 AstrBot 配置文件 ID 独立设置人格模式及轮班规则；旧版全局字段已隐藏停用 |
| `enable_foreground_continuation` | bool | `true` | 是否启用临时角色连续发言 |
| `foreground_ttl_seconds` | int | `120` | 临时角色每次发言后保持前台的最长秒数 |
| `foreground_followup_turns` | int | `3` | 初次临时插话后最多继续回答的后续消息数 |
| `enable_keyword_switching` | bool | `true` | 仅 `mode=keyword` 的已启用配置文件使用 |
| `keyword_mappings` | list | `["关键词:人格"]` | 关键词与人格映射；仅 `mode=keyword` 使用 |
| `auto_switch_scope` | `conversation` | `conversation` | 仍强制 conversation 隔离，自动行为额外按 config_id 过滤 |
| `manage_wait_timeout_seconds` | int | `60` | 创建、更新人格或上传头像时等待用户内容的最长时间 |
| `admin_commands` | list | 含 `switch` | `switch` 始终仅允许管理员，用作调试/故障恢复 |
| `llm_tool_options` | list | `[]` | 向 LLM 暴露的人格函数工具；不再包含 `switch` |
| `enable_auto_switch_announce` | bool | `true` | 仅影响兼容的手动/关键词切换；定时轮班静默交接 |
| `clear_context_on_switch` | bool | `false` | 仅影响兼容切换；定时轮班始终保留上下文 |
| `sync_nickname_on_switch` | bool | `true` | 切换人格时是否同步修改 QQ 昵称或群名片 |
| `nickname_sync_mode` | `profile` / `group_card` / `hybrid` | `group_card` | QQ 昵称/群名片同步模式 |
| `sync_avatar_on_switch` | bool | `false` | 切换人格时是否同步修改 QQ 头像 |
| `nickname_template` | string | `[B0T]{persona_id}` | QQ 昵称模板 |

