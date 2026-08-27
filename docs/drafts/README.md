# 码表数据模式与编译器工程规范

[简体中文](README.md) | [English](README.en.md)

| 属性 | 规格说明 |
| :--- | :--- |
| **所属模块** | **kino** 数据工程与码表编译子系统 |
| **文档职责** | 规范 `docs/drafts/*.csv` 数据建模规范、编译器流水线契约、2-gram 倒排索引生成算法、OpenCC 注入规则与性能预算 |
| **不包含内容** | 用户界面候选词排版（见 [`../kino.md`](../kino.md)）、操作系统安装步骤（见根目录 [`../../README.md`](../../README.md)） |
| **文档状态** | 现行权威数据工程标准（Active Normative Data Specification） |
| **修订日期** | 2026-08-27 |

---

## 1. 编译管线与架构拓扑

kino 采用**离线编译、运行时零解析**的数据架构设计。所有结构化符号、假名与按键映射源数据统一存放于 `docs/drafts/*.csv` 中，通过 `scripts/gen_overlay.py` 离线预编译为 Rime 原生字典、Lua 倒排索引及 OpenCC 词表：

```
[源数据层] docs/drafts/*.csv
   ├── kana.csv             (假名音节源)
   ├── latin-accents.csv    (拉丁重音快照)
   ├── math-symbols.csv     (数学/命令宽表)
   ├── typst-extra.csv      (Typst 函数与空格)
   ├── punctuation.csv      (标点映射契约)
   ├── brackets.csv         (括号选单源)
   └── emoji.csv            (CLDR 46 标注)
                 │
                 ▼ 离线预编译 (scripts/gen_overlay.py)
[生成物层] overlay/
   ├── kana.dict.yaml          (假名音节码表，.gitignore)
   ├── latin.dict.yaml         (拉丁重音码表，.gitignore)
   ├── commands.dict.yaml      (短 ASCII 精确退化码表，.gitignore)
   ├── lua/commands_idx.lua    (2-gram 倒排索引表，.gitignore)
   ├── lua/jp_romaji.lua       (罗马音状态机最长匹配表，.gitignore)
   └── opencc/emoji.txt        (Emoji 补丁词表，.gitignore)
                 │
                 ▼ 一键部署与资产分发 (scripts/deploy.py)
[运行时层] 用户 Rime 目录 (~/.local/share/fcitx5/rime 或 %APPDATA%\Rime)
   ├── 同步上游 oh-my-rime 基础词库
   ├── 覆盖应用 overlay/ 生成配置
   └── 挂载 kagiroi.mozc.dict.yaml (~58MB) 与 kagiroi_matrix (~98MB)
```

### 核心开发红线

1. **严禁手动编辑生成物**：`overlay/` 下带有 `.gitignore` 属性的编译产物必须全部通过构建脚本生成。
2. **严禁写回历史合并表**：禁止将多方言宽表反向导出为旧版 `docs/drafts/commands.csv`。
3. **禁止提交中间过程文件**：`kana.expanded.csv` 与 `emoji.core.csv` 等已并入宽表，严禁提交至 Git。
4. **多值字段统一分隔符**：同一单元格内的多个等价别名或多方言编码，一律使用 ` | `（前后带空格的竖线）分隔。

---

## 2. 数据源清单与分类

| 数据文件 | 资产类型 | 核心字段结构 | 维护说明 |
| :--- | :--- | :--- | :--- |
| **`math-symbols.csv`** | 手写事实源宽表 | `glyph,latex,latex_alias,katex,typst,typst_shorthand,lean,lean_shorthand,mma,mma_alias` | 数学符号核心事实源。单行对应唯一定义字符（Glyph），横向展开各大生态方言。 |
| **`typst-extra.csv`** | 扩展事实源 | `code,kind,preview,description` | 专用于无具体单字符 Glyph 的 Typst 函数（`typst-fn`）、空格（`typst-space`）及算子（`typst-op`）。 |
| **`kana.csv`** | 手写事实源 | `hira,kata,codes,family,notes` | 日文假名基础音节与罗马音对照表。 |
| **`punctuation.csv`** | 手写事实源 | `key,half,full,notes,recommend` | 键面标点半角/全角映射及候选推荐集。 |
| **`brackets.csv`** | 手写事实源 | `type,left,right,notes` | 括号、引号及特殊围套符号库。 |
| **`latin-accents.csv`** | 导入快照 | `glyph,codes` | 拉丁重音字母与西里尔/特殊字母映射表。 |
| **`emoji.csv`** | 导入快照 | `emoji,codes_zh,codes_en` | 基于 Unicode CLDR 46 的 Emoji 多语言标注快照。 |
| **`import/lean-abbreviations.json`** | 官方导入快照 | JSON 键值对 | Lean 官方缩写快照，仅由 `import_math_symbols.py` 消费。 |
| **`import/mma-named.json`** | 官方导入快照 | JSON 键值对 | Mathematica `NamedCharacter` 映射，仅由导入脚本消费。 |
| **`import/katex-symbols.json`** | 官方导入快照 | JSON 结构体 | KaTeX `symbols.ts` 提取快照，仅供导入脚本同步。 |

---

## 3. 详细模式与字段契约规范

### 3.1 `kana.csv`（假名音节源）

- **`codes`**：支持训令式（Kunrei-shiki）与赫本式（Hepburn）并存，使用 ` | ` 分隔（如 `si | shi`）。
- **`family`**：音节族分类，枚举值必须为 `gojuon`（五十音）、`youon`（拗音）、`sokuon`（促音）、`small`（小假名）。
- **特殊过滤与健全性规则**：
  - `kata == "?"` 的行在生成时自动跳过（特殊外来语假名由独立条目定义）。
  - 剔除历史脏数据 `ccye`。
  - 独立 `n` / `nn` 不进入最长匹配词典（由运行时 `jp_draft.lua` 状态机的 Pending-N 逻辑专门调度）。
  - `family == "sokuon"` 且编码以 `nn` 开头的行不进词典，防止出现 `konnichiha` $\rightarrow$ `こっにちは` 的错误促音切分。

### 3.2 `latin-accents.csv`（拉丁重音）

- **编码格式**：原始 CSV 中的 `codes` 带有前导分号（如 `;a` $\rightarrow$ `á`，`;;` $\rightarrow$ `；`）。
- **编译器行为**：`gen_overlay.py` 负责剔除前导 `;`，并在生成的 `overlay/latin.dict.yaml` 中配置 `prefix: ";"`。
- **大小写对齐**：末尾字母大写映射为对应大写字符（如 `;A` $\rightarrow$ `Á`）。
- **空行过滤**：自动过滤 Glyph 本身为 ASCII `;` 的无意义恒等映射。

### 3.3 `math-symbols.csv` 与 `typst-extra.csv`（符号与命令宽表）

`math-symbols.csv` 包含 10 个标准列。生成器在解析时将其横向展开为以下归一化类型（Kind）：

| 归一化类型 (Kind) | 数据来源 | 关联功能开关 | 匹配与注解说明 |
| :--- | :--- | :--- | :--- |
| **`latex`** | `latex` 列 | `kino_latex` | TeX/AMS/unicode-math 原生控制序列（如 `\alpha`） |
| **`latex-alias`** | `latex_alias` 列 | `kino_latex` | 社区常用自造别名与符号宏（注解呈现为 `[latex*]`） |
| **`katex`** | `katex` 列 | `kino_katex` | KaTeX 支持的专用数学宏 |
| **`typst-sym`** | `typst` 列 | `kino_typst` | Typst 标准符号标识符（如 `arrow.r`） |
| **`typst-shorthand`** | `typst_shorthand` 列 | `kino_typst` | Typst 简写形式（如 `->`, `=>`） |
| **`typst-fn` / `typst-space` / `typst-op`** | `typst-extra.csv` | `kino_typst` | Typst 函数调用与空间符号（如 `sin`, `quad`） |
| **`lean`** | `lean` 列 | `kino_lean` | Lean 4 官方输入法控制宏 |
| **`lean-shorthand`** | `lean_shorthand` 列 | `kino_lean` | Lean 简写别名 |
| **`mma`** | `mma` 列 | `kino_mma` | Mathematica `NamedCharacter` 标识符（如 `Alpha`，不带括号） |
| **`mma-alias`** | `mma_alias` 列 | `kino_mma` | Mathematica 符号简写（如 `->`） |
| **`unicode`** | Python `unicodedata` 紧凑名 | 恒开 (无开关) | 基于 Unicode 标准名称构建的全局紧凑词条 |

#### 2-Gram 倒排索引生成规则

1. **分词与大小写**：所有 ASCII 字母在建立索引与运行时检索时均执行 `lower()` 归一化。
2. **2-Gram 窗口**：固定参数 $\text{GRAM\_N} = 2$。对所有长度 $\ge 2$ 的连续子串建立倒排拉链（Posting List）。
3. **Unicode 虚词停用词表**：在为 Unicode 描述文本构建索引时，强制剔除以下 20 个高频虚词及长度 $< 4$ 的短词：
   ```
   of, the, and, or, to, in, on, a, an, with, for, from, by, at, as, is, small, letter, capital, sign, symbol
   ```
4. **拉链不截断**：为保证数学符号召回率，索引拉链数组完全展开，不设截断上限。

### 3.4 `emoji.csv`（CLDR 46 标注）

1. **底库继承**：编译器首先完整继承 `proj-ref/oh-my-rime/opencc/emoji.txt` 的基础 Emoji 映射。
2. **高频冲突门控**：向基础库追加 `emoji.csv` 的标注数据时，执行硬性过滤准则：
   - 纯中文字词长度必须 $\ge 3$（如 `开心果` $\rightarrow$ 🥑）。
   - 纯拉丁字母词长度必须 $\ge 3$（如 `cat` $\rightarrow$ 🐱）。
   - 严禁包含 1~2 字的高频中文汉字（如 `你`、`好`、`大`、`中`），彻底消除 Emoji 污染核心中文拼音热路径的风险。

---

## 4. 构建、部署与回归验证

### 4.1 编译与生成工作流

```bash
# 1. (可选) 从离线快照刷新 Lean/MMA 宽表列 (不发起网络请求)
python3 scripts/import_math_symbols.py --lean-only

# 2. 执行全量码表编译与索引生成
python3 scripts/gen_overlay.py --root . --overlay overlay

# 3. 健全性检查：确保未产生非法合并文件
test ! -f docs/drafts/commands.csv && echo "Sanity Check Passed."

# 4. 执行自动化测试回归
python3 -m pytest tests/ -v

# 5. 执行一键部署
./scripts/deploy.sh
```

---

## 5. 命令检索算法与性能预算

### 5.1 四层匹配优先级模型

在 `overlay/lua/command_draft.lua` 运行时中，候选词严格按得分降序归入四层结构（得分越低优先级越高）：

```
[用户输入 \query]
      │
      ├── 0: Exact Match   ──> 全等匹配 (如 \alpha == alpha)
      │
      ├── 1: Prefix Match  ──> 前缀匹配 (如 \alp -> alpha)
      │
      ├── 2: Dotted Match  ──> 包含 . 时最后一段匹配 (如 \l -> arrow.l)
      │
      └── 3: Infix (2-gram)──> 2-gram 倒排拉链求交 (如 \pha -> alpha)
```

### 5.2 运行时性能硬预算 (Performance Budget)

| 监控指标 | 性能预算上限 | 违规设计与禁止操作 (Anti-Patterns) |
| :--- | :--- | :--- |
| **拼音热路径延迟** | $\le 1.0\text{ ms}$ | 严禁在拼音热路径上挂载全局 Lua Filter；严禁在拼音流中执行编辑距离纠错。 |
| **`\` 命令检索耗时** | $\le 5.0\text{ ms}$ | 严禁在 Lua 运行时中动态扫盘解析 CSV 文件；所有查询必须直接命中 `commands_idx.lua` 内存表。 |
| **内存占用预算** | $\le 30\text{ MB}$ (基础态) | 严禁在 `commands.dict.yaml` 中暴力枚举展开所有 Infix 变体；严禁给上万条目的命令码表开启拼读补全（`enable_completion`）。 |

---

## 6. 日文模型资产与分发契约

日文大规模模型由 `proj-ref/Insomnia1437-rime` 提供，不属于 CSV 生成体系：

| 文件路径 | 部署后用户目录位置 | 技术规格与契约 |
| :--- | :--- | :--- |
| `proj-ref/Insomnia1437-rime/kagiroi.mozc.dict.yaml` | `kagiroi.mozc.dict.yaml` (~58MB) | 必须完整保留 `表面\|left right` 格式及 Mozc 原生权重；**严禁剥离 ID 或篡改种子词权重**。 |
| `proj-ref/Insomnia1437-rime/kagiroi_matrix.dict.yaml` | `kagiroi_matrix.dict.yaml` (~98MB) | Mozc Bigram 连接代价矩阵。首次编译需要 1~2 分钟。 |
| `proj-ref/Insomnia1437-rime/lua/kagiroi/*` | `lua/kagiroi/` | 包含 `kagiroi_viterbi`, `segmenter`, `lru`, `priority_queue`。不部署独立 translator 包装。 |

`overlay/jp.dict.yaml` 作为包装层，内部仅声明 `import_tables: [kagiroi.mozc]`。具体底层接口契约参见 [`jp-viterbi.md`](../jp-viterbi.md)。

---

## 7. 上游依赖与只读参考源

- **[`proj-ref/oh-my-rime`](https://github.com/Mintimate/oh-my-rime)**：上游薄荷拼音主仓库（部署时整树同步为基础底座）。
- **[`proj-ref/Insomnia1437-rime`](https://github.com/Insomnia1437/rime)**：日文 Mozc 词典与 Viterbi 连接代价矩阵事实源。
- **[`proj-ref/rime-spanish`](https://github.com/gkovacs/rime-spanish)**：拉丁重音 QWERTY 键盘映射参考源。
- **`proj-arc/cloverplus`**：历史四叶草方案归档（上游 [fkxxyz/rime-cloverpinyin](https://github.com/fkxxyz/rime-cloverpinyin)），提供标点符号与部分数学符号的历史参考。

---

## 8. 关联文档导航

- [系统安装、多平台部署与环境配置](../../README.md) (`README.md`)
- [文档体系架构与 SSOT 仲裁准则](../README.md) (`docs/README.md`)
- [kino 完整按键交互契约与引擎规范](../kino.md) (`docs/kino.md`)
- [日文 Viterbi 引擎与连接矩阵底层契约](../jp-viterbi.md) (`docs/jp-viterbi.md`)
- [命令宽表与 feature_gate 种类契约](../math-symbols.md) (`docs/math-symbols.md`)
