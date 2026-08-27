# kino

多通道 Rime 叠层：**拼音 · 日文 Viterbi · 拉丁重音 · 数学符号**。

<p align="center">
  <img src="../assets/kino-preview.png" alt="kino preview" width="100%">
</p>

[GitHub](https://github.com/Epistemelody/rime-kino) · [English README](../README.en.md) · [完整安装说明](../README.md)

## 平台

Linux（Fcitx5）· Windows（小狼毫）· macOS（鼠须管）

```bash
git clone --recurse-submodules --shallow-submodules https://github.com/Epistemelody/rime-kino.git
cd rime-kino
./scripts/deploy.sh   # Windows: .\scripts\deploy.ps1
```

## 通道

| 键 | 作用 |
| :--- | :--- |
| 拼音 | 严格热路径，缓冲区 256 字符 |
| `\` | 数学 / 命令（LaTeX · Typst · Lean · MMA） |
| `;` | 拉丁重音（`;n` → ñ） |
| `~` | 日文假名与 Viterbi 汉字 |

## 文档

- [交互契约](kino.md)
- [文档治理](README.md)
- [码表与索引](drafts/README.md)
- [日文 Viterbi](jp-viterbi.md)
- [数学符号管线](math-symbols.md)
