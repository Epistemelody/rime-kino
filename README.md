# kino

[简体中文](README.md) | [English](README.en.md) | [网页文档](https://epistemelody.github.io/rime-kino/)

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg?style=flat-square)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform: Linux, Windows & macOS](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-informational.svg?style=flat-square)](https://rime.im/download/)
[![Engine: Rime & librime-lua](https://img.shields.io/badge/Engine-Rime%20%2B%20librime--lua-orange.svg?style=flat-square)](https://rime.im/)
[![Tests: 68 Passed](https://img.shields.io/badge/Tests-68%20Passed-brightgreen.svg?style=flat-square)](tests/)

> 一套无缝集成**中文拼音、日文假名/汉字（Viterbi）、拉丁重音、多生态数学符号（LaTeX / Typst / Lean / MMA）与成对标点**的高性能多通道 Rime 输入法叠层框架。

**kino**（读音：`/ˈkiːnoʊ/`，*Kinetic Input Normalized Overlay*）是一个构建于 [oh-my-rime (薄荷拼音)](https://github.com/Mintimate/oh-my-rime) 之上的现代多通道 Rime 叠层方案。在保障中文拼音原生极速响应的同时，通过离线 2-gram 倒排索引与无锁 Lua 运行时，开箱提供**中英混输、日文假名与维特比分词、拉丁重音直出、多方言数学符号检索（LaTeX / KaTeX / Typst / Lean 4 / Mathematica / Unicode）、成对标点与低干扰 Emoji** 等全套能力。

<p align="center">
  <img src="assets/kino-preview.png" alt="kino preview" width="100%">
</p>

---

## 特性概览 (Features)

- **严格拼音热路径**：禁用一切模糊音与错位容错代数（`negn` 严格不出「能」）；输入缓冲区扩容至 256 字符。
- **多生态数学符号 (`\`)**：单表覆盖 LaTeX / KaTeX / Typst / Lean 4 / Mathematica / Unicode，支持 4 级计分检索（精确/前缀/点号段/2-gram 倒排）与方言合并注解；单按 `\` 输出顿号 `、`。
- **拉丁重音直出 (`;`)**：`;n` $\to$ `ñ`，`;a` $\to$ `á`，`;?` $\to$ `¿`；双击 `;;` 输出全角分号；单按分号挂起不污染文档。
- **维特比分词日文引擎 (`~`)**：确定性罗马音 DFA 状态机（Pending-N、促音、长音、大小写翻转）+ Mozc 连接矩阵全局最优 Viterbi 分词；支持独立「假名」方案。
- **成对标点与括号选单**：`'` 依次输出 `「` 与 `」`；`"` 依次输出 `“` 与 `”`；`[` 唤出直角与学术括号选单。
- **低干扰 Emoji 联想**：集成 CLDR 46 标注，实施 $\ge 3$ 字符长度门控，彻底剔除 1~2 字高频中文词的表情干扰。
- **正交功能开关**：提供 8 组独立运行期 Feature Flags，状态自动持久化。
- **统一 Nord 极夜美学**：Linux (Fcitx5)、Windows (小狼毫) 与 macOS (鼠须管) 统一预设 Nord Polar Night 深色垂直排版（10 候选/页），严格无行内预编辑污染。

---

## 前置准备 (Prerequisites)

在部署 kino 叠层前，需确保宿主系统已就绪对应的 Rime 输入法前端与 Lua 运行时扩展：

### 1. Linux (Fcitx5 架构)
- **输入法框架**：需安装 `fcitx5` 与 `fcitx5-rime`。
- **Lua 运行时支持**：kino 依赖 `librime-lua` 执行 2-gram 倒排索引检索与 Viterbi 算法，必须确保该插件已安装。
- **系统环境变量**：将以下变量写入 `~/.config/environment.d/fcitx5.conf`（或 `~/.pam_environment` / `~/.xprofile`）并注销重新登录：
  ```ini
  GTK_IM_MODULE=fcitx
  QT_IM_MODULE=fcitx
  XMODIFIERS=@im=fcitx
  ```
- **添加输入法**：打开 `fcitx5-configtool`，在输入法列表中添加 **中州韵 (Rime)**。

### 2. Windows (小狼毫 Weasel)
- 从 [Rime 官方下载页](https://rime.im/download/) 或 [Weasel Releases](https://github.com/rime/weasel/releases) 获取并运行最新版 **小狼毫安装包**（推荐 0.16.0+，已内嵌 librime-lua 运行时）。
- 安装完成后，系统托盘区域将常驻小狼毫服务图标。

### 3. macOS (鼠须管 Squirrel)
- 通过 Homebrew 安装：`brew install --cask squirrel`，或从 [Rime 官方下载页](https://rime.im/download/) / [Squirrel Releases](https://github.com/rime/squirrel/releases) 获取最新版（建议使用已内嵌 librime-lua 的近期版本）。
- 安装完成后，菜单栏将出现鼠须管图标。

---

## 仓库布局 (Structure)

```
rime-kino/
├── assets/                       # 项目主视觉图与媒体资源 (kino-preview.png)
├── overlay/                      # 叠层配置与 Lua 扩展 (custom.yaml, lua/)
├── platform/fcitx5/              # Linux Fcitx5 专用配置与 Nord 主题
├── docs/                         # 项目技术文档体系 (kino.md, drafts/README.md)
├── scripts/                      # 码表编译器 (gen_overlay.py) 与一键部署脚本 (deploy.py)
├── proj-ref/                     # 运行时子模块 + 可选研究参考
└── tests/                        # 自动化测试套件
```

---

## 快速上手 (Quickstart)

### 1. 克隆仓库与子模块

部署只需要两个**运行时**子模块：`oh-my-rime`（拼音底座）与 `Insomnia1437-rime`（日文 Mozc）。其余 `proj-ref/*` 是研究参考，默认不下载。

```bash
git clone --recurse-submodules --shallow-submodules https://github.com/Epistemelody/rime-kino.git
cd rime-kino
```

`--shallow-submodules` 只取当前 pinned 提交（薄荷拼音完整历史约 400MB）。`.gitmodules` 对研究参考设了 `update = none`，因此 `--recurse-submodules` 不会拉取 `rime-ice` / `iamcheyan-rime` / `rime-pinyin-jap` / `rime-spanish`。

已有仓库、或 clone 时忘了子模块：

```bash
python3 scripts/init_submodules.py          # 仅运行时，depth 1
python3 scripts/init_submodules.py --all    # 另含研究参考
```

### 2. 部署到系统

#### Linux (主流发行版)

根据所用发行版安装依赖软件包（注意：**librime-lua** 为必要依赖）：

```bash
# Fedora / RHEL
sudo dnf install -y fcitx5 fcitx5-rime librime-lua fcitx5-configtool python3

# Arch Linux / Manjaro
sudo pacman -S --needed fcitx5 fcitx5-rime librime-lua fcitx5-configtool python

# Debian / Ubuntu (>= 24.04)
sudo apt update && sudo apt install -y fcitx5 fcitx5-rime librime-plugin-lua fcitx5-config-qt python3

# openSUSE (Tumbleweed / Leap)
sudo zypper install -y fcitx5 fcitx5-rime librime-lua fcitx5-config-tool python3
```

执行一键编译与部署脚本：

```bash
./scripts/deploy.sh
```

#### Windows (小狼毫 Weasel)

```powershell
# 在 PowerShell 中执行部署，随后在系统托盘右键小狼毫点击「重新部署」
.\scripts\deploy.ps1
```

#### macOS (鼠须管 Squirrel)

```bash
./scripts/deploy.sh
```

部署完成后，点击菜单栏鼠须管图标并选择「重新部署」。用户目录为 `~/Library/Rime`。

---

## 交互速查 (Cheat Sheet)

| 输入模式 | 按键示例 | 输出结果 | 交互说明 |
| :--- | :--- | :--- | :--- |
| **拼音热路径** | `nihao` | `你好` | 编码位于窗口顶部，Space 上屏 |
| **中英切换** | 输入中按 `Shift_L` | `nihao` | **Raw Commit**：直接上屏原始 ASCII 字符 |
| **顿号与命令** | 单按 `\` / `\alpha` / `\->` | `、` / `α` / `→` | 注解显示 `[latex katex typst lean mma]`；`/` 保持斜杠 |
| **Typst 点号** | `\arrow.l` | `←` | 点号参与检索，不触发翻页 |
| **拉丁重音** | `;n` / `;a` / `;;` | `ñ` / `á` / `；` | 单按 `;` 挂起不上屏 |
| **日文假名/汉字**| `~ka` / `~watashiha` | `か` / `私は` | 罗马音连打 + Mozc 维特比最优切分 |
| **成对引号/括号**| 连续按 `'` / 按 `[` | `「」` / 选单 | 成对直角引号；`[` 唤出多项括号选单 |
| **方案选单** | `Ctrl+\`` | `kino` / `假名` | 切换默认方案或独立假名方案 |

---

## 路线图 (Roadmap)

- [ ] **多语种短语与外语词库扩展 (Multilingual Lexicons)**：
  - 引入现代**英语高频短语与专业技术术语**词库（支持智能补全）。
  - 支持**法语 (French)、德语 (German)、西班牙语 (Spanish)** 等欧洲语言的常用词汇、变音符号短语及专业名词直出。
- [ ] **自适应 Viterbi 分词与词频记忆 (Adaptive Learning Cache)**：
  - 针对日文长句输入引入本地用户高频词优先转移缓存，减少二次选词成本。
- [ ] **跨平台可视化配置工具 (Interactive Configuration Dashboard)**：
  - 提供轻量 Web / TUI 控制面板，支持 8 组 Feature Flags 开关与主题色板的一键热加载。

---

## 测试与质量 (Testing)

```bash
.venv/bin/pytest tests/ -q
# 65 passed in ~3s
```

---

## 完整文档导航 (Documentation)

- [网页版文档（展示与说明）](https://epistemelody.github.io/rime-kino/)
- [文档体系与 SSOT 治理规范](docs/README.md) (`docs/README.md`)
- [kino 完整按键交互契约与引擎手册](docs/kino.md) (`docs/kino.md`)
- [码表数据模式、2-Gram 索引与性能规范](docs/drafts/README.md) (`docs/drafts/README.md`)
- [日文 Viterbi 引擎与连接矩阵契约](docs/jp-viterbi.md) (`docs/jp-viterbi.md`)
- [数学符号宽表与命令管线](docs/math-symbols.md) (`docs/math-symbols.md`)

---

## 关联项目与致谢 (Relevant Projects)

- [oh-my-rime (薄荷拼音)](https://github.com/Mintimate/oh-my-rime)：中文拼音基础方案与多词典生态（`proj-ref/oh-my-rime`）。
- [Insomnia1437/rime (カギロイ)](https://github.com/Insomnia1437/rime)：Mozc 日文大词库与 Viterbi 转移矩阵事实源（`proj-ref/Insomnia1437-rime`）。
- [iamcheyan/rime](https://github.com/iamcheyan/rime)：双拼与方案编排参考（`proj-ref/iamcheyan-rime`，研究参考，默认不克隆）。
- [tumuyan/rime-pinyin-jap](https://github.com/tumuyan/rime-pinyin-jap)：拼音日文方案参考（`proj-ref/rime-pinyin-jap`，研究参考，默认不克隆）。
- [gkovacs/rime-spanish](https://github.com/gkovacs/rime-spanish)：拉丁重音 `;` 键位参考（`proj-ref/rime-spanish`，研究参考，默认不克隆）。
- [iDvel/rime-ice](https://github.com/iDvel/rime-ice)：雾凇拼音参考（`proj-ref/rime-ice`，研究参考，默认不克隆）。
- [fkxxyz/rime-cloverpinyin (四叶草拼音)](https://github.com/fkxxyz/rime-cloverpinyin)：拼音习惯与成对标点参考。
- [shenlebantongying/rime_latex](https://github.com/shenlebantongying/rime_latex)：LaTeX 数学符号方案参考。
- `proj-arc/cloverplus`：基于四叶草拼音与 rime_latex 的本地定制归档（历史参考，非运行时代码）。
- [hchunhui/librime-lua](https://github.com/hchunhui/librime-lua)：Rime Lua 运行时引擎。

---

## 许可协议 (License) & 引用 (Citation)

本项目源码基于 **[GPL-3.0](https://www.gnu.org/licenses/gpl-3.0)** 许可协议开源。

```bibtex
@software{epistemelody2026kino,
  author       = {Felidz and {Epistemelody}},
  title        = {kino: A Modern Table-Driven Multi-Channel Rime Input Overlay Framework},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/Epistemelody/rime-kino}}
}
```
