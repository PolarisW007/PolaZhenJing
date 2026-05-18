#!/usr/bin/env python3
"""
Markdown → PDF 转换工具（基于 markdown-pdf / PyMuPDF）

轻量替代 Playwright 方案：
- 零系统级依赖，纯 pip install 即可
- 转换速度极快（毫秒级）
- 内置中文字体支持
- 支持单文件 & 批量转换
"""

import os
import sys
import argparse
import time
from markdown_pdf import MarkdownPdf, Section


# ── GitHub 风格 CSS（注入到 markdown-pdf 渲染引擎）──────────────────────
CSS = """\
body {
    box-sizing: border-box;
    min-width: 200px;
    max-width: 980px;
    margin: 0 auto;
    padding: 45px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial,
                 sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    font-size: 16px;
    line-height: 1.5;
    word-wrap: break-word;
    color: #24292e;
}
h1, h2, h3, h4, h5, h6 {
    margin-top: 24px; margin-bottom: 16px;
    font-weight: 600; line-height: 1.25;
}
h1 { font-size: 2em;    border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
h2 { font-size: 1.5em;  border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
h3 { font-size: 1.25em; }
h4 { font-size: 1em; }
h5 { font-size: .875em; }
h6 { font-size: .85em; color: #6a737d; }
p  { margin-top: 0; margin-bottom: 16px; }
blockquote {
    padding: 0 1em; color: #6a737d;
    border-left: .25em solid #dfe2e5;
    margin: 0 0 16px 0;
}
ul, ol { padding-left: 2em; margin-top: 0; margin-bottom: 16px; }
code {
    padding: .2em .4em; margin: 0; font-size: 85%;
    background-color: #f6f8fa; border-radius: 6px;
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
}
pre {
    padding: 16px; overflow: auto; font-size: 85%;
    line-height: 1.45; background-color: #f6f8fa;
    border-radius: 6px; margin-bottom: 16px;
}
pre code {
    display: inline; padding: 0; margin: 0;
    overflow: visible; line-height: inherit;
    word-wrap: normal; background-color: transparent; border: 0;
}
table {
    display: table; width: 100%; overflow: auto;
    margin-top: 0; margin-bottom: 16px;
    border-spacing: 0; border-collapse: collapse;
}
table tr { background-color: #fff; border-top: 1px solid #c6cbd1; }
table tr:nth-child(2n) { background-color: #f6f8fa; }
table th, table td { padding: 6px 13px; border: 1px solid #dfe2e5; }
table th { font-weight: 600; }
img { max-width: 100%; box-sizing: content-box; background-color: #fff; }
hr {
    height: .25em; padding: 0; margin: 24px 0;
    background-color: #e1e4e8; border: 0;
}
"""


def convert_md_to_pdf(input_file: str, output_file: str) -> bool:
    """将单个 Markdown 文件转换为 PDF。"""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            md_text = f.read()

        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(md_text, toc=False), user_css=CSS)
        pdf.save(output_file)

        size_kb = os.path.getsize(output_file) / 1024
        print(
            f"转换成功: {input_file} → {output_file}  ({size_kb:.1f} KB)\n"
            f"Successfully converted: {input_file} → {output_file}"
        )
        return True

    except Exception as e:
        print(
            f"转换失败 {input_file}: {e}\n"
            f"Failed to convert {input_file}: {e}",
            file=sys.stderr,
        )
        return False


def main():
    parser = argparse.ArgumentParser(
        description=(
            "使用 markdown-pdf 将 Markdown 文件转换为 PDF。\n"
            "Convert Markdown files to PDF using markdown-pdf (PyMuPDF)."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input",
        help="输入 Markdown 文件路径\nInput Markdown file path",
    )
    parser.add_argument(
        "-o", "--output",
        help="输出 PDF 文件路径\nOutput PDF file path",
    )

    args = parser.parse_args()

    # 参数校验
    if args.input and not args.output:
        parser.error("指定 -i 时必须同时指定 -o。\n-i requires -o to be specified.")

    start = time.time()

    if args.input:
        # ── 单文件模式 ──
        if not os.path.exists(args.input):
            print(
                f"错误：未找到输入文件: {args.input}\n"
                f"Error: Input file not found: {args.input}",
                file=sys.stderr,
            )
            sys.exit(1)

        # 确保输出目录存在
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        success = convert_md_to_pdf(args.input, args.output)
        if not success:
            sys.exit(1)
    else:
        # ── 批量模式 ──
        root_dir = os.getcwd()
        count_ok, count_fail = 0, 0
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.lower().endswith(".md"):
                    input_path = os.path.join(dirpath, filename)
                    output_path = os.path.splitext(input_path)[0] + ".pdf"
                    if convert_md_to_pdf(input_path, output_path):
                        count_ok += 1
                    else:
                        count_fail += 1

        print(f"\n批量转换完成: 成功 {count_ok}, 失败 {count_fail}")

    elapsed = time.time() - start
    print(f"总耗时: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
