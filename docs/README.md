# kino 文档体系与治理架构

[简体中文](README.md) | [English](README.en.md)

| 属性 | 规格说明 |
| :--- | :--- |
| **所属项目** | **kino**（Rime Overlay 叠层方案，方案标识：`rime_mint`） |
| **代码仓库** | `rime-kino` |
| **文档职责** | 阐明项目完整文档体系拓扑、单一事实源（SSOT）权威层级、冲突仲裁机制与角色阅读路径 |
| **不包含内容** | 具体操作系统安装命令（见根目录 `README.md`）、详细按键交互规则（见 `kino.md`）、CSV 数据列规范（见 `drafts/README.md`） |
| **文档状态** | 现行权威（Active Normative） |
| **修订日期** | 2026-08-27 |

---

## 1. 架构定位与设计哲学

kino 项目采用严格的**单一事实源（Single Source of Truth, SSOT）**与**模块自洽**原则进行文档治理：

1. **单篇自洽（Self-Contained）**：每篇文档在其定义的职责边界内必须完全自洽，读者仅凭当前文档即可完整闭环执行其标题所承诺的技术任务，无需跨文档跳转搜寻必要步骤。
2. **权威分权（Separation of Authority）**：每一项技术决策、接口契约和配置参数均有且仅有一个最高仲裁文档。
3. **消除冗余与分歧（Zero-Divergence）**：禁止在非权威文档中二次复制或重新解释规则细节，跨领域技术关联一律采用显式链接索引。

---

## 2. 文档拓扑与职责矩阵

```
                                  docs/README.md
                          (文档架构地图与 SSOT 仲裁中枢)
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
     README.md                      docs/kino.md               docs/drafts/README.md
(安装/部署/系统级排错)          (按键交互/通道行为规范)         (数据模式/索引编译/性能约束)
         │                               │                               │
         ▼                               ▼                               ▼
   系统依赖/环境变量              按键到上屏/Lua通道               CSV列规范/2-gram/OpenCC
```

### 文档职责划分与边界

| 文档路径 | 目标读者 | 权威负责范围 | 显式非职责范围 |
| :--- | :--- | :--- | :--- |
| **[`../README.md`](../README.md)**<br>([English](../README.en.md)) | 首次安装者、系统管理员、CI/CD 维护者 | 仓库克隆、子模块依赖、跨平台环境配置、部署脚本、验收最小集、系统排错 | 详细全量按键映射契约、CSV 内部数据结构 |
| **[`kino.md`](kino.md)**<br>([English](kino.en.md)) | 终端使用者、交互开发者、QA 验收人员 | 按键到上屏完整契约、前缀通道（`\` / `;` / `~`）、候选窗排版、标点与 Emoji 规则、完整人测清单 | Linux 系统软件包管理、环境变量导出步骤 |
| **[`drafts/README.md`](drafts/README.md)**<br>([English](drafts/README.en.md)) | 码表维护者、数据工程师、编译器开发者 | `docs/drafts/*.csv` 列定义、生成器编译管线、2-gram 倒排索引结构、OpenCC 规则、性能预算 | 运行时用户界面排版与视觉展现（以 `kino.md` 为准） |
| **[`jp-viterbi.md`](jp-viterbi.md)** | 引擎维护者 | Mozc 词库格式、Viterbi 连接代价、日文 Lua 部署契约 | 用户可见按键顺序（以 `kino.md` 为准） |
| **`drafts/*.csv`** | 自动化生成器、数据维护者 | 码表底层结构化原始数据源 | 文本交互叙事与逻辑描述 |

---

## 3. 权威仲裁与单一事实源（SSOT）准则

当不同文档、代码注释或历史方案在某项技术细节上出现分歧时，必须严格依照下表裁定最终权威：

| 技术领域 / 决策主题 | 唯一最高权威（SSOT） | 仲裁与执行准则 |
| :--- | :--- | :--- |
| **系统依赖、部署命令、环境变量、OS 排错** | 仓库根目录 `README.md` | 以根目录部署脚本与平台说明为准，禁止在其他文档修改安装依赖步骤。 |
| **按键序列、前缀通道、候选窗与预编辑、Shift 行为** | `docs/kino.md` | 用户交互、快捷键、候选词展示形态与注释格式以 `kino.md` 为唯一标准。 |
| **CSV 列结构、生成文件白名单、2-gram 索引、OpenCC 限制** | `docs/drafts/README.md` | 数据管道、字段映射、文件提交边界与构建性能预算以 `drafts/README.md` 为准。 |
| **Mozc 词库格式、Viterbi 权重代价、日文 Lua 内存管理** | `docs/jp-viterbi.md` | 日文引擎与部署层的数据边界以 Viterbi 规范为准（严禁私自修改原生权重）。 |

---

## 4. 角色阅读路径推荐

### 路径 A：普通用户与日常打字者
1. 阅读根目录 **[`README.md`](../README.md)** 完成环境安装与一键部署。
2. 查阅 **[`docs/kino.md`](kino.md)** 掌握前缀快捷通道（LaTeX 数学符号、拉丁重音、日文假名及 Viterbi 汉字）。

### 路径 B：符号与码表贡献者
1. 阅读 **[`docs/drafts/README.md`](drafts/README.md)** 了解 CSV 字段模型与符号分类规范。
2. 对照 **[`docs/kino.md`](kino.md)** 确认符号在用户界面中的展示注释与去重行为。
3. 执行 `python3 scripts/gen_overlay.py` 并运行 `pytest tests/` 完成测试回归。

### 路径 C：核心引擎与跨平台维护者
1. 通读 **[`README.md`](../README.md)** 与 **[`docs/kino.md`](kino.md)** 掌握平台不变量（如 `PreeditMode="Do not show"`、`SwitchInputMethodBehavior="Commit raw input"`）。
2. 深入阅读 **[`jp-viterbi.md`](jp-viterbi.md)** 掌握 Mozc 字典与连接矩阵的底层生命周期管理。

---

## 5. 外部与上游参考资源

网页渲染版见 [epistemelody.github.io/rime-kino](https://epistemelody.github.io/rime-kino/)。

- **薄荷拼音上游**：[`proj-ref/oh-my-rime`](https://github.com/Mintimate/oh-my-rime)（只读 Vendor 子模块，提供中文基础词库与主方案）。
- **Mozc 日文模型**：[`proj-ref/Insomnia1437-rime`](https://github.com/Insomnia1437/rime)（只读 Vendor 子模块，提供日文大词典与连接矩阵）。
- **双拼编排参考**：[`proj-ref/iamcheyan-rime`](https://github.com/iamcheyan/rime)
- **拼音日文参考**：[`proj-ref/rime-pinyin-jap`](https://github.com/tumuyan/rime-pinyin-jap)
- **拉丁重音参考**：[`proj-ref/rime-spanish`](https://github.com/gkovacs/rime-spanish)
- **四叶草配置归档**：`proj-arc/cloverplus`（历史归档参考，非运行代码；上游为 [fkxxyz/rime-cloverpinyin](https://github.com/fkxxyz/rime-cloverpinyin)）。
