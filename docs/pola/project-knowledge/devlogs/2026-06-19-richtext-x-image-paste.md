# 2026-06-19 富文本粘贴 X 图片恢复

## 需求

用户在 `/PolaZhenjing/admin/upload` 粘贴 X/Twitter 内容时，正文可以进入富文本编辑器，但原本能显示的图片不再显示。需要排查并恢复粘贴图片能力。

## 原因

URL 抓取入口仍然按既有策略拒绝 X/Twitter 直接抓取，因为该站点需要登录且动态渲染。实际问题出在富文本粘贴链路：浏览器从 X 复制出的图片常位于 `picture > source srcset` 或 CSS `background-image`，而当前前端和后端只识别普通 `img/src`，导致粘贴时图片被当作无效图片删除或保存时丢失。

## 改动

- `app/templates/upload.html`
  - 富文本粘贴预处理新增 `picture/source srcset` 识别。
  - 新增 CSS 背景图 URL 提升为普通 `img` 的兜底。
  - 扩展 `data-image-url`、`data-media-url`、`data-full-url` 等常见剪贴板属性。
- `app/templates/article_edit.html`
  - 与上传页保持一致，避免编辑已有文章时再次丢图。
- `app/uploader.py`
  - 后端富文本本地化新增 `picture/source srcset` 兜底。
  - 将内容型 CSS 背景图提升为 `img` 后进入现有 richtext 图片本地化流程。
- `app/article_content.py`
  - 保留 `source/srcset` 和 `picture` 内 `img` 的安全属性，避免转换阶段误删图片。
- `tests/test_article_edit_rich_editor.py`
  - 新增 X 复制格式回归：`picture/source srcset` 和 `background-image` 都能被下载成本地 richtext 图片。
- `app/converter.py`
  - 对公开 X/Twitter status/article 链接增加 SSR 降级提取。
  - 能从 X 首屏 HTML 中提取文章标题、预览文本和 `pbs.twimg.com` 封面图，避免 URL 抓取入口直接失败。
  - 当云服务器访问 X 超时或被网络拦截时，转成带操作建议的 `URLFetchBlocked`，提示用户改用本机浏览器复制后粘贴。
- `tests/test_converter_x_fallback.py`
  - 新增 X status/article URL 识别和 SSR 文章卡片提取测试。
  - 新增 X 网络超时错误映射测试。

## 验证

- `.venv/bin/python -m pytest tests/test_article_edit_rich_editor.py tests/test_article_content.py -q`
  - 17 passed
- `.venv/bin/python -m pytest tests/test_converter_x_fallback.py tests/test_article_edit_rich_editor.py tests/test_article_content.py -q`
  - 19 passed
- `.venv/bin/python -m py_compile app/converter.py app/uploader.py app/article_content.py`
  - passed
- 真实链接验证：
  - `https://x.com/heynavtoor/status/2067194761446920264?s=46`
  - `fetch_url_as_markdown()` 输出标题 `The Stanford STORM Method: How to Make Claude Research Like a PhD in Minutes`
  - 输出 Markdown 包含封面图 `https://pbs.twimg.com/media/HLAlQnCbgAADUcf.jpg`
- 线上服务器网络验证：
  - 云服务器访问 `x.com`、`cdn.syndication.twimg.com` 和 `pbs.twimg.com` 均出现超时；因此生产 URL 抓取对 X 仍依赖云服务器出口网络可达性。
  - 已增加超时兜底提示，避免服务端异常暴露给用户。

## 风险与边界

- 本次只对公开 X/Twitter status/article 链接做 SSR 降级提取；其它 X 页面仍会提示改用粘贴内容或外部抓取工具。
- X SSR 通常只稳定暴露文章标题、预览和封面图，不保证能抓到完整长文正文。完整正文仍推荐打开页面后复制正文粘贴。
- 当前云服务器出口到 X/PBS 不稳定时，URL 抓取仍可能无法成功；本机浏览器粘贴是更稳定的工作流。
- CSS 背景图提升只接受明显图片 URL、`twimg.com` 或带 `format=` 的媒体 URL，减少误把装饰背景保存进文章的风险。
