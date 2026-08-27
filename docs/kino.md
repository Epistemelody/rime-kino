# kino 交互契约与引擎规范手册

[简体中文](kino.md) | [English](kino.en.md)

| 属性 | 规格说明 |
| :--- | :--- |
| **产品方案** | **kino**（方案标识符：`rime_mint`） |
| **文档职责** | 详尽定义按键输入到文字上屏的完整交互契约、前缀通道路由、维特比分词模型、候选窗视觉排版、标点与 Emoji 规则及 QA 验收矩阵 |
| **不包含内容** | 操作系统底层软件包安装教程（见根目录 [`README.md`](../README.md)）、CSV 内部字段设计（见 [`drafts/README.md`](drafts/README.md)） |
| **文档状态** | 现行权威交互标准（Active Normative Specification） |
| **修订日期** | 2026-08-27 |

---

## 目录

1. [产品身份与非目标](#1-产品身份与非目标)
2. [跨平台运行环境快速接入](#2-跨平台运行环境快速接入)
3. [平台不变量与界面排版准则](#3-平台不变量与界面排版准则)
4. [方案列表与功能开关](#4-方案列表与功能开关)
5. [候选窗呈现与预编辑契约](#5-候选窗呈现与预编辑契约)
6. [中英切换与上屏语义](#6-中英切换与上屏语义)
7. [拼音热路径与音节代数](#7-拼音热路径与音节代数)
8. [前缀引导通道规范](#8-前缀引导通道规范)
   - 8.1 [`\` 符号与数学命令通道](#81--符号与数学命令通道-command-draft)
   - 8.2 [`;` 拉丁重音通道](#82--拉丁重音通道-latin-accents)
   - 8.3 [`~` 日文假名与维特比汉字分词](#83--日文假名与维特比汉字分词-japanese-kana--viterbi)
9. [键面标点权威映射](#9-键面标点权威映射)
10. [Emoji 过滤与注入规则](#10-emoji-过滤与注入规则)
11. [继承的上游扩展功能](#11-继承的上游扩展功能)
12. [手写源码与生成文件边界](#12-手写源码与生成文件边界)
13. [测试套件与验收清单](#13-测试套件与验收清单)
14. [关联文档导航](#14-关联文档导航)

---

## 1. 产品身份与非目标

### 1.1 产品身份模型

| 项目 | 技术定位 | 说明 |
| :--- | :--- | :--- |
| **产品名** | **kino** | 用户界面、方案选单、系统托盘呈现的统一品牌显示名称。 |
| **方案标识符** | `rime_mint` | 保持不变。沿用薄荷拼音主方案 ID，确保词库结构与用户词典无缝兼容。 |
| **上游内核** | `proj-ref/oh-my-rime` | 只读 Vendor 子模块。部署时作为基础文件同步至用户目录。 |
| **定制叠加层** | `overlay/` | kino 的唯一个性化代码基准，包含补丁 YAML、Lua 脚本与方案包装。 |
| **历史归档** | `proj-arc/cloverplus` | 基于四叶草拼音与 rime_latex 的定制快照，仅作标点与符号考据，不是活动运行代码。 |

### 1.2 显式非目标（Explicit Non-Goals）

为保证工业级稳定性与极速打字响应，kino 明确排除以下特性：

- **禁止将独立 Kagiroi 方案加入切换菜单**：日文输入统一通过 kino 主方案的 `~` 前缀通道路由。
- **禁止将空格键重定义为日文转换键**：在所有语言通道中，空格键始终保持为「首选候选词上屏」。
- **不实现用户词典学习/义训/Nico 表**：避免大规模外部词库污染核心拼音索引与内存空间。
- **不引入复杂双拼变体**：不提供 `sbzr_mix` 及 Spanish Colemak 等非标准键盘布局。
- **不引入 Typst `frac` 交互式结构格子**：所有数学符号输出均为平铺 Unicode 字符或宏序列。

---

## 2. 跨平台运行环境快速接入

在已配置好基础依赖的机器上，运行以下命令即可重新构建并部署 kino：

```bash
# Linux (Fcitx5) / macOS (Squirrel)
./scripts/deploy.sh

# Windows (PowerShell)
.\scripts\deploy.ps1
# 部署后在系统托盘右键小狼毫图标并点击「重新部署」
```

macOS 部署完成后，点击菜单栏鼠须管图标并选择「重新部署」。

### 运行时目标目录

- **Linux**：`~/.local/share/fcitx5/rime`
- **Windows**：`%APPDATA%\Rime`
- **macOS**：`~/Library/Rime`
- **安全干跑模式**：设置环境变量 `RIME_DIR=/tmp/target`，部署脚本将跳过系统主题修改与 150MB 日文大表复制。

---

## 3. 平台不变量与界面排版准则

无论在何种操作系统或桌面环境中，以下排版与交互准则必须严格成立：

| 平台环境 | 配置文件路径 | 关键配置项 | 强制值 | 技术目的 |
| :--- | :--- | :--- | :--- | :--- |
| **Linux (Fcitx5)** | `platform/fcitx5/conf/rime.conf` | `PreeditMode` | `Do not show` | 禁用嵌入式行内预编辑，防止字母直接插入文档 |
| | | `SwitchInputMethodBehavior` | `Commit raw input` | Shift 切中英时提交纯原始 ASCII 编码（如 `nihao`） |
| | `~/.config/fcitx5/conf/classicui.conf` | `Theme` / `DarkTheme` | `kino-dark` | 默认采用 Nord 极夜深色主题 |
| | | `UseDarkTheme` | `False` | 锁定深色主题，不随系统浅色模式切换 |
| **Windows (Weasel)** | `overlay/weasel.custom.yaml` | `inline_preedit` | `false` | 禁用行内直接预编辑 |
| | | `preedit_type` | `composition` | 编码区统一显示输入组合串 |
| | | `horizontal` | `false` | 候选词强制采用纵向垂直排列 |
| | | `color_scheme_dark` | `kino_dark` | 启用匹配的 Nord Dark 界面配色 |
| **macOS (Squirrel)** | `overlay/squirrel.custom.yaml` | `inline_preedit` | `false` | 禁用行内直接预编辑 |
| | | `horizontal` | `false` | 候选词强制采用纵向垂直排列 |
| | | `color_scheme` | `kino_dark` | 启用匹配的 Nord Dark 界面配色 |
| **Rime 全局** | `overlay/default.custom.yaml` | `menu/page_size` | `10` | 每页固定呈现 10 个候选词（数字键 `1`–`9`、`0` 选词） |

---

## 4. 方案列表与功能开关

### 4.1 方案选单定义 (`schema_list`)

`overlay/default.custom.yaml` 中的方案选单列表**严格仅包含以下两项**：

1. **`rime_mint`**（显示名称：`kino`）：默认全功能输入方案。
2. **`kana`**（显示名称：`假名`）：轻量级独立日文假名方案。

> `latin`（拉丁重音）与 `jp`（日文 Viterbi）仅作为 kino 内部 Lazy-Load 词库模块存在，**严禁**暴露在方案切换菜单中。

### 4.2 功能开关矩阵（Feature Flags）

所有功能开关**默认全部开启**（`reset: 1`），用户可通过快捷键或状态栏独立关闭指定通道。关闭后该通道立即停止输出候选词，完全不影响其余通道：

| 开关标识符 | 快捷切换键 | 状态显示（关 / 开） | 管控功能与作用域 |
| :--- | :--- | :--- | :--- |
| `emoji_suggestion` | `Control+Shift+E` | 😺 / 😸 | 控制基于 OpenCC 的拼音 Emoji 联想输出 |
| `kino_typst` | 方案选单 / 状态栏 | 无typst / typst | 控制 `\` 通道中 `typst-*` 类符号与函数宏 |
| `kino_latex` | 方案选单 / 状态栏 | 无latex / latex | 控制 `\` 通道中 `latex` 与 `latex-alias` 类符号 |
| `kino_katex` | 方案选单 / 状态栏 | 无katex / katex | 控制 `\` 通道中 `katex` 专用宏 |
| `kino_lean` | 方案选单 / 状态栏 | 无lean / lean | 控制 `\` 通道中 `lean` 与 `lean-shorthand` 符号 |
| `kino_mma` | 方案选单 / 状态栏 | 无mma / mma | 控制 `\` 通道中 Mathematica `NamedCharacter` 符号 |
| `kino_latin` | 方案选单 / 状态栏 | 无latin / latin | 控制 `;` 前缀拉丁重音字符通道 |
| `kino_japanese` | 方案选单 / 状态栏 | 无日语 / 日语 | 控制 `~` 前缀日文假名及 Viterbi 汉字通道（不影响独立「假名」方案） |

**底层实现机制**：由 `overlay/lua/kino_features.lua` 读取上下文选项；`command_draft.lua` 与 `jp_draft.lua` 依据开关动态拦截候选；`lua_filter@*feature_gate` 作为兜底屏障过滤退化码表输出。

---

## 5. 候选窗呈现与预编辑契约

1. **零行内污染**：输入未完成时，未上屏字符严格限制在输入法候选窗口顶部的预编辑（Composition）区域，目标应用程序的光标处不得出现任何半生字符。
2. **多方言注释排版**：在 `\` 命令通道中，候选词右侧的注解必须统一采用方括号格式，且按固定顺序合并展示当前已开启的方言出处：
   $$\text{格式：} \quad \text{glyph} \quad \text{code}\ [\text{dialect}_1 \ \text{dialect}_2 \dots]$$
   - **固定方言顺序**：`latex` $\rightarrow$ `latex*` $\rightarrow$ `katex` $\rightarrow$ `typst` $\rightarrow$ `lean` $\rightarrow$ `mma` $\rightarrow$ `unicode`
   - **示例**：
     - 输入 `\alpha` $\rightarrow$ 显示 `α`，注解为 `alpha [latex katex typst lean mma]`
     - 输入 `\plus` $\rightarrow$ 显示 `+`，注解为 `plus [latex*]`（`latex*` 标示非 TeX 原生别名）

---

## 6. 中英切换与上屏语义

### 6.1 Shift 键状态机与 Raw Input 提交

在 `overlay/rime_mint.custom.yaml` 的 `ascii_composer` 映射中：

| 按键动作 | 缓冲区状态 | 触发行为与技术保证 |
| :--- | :--- | :--- |
| **`Shift_L` (左 Shift)** | 存在未上屏编码 | 触发 `commit_code`：**直接上屏原始 ASCII 字符**（例如输入 `nihao` 后按左 Shift，文本框直接输入 `nihao`，严禁输出「你好」）。 |
| **`Shift_R` (右 Shift)** | 存在未上屏编码 | 同样触发 `commit_code`，覆盖上游薄荷默认的 `inline_ascii` 模式。 |
| **`Shift` (单按)** | 无未上屏编码 | 触发 Fcitx5 全局中英文切换（`SwitchInputMethodBehavior="Commit raw input"`）。 |

### 6.2 选词与翻页键位映射

- **空格键 (`Space`)**：始终上屏当前第 1 候选词（中/英/命令/日语全通道通用）。
- **数字键 (`1`–`9`, `0`)**：分别选取当前页的第 1 至第 10 个候选词。
- **翻页键**：`-` / `=` 以及 `,` / `.`（在已有候选窗状态下）、方向键上下翻页、鼠标滚轮滚动。

---

## 7. 拼音热路径与音节代数

### 7.1 核心输入缓冲区与拼写规则

1. **输入字符集 (`alphabet`)**：
   $$\{ \text{a–z},\ \text{A–Z},\ \backslash,\ \sim,\ ; \}$$
   前缀字符 `\`、`~`、`;` 必须注册进 `alphabet`，防止在单按时被分词器识别为标点直接上屏。
2. **缓冲区上限提升**：薄荷原版 `codeLengthLimit_processor: 25` 将在第 26 字符丢弃输入；kino 将其覆写为 **256** 字符。
3. **严格禁用模糊音与纠错**：强制设置 `translator/enable_correction: false`。
4. **拼写代数 (`speller/algebra`) 精简矩阵**：

```yaml
speller/algebra:
  - xlit|āáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜü|aaaaooooeeeeiiiiuuuuvvvvv| # 万象声调折算
  - xform/^ng$/eng/                                          # ng 特殊形式
  - xform/^([n])([g])$/$1e$2/
  - xform/^([ńňǹ])g$/eng/
  - xform/^[ńňǹ]$/en/
  - erase/^xx$/                                              # 擦除占位符
  - derive/^([zcs]h).+$/$1/                                  # 简拼：zh, ch, sh
  - abbrev/^([a-z]).+$/$1/                                   # 简拼：首字母
```

> **严格禁止**引入任何 `derive/...ng$/$1gn/`（如 `negn` $\rightarrow$ `neng`）、`hzi` $\rightarrow$ `zhi` 自动容错或 `en` / `eng`、`z` / `zh` 模糊规则。`nihao` 输出「你好」，而 `negn` 必须判定为非法拼音，绝不出「能」。

---

## 8. 前缀引导通道规范

### 8.1 处理器与分段器流水线

为保证前缀通道中的点号 `.` 与连字符 `-` 不被翻页键抢占，`overlay/rime_mint.custom.yaml` 对流水线进行了重构：

```
[键盘事件输入]
      │
      ▼
1. lua_processor (长度限制等)
2. ascii_composer & recognizer
3. lua_processor@*command_keys  <── 关键：必须位于 key_binder 之前拦截 `\arrow.l` 的点号与 `~-` 的长音
4. key_binder (快捷键与翻页)
5. speller / punctuator / selector
      │
      ▼
[分段器流水线]
1. ascii_segmentor / matcher
2. affix_segmentor@commands     <── 关键：必须位于 abc_segmentor 之前分流
3. affix_segmentor@latin
4. affix_segmentor@kana
5. abc_segmentor (中文拼音主分段器)
6. punct_segmentor / fallback_segmentor
```

---

### 8.1 `\` 符号与数学命令通道 (Command Draft)

- **触发规则**：正则表达式 `^\\[A-Za-z0-9.\\-=><!*~:|\\[\\]^_+(){}'?/#&`"]*$`
- **状态栏提示**：`[cmd]`
- **核心逻辑**：由 `overlay/lua/command_draft.lua` 加载动态生成的 `lua/commands_idx.lua` 2-gram 倒排索引。

#### A. 空查询行为（单按 `\` 键）

| 候选序号 | 上屏字符 | 注解说明 | 交互作用 |
| :--- | :--- | :--- | :--- |
| **1** | `、` | `\` | **系统默认顿号**（单按 `\` 立即产生顿号候选） |
| **2** | `\` | `backslash` | ASCII 反斜杠字符 |
| **3** | `＼` | `fullwidth` | 全角反斜杠字符 |

> `/` 键已被解绑，**不再**输出顿号。

#### B. 非空查询的四层匹配算法

匹配时对 ASCII 字母执行 `lower()`，按得分升序排列（得分越小优先级越高），单次查询最多输出 **20** 个去重候选：

| 优先级得分 | 匹配层级 | 匹配规则与行为 | 实例输入 $\rightarrow$ 命中目标 |
| :--- | :--- | :--- | :--- |
| **0** | **Exact (精确匹配)** | 编码全等匹配 | `\alpha` $\rightarrow$ `α`；`\to` $\rightarrow$ `→` |
| **1** | **Prefix (前缀匹配)** | 编码以前缀开头 | `\alp` $\rightarrow$ `α` (`alpha`) |
| **2** | **Dotted (点号段匹配)** | 编码包含 `.` 时，最后一段前缀匹配 | `\l` $\rightarrow$ `←` (`arrow.l`) |
| **3** | **Infix (2-gram 倒排)** | 查询长度 $\ge 2$ 时触发 2-gram 倒排索引 | `\pha` $\rightarrow$ `α` (`alpha`) |

**Unicode 检索约束**：Unicode 字符仅在查询长度 $\ge 4$ 时参与 Infix 检索，且构建索引时自动剥离 20 个英文高频虚词（如 `of`, `the`, `symbol`）。

---

### 8.2 `;` 拉丁重音通道 (Latin Accents)

- **触发规则**：正则表达式 `^;[A-Za-z?;]+$`
- **状态栏提示**：`[á]`
- **数据源**：`docs/drafts/latin-accents.csv`

| 键盘输入序列 | 输出字符 | 说明 |
| :--- | :--- | :--- |
| **单按 `;`** | *(无直接输出)* | 保持挂起等待后续字符，不污染文本框 |
| **`;n` / `;N`** | `ñ` / `Ñ` | 西班牙语/拉丁重音字符 |
| **`;a` / `;A`** | `á` / `Á` | 保持大小写敏感 |
| **`;;`** | `；` | 双击 `;` 快速输出中文全角分号 |
| **`;?`** | `¿` | 西班牙语倒问号 |

---

### 8.3 `~` 日文假名与维特比汉字分词 (Japanese Kana & Viterbi)

- **触发规则**：正则表达式 `^~[A-Za-z~-]+$`
- **状态栏提示**：`[かな]`
- **双路处理机制**：
  1. `lua_translator@*jp_draft`：罗马音最长匹配状态机 + Mozc Viterbi 句级分词。
  2. `table_translator@kana`：音节表兜底翻译器（`enable_sentence: false`）。

#### A. 罗马音转换状态机核心规则

1. **Pending-N 机制**：遇到 `n` 进入等待态。若后接元音/`y` 则合并音节（如 `nni` $\rightarrow$ `ん` + `に`）；若后接非元音或串尾则结算为单个 `ん`。
2. **促音判定**：遇到双写非 `n/y` 辅音（如 `kka`），自动消耗首个辅音并输出促音 `っ`。
3. **大小写首选反转**：小写输入以平假名为主首选，大写输入以片假名为主首选（`~ka` $\rightarrow$ `か`/`カ`；`~KA` $\rightarrow$ `カ`/`か`）。
4. **长音处理**：`~` 后的连字符 `-` 自动转换为日文长音符 `ー`（如 `~-` $\rightarrow$ `ー`）。

#### B. Kagiroi Mozc 维特比汉字分词契约

平假名序列由 `jp_draft.lua` 投递至 Kagiroi 维特比分词模块。分词引擎采用**延迟懒加载机制（Lazy Loading）**：在 Rime 初始化时不载入 90MB+ 大词库，仅在首次键入 `~` 时挂载。

- **权重模型**：保留 Mozc 原始原生权重（`cost = 1e8 * exp(weight)`），**严禁**人工干预种子词权重至 100000。
- **候选排版**：首选展示平/片假名，随后附带最多 2 条维特比最优切分汉字短语。

| 输入序列 | 假名输出 | 汉字候选包含项（按数字键选取） |
| :--- | :--- | :--- |
| `~watashiha` | `わたしは` / `ワタシハ` | `私は` |
| `~toukyouni` | `とうきょうに` / `トウキョウニ` | `東京に` |
| `~kyou` | `きょう` / `キョウ` | `今日` |
| `~konnichiha` | `こんにちは` / `コンニチハ` | `今日は` |

#### C. 独立方案「假名」

通过 `Ctrl+\`` 可切换至纯「假名」方案。该方案无需输入 `~` 前缀，直接键入 `ka` 即可输出 `か`/`カ`，适用于纯日文假名排版场景。

---

## 9. 键面标点权威映射

以 `proj-arc/cloverplus` 的 `half_shape` 配置为最高准则，并在 `rime_mint.custom.yaml` 中实现：

| 物理按键 | 单按/首选输出 | 扩展候选列表 / 成对状态机行为 | 特殊规则说明 |
| :--- | :--- | :--- | :--- |
| `,` | `，` | - | 供应商提交 |
| `.` | `。` | - | 供应商提交 |
| `/` | `/` | `/`，`÷` | **严禁映射为顿号** |
| `\` | `、` | 进入 `\` 命令通道（§8.1） | 注册进 `alphabet` |
| `;` | 进入拉丁通道 | 进入 `;` 拉丁通道（§8.2） | 注册进 `alphabet` |
| `~` | 进入日文通道 | 进入 `~` 日文通道（§8.3） | 单按不上屏 `～` |
| `'` | 成对 `「」` | 第一次按输出 `「`，第二次按输出 `」` | 采用薄荷直角引号样式 |
| `"` | 成对 `“”` | 第一次按输出 `“`，第二次按输出 `”` | 标准成对引号 |
| `[` | `「` | 菜单：`「 『 〚 〘 〖 【 〔 ［` | 括号选单，首选直角引号 |
| `]` | `」` | 菜单：`」 』 〛 〙 〗 】 〕 ］` | 闭合括号选单 |
| `{` / `}` | `『` / `』` | 菜单：`『 〖 ｛` / `』 〗 ｝` | 花括号选单 |
| `<` / `>` | `《` / `》` | 标准书名号 |  |
| `_` | `——` | 双破折号 |  |
| `*` | `×` | 乘号 |  |
| `$` | `￥` | 候选包含 `$` |  |
| `^` | `……` | 六点省略号 |  |

---

## 10. Emoji 过滤与注入规则

Emoji 功能以薄荷拼音 `opencc/emoji.txt` 为基础底库，由 `scripts/gen_overlay.py` 动态注入来自 CLDR 46 的扩展标注数据：

1. **长度门控策略**：仅允许触发词长度 $\ge 3$ 的中文字词（如 `开心果`）及纯拉丁词（如 `happy`）注入，**严禁**为 1~2 字的高频中文基础词（如 `你`、`好`、`中国`）绑定 Emoji 转换，防止在拼音热路径中产生视觉干扰。
2. **开关控制**：由 `emoji_suggestion` 独立控制，支持通过 `Control+Shift+E` 全局开关。

---

## 11. 继承的上游扩展功能

kino 完整保留了上游 oh-my-rime 的实用工具链：

| 快捷输入方式 | 触发前缀 / 按键 | 示例与输出效果 |
| :--- | :--- | :--- |
| **内置简易计算器** | `=` | 输入 `=128*1024` $\rightarrow$ 输出 `131072` |
| **公历转农历日期** | `N` + 数字 | 输入 `N20260827` $\rightarrow$ 输出对应农历与干支纪年 |
| **五笔反查** | `Uw` | 通过五笔编码反查汉字读音与字形 |
| **拆字/笔画反查** | `Uu` / `Ui` | 支持复杂生僻字拆解与笔画反查 |
| **Unicode 编码反查**| `Uc` | 输入十六进制 Unicode 输出对应字符 |
| **全半角切换** | `Shift+Space` / `Ctrl+Shift+3` | 切换全角与半角字符输入状态 |
| **简繁切换** | `Ctrl+Shift+1` | 快速切换简体中文与繁体中文输出模式 |

---

## 12. 手写源码与生成文件边界

| 资产类型 | 包含文件列表 | 维护准则 |
| :--- | :--- | :--- |
| **必须提交的手写源** | `overlay/*.custom.yaml`<br>`overlay/lua/*.lua`<br>`overlay/jp.dict.yaml`<br>`docs/drafts/*.csv`<br>`platform/` | 所有配置修改、Lua 特性增强与 CSV 词条维护均在此类文件中进行。 |
| **禁止提交的生成物** | `overlay/*.dict.yaml`（除 `jp.dict.yaml`）<br>`overlay/lua/commands_idx.lua`<br>`overlay/lua/jp_romaji.lua`<br>`overlay/opencc/emoji.txt`<br>`docs/drafts/commands.csv` | 由 `scripts/gen_overlay.py` 编译生成，已列入 `.gitignore`，严禁手动修改或提交。 |

---

## 13. 测试套件与验收清单

### 13.1 自动化测试执行

在仓库根目录下执行 pytest 回归测试：

```bash
python3 -m pytest tests/test_tables.py tests/test_gen_overlay.py tests/test_command_index.py tests/test_jp_romaji.py tests/test_emoji_opencc.py tests/test_overlay_branding.py tests/test_deploy.py -v
```

### 13.2 人工全量验收清单 (QA Checklist)

在部署有 kino 的机器上，打开文本编辑器，验证以下每一项交互行为：

- [ ] **1. 基础拼音与长句**：输入 `nihao` 输出 `你好`；连续输入超过 25 字符不发生截断（上限 256）。
- [ ] **2. 严格拼音分词**：输入 `negn` 不得出「能」。
- [ ] **3. Shift 原始上屏**：输入 `nihao` 时按左 `Shift`，直接上屏 `nihao`。
- [ ] **4. 符号与命令通道**：
  - [ ] 单按 `\` 第一候选为 `、`；`/` 不得输出 `、`。
  - [ ] 输入 `\alpha` / `\Alpha` 分别输出 `α` 与 `Α`，注解包含方言来源。
  - [ ] 输入 `\a` 输出 `α`（注解 `a [lean]`）；输入 `\pha` 输出 `α`（2-gram 检索生效）。
  - [ ] 输入 `\arrow.l` 时能够正常键入 `.`，第一候选为 `←`。
  - [ ] 输入 `\->` 输出 `→`；输入 `\forall` 输出 `∀`；输入 `\^2` 输出 `²`。
- [ ] **5. 拉丁重音通道**：输入 `;n` 输出 `ñ`；输入 `;;` 输出 `；`；方案选单中不出现 Latin。
- [ ] **6. 日语与维特比分词**：
  - [ ] 输入 `~ka` 输出 `か`，输入 `~KA` 输出 `カ`。
  - [ ] 输入 `~watashiha` 候选列表包含 `わたしは` 与 `私は`。
  - [ ] 输入 `~toukyouni` 候选列表包含 `東京に`；输入 `~kyou` 包含 `今日`。
  - [ ] 候选词文本纯净，不包含 `|1913` 等内部词库 ID。
- [ ] **7. 标点成对状态机**：按 `'` 第一次输出 `「`，第二次输出 `」`；按 `[` 弹出直角引号选单。
- [ ] **8. 独立假名方案**：按 `Ctrl+\`` 切换至「假名」，直接输入 `ka` 输出 `か`。
- [ ] **9. 页面排版规格**：候选词列表每页固定 10 项；界面为 Nord 深色纵向排列。
- [ ] **10. 功能开关隔离**：关闭 `kino_typst` 后，`\` 检索中不再出现 Typst 专用符号；关闭 `kino_japanese` 后 `~` 停用，但独立「假名」方案仍可正常使用。

---

## 14. 关联文档导航

- [系统安装、多平台部署与环境配置](../README.md) (`README.md`)
- [文档体系架构与 SSOT 仲裁准则](README.md) (`docs/README.md`)
- [码表结构、2-gram 索引与构建性能规范](drafts/README.md) (`docs/drafts/README.md`)
- [日文 Viterbi 分词与连接矩阵底层契约](jp-viterbi.md) (`docs/jp-viterbi.md`)
