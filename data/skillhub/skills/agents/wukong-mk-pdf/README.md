# Markdown → PDF（轻量版）

这个工具用于把 Markdown（`.md`）转换成高质量 PDF（`.pdf`）。

实现方式：使用 `markdown-pdf`（基于 PyMuPDF）直接渲染 Markdown 为 PDF，无需浏览器引擎。内置 GitHub 风格 CSS，支持表格、代码块、目录（TOC）等常见特性。

## 特性

- **零系统依赖**：纯 `pip install`，不需要 Chromium、cairo 等系统级组件
- **毫秒级转换**：比 Playwright 方案快 100 倍以上
- **中文友好**：PyMuPDF 内置字体支持
- **批量转换**：递归扫描当前目录下所有 `.md`
- **单文件转换**：指定输入/输出路径
- **无临时文件**：不生成中间 HTML，无需清理

## 环境要求

- Python 3.8+
- macOS / Linux / Windows

## 安装

安装 Python 依赖（仅一个包）：

```bash
pip install -r requirements.txt
```

（可选）国内源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> **无需安装浏览器内核**，告别 `playwright install chromium`。

## 使用

批量转换（默认：在当前目录递归转换所有 `.md`）：

```bash
python3 convert_md_to_pdf.py
```

单文件转换：

```bash
python3 convert_md_to_pdf.py -i input.md -o output.pdf
```

查看帮助：

```bash
python3 convert_md_to_pdf.py -h
```

## 与旧版（Playwright）的对比

| 对比项       | 旧版 Playwright        | 新版 markdown-pdf      |
| ------------ | ---------------------- | ---------------------- |
| 系统依赖     | 需要 Chromium (~200MB) | 无                     |
| 安装步骤     | pip + playwright install | pip install 一步到位   |
| 转换速度     | 秒级                   | 毫秒级                 |
| 中文支持     | 依赖系统字体           | 内置支持               |
| 临时文件     | 生成 *.temp.html       | 无                     |
| 沙箱兼容性   | 受限（需 headless 浏览器） | 完全兼容           |
| 渲染质量     | 浏览器级（最高）       | 高质量（满足绝大多数场景） |

## 说明与限制

- **图片**：支持绝对路径和网络图片。相对路径图片的解析取决于工作目录。
- **样式**：内置 GitHub Markdown 风格 CSS，可在脚本中自定义 `CSS` 变量。
- **PDF 规格**：A4 纸张，自动生成 TOC（2 级标题深度）。
