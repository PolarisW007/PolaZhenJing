---
name: wukong-mk-pdf
description: "Markdown 转 PDF 工具：将 Markdown 文件通过 markdown-pdf（PyMuPDF）渲染为高质量 PDF。零系统依赖，纯 pip 安装，毫秒级转换。支持单文件和批量转换。Run: /path/to/python .../convert_md_to_pdf.py -i input.md -o output.pdf"
metadata:
  platforms: "claude-code,openclaw,cursor,wukong"
  skill-root-env: "MK_PDF_SKILL_ROOT"
  display-name: "Markdown 转 PDF"
  author: 王畅
  created: "2026-04-08"
  updated: "2026-04-14"
---
# Markdown → PDF —— 轻量高速渲染

将 Markdown（`.md`）文件转换为高质量 PDF（`.pdf`）。使用 `markdown-pdf`（基于 PyMuPDF）直接渲染，无需浏览器引擎。内置 GitHub 风格 CSS，支持表格、代码块、目录（TOC）等常见特性。

## 何时使用

- 用户需要将 Markdown 文件转换为 PDF 格式。
- 用户需要批量转换目录下所有 `.md` 文件为 PDF。
- 用户需要快速生成高质量 PDF 文档（毫秒级完成）。

## 依赖

- Python 3.8+
- `pip install -r <技能根>/requirements.txt`（仅需 `markdown-pdf`，自动包含 PyMuPDF）
- **无需浏览器内核**，无需系统级 C 库

## 执行协议

### 单文件转换

将指定的 Markdown 文件转换为 PDF：

```bash
"/path/to/python" "/path/to/wukong-mk-pdf/convert_md_to_pdf.py" \
  -i "input.md" \
  -o "output.pdf"
```

> `-i` 和 `-o` 必须同时指定。

### 批量转换

递归扫描当前目录下所有 `.md` 文件并转换为同名 `.pdf`：

```bash
cd /path/to/target/directory
"/path/to/python" "/path/to/wukong-mk-pdf/convert_md_to_pdf.py"
```

> 不传 `-i`/`-o` 参数时自动进入批量模式，以当前工作目录为根递归扫描。

## CLI 参数

| 参数              | 说明                   | 默认值                             |
| ----------------- | ---------------------- | ---------------------------------- |
| `-i` / `--input`  | 输入 Markdown 文件路径 | 无（不指定则批量模式）             |
| `-o` / `--output` | 输出 PDF 文件路径      | 无（批量模式下自动生成同名`.pdf`） |

## PDF 输出规格

| 配置项 | 值                   |
| ------ | -------------------- |
| 纸张   | A4                   |
| 样式   | GitHub Markdown 风格 |
| TOC    | 自动生成（2 级标题） |
| 中文   | 内置支持             |

## 注意事项

- **零系统依赖**：不需要 Chromium、cairo、pango 等系统级二进制或 C 库，`pip install` 即可运行。
- **速度极快**：毫秒级转换，适合批量处理。
- **无临时文件**：不生成中间 HTML 文件，无需清理。
- **中文友好**：PyMuPDF 内置字体支持，中文内容无需额外配置。

## 目录结构

```
wukong-mk-pdf/
├── SKILL.md              # 本文件（技能元数据）
├── README.md             # 项目说明
├── convert_md_to_pdf.py  # 核心转换脚本
└── requirements.txt      # Python 依赖（markdown-pdf）
```
