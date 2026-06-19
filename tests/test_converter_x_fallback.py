import requests

import pytest

from app.converter import (
    URLFetchBlocked,
    _extract_x_public_article_markdown,
    _is_x_public_article_url,
    fetch_url_as_markdown,
)


def test_detects_public_x_status_and_article_urls():
    assert _is_x_public_article_url("https://x.com/heynavtoor/status/2067194761446920264?s=46")
    assert _is_x_public_article_url("https://twitter.com/heynavtoor/status/2067194761446920264")
    assert _is_x_public_article_url("https://x.com/i/article/2067171614580441089")
    assert not _is_x_public_article_url("https://x.com/home")


def test_extract_x_article_preview_and_cover_from_ssr_payload():
    html = '''
    <html><head><meta property="og:title" content="Fallback title"></head><body>
    <script>
    __typename:"ArticleEntity",rest_id:"2067171614580441089",
    title:"The Stanford STORM Method: How to Make Claude Research Like a PhD in Minutes",
    preview_text:"Most people use Claude like a search box.\\nSave this :)",
    cover_media_results:{"__ref":"media"}
    original_img_url:"https://pbs.twimg.com/media/HLAlQnCbgAADUcf.jpg"
    </script>
    </body></html>
    '''

    result = _extract_x_public_article_markdown(
        html,
        "https://x.com/heynavtoor/status/2067194761446920264?s=46",
    )

    assert result is not None
    markdown, title = result
    assert title == "The Stanford STORM Method: How to Make Claude Research Like a PhD in Minutes"
    assert "# The Stanford STORM Method" in markdown
    assert "![The Stanford STORM Method" in markdown
    assert "https://pbs.twimg.com/media/HLAlQnCbgAADUcf.jpg" in markdown
    assert "Most people use Claude like a search box." in markdown
    assert "原文链接：https://x.com/heynavtoor/status/2067194761446920264?s=46" in markdown


def test_x_fetch_timeout_returns_actionable_blocked_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.ReadTimeout("x.com timed out")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(URLFetchBlocked) as excinfo:
        fetch_url_as_markdown("https://x.com/heynavtoor/status/2067194761446920264?s=46")

    assert "服务器访问 X/Twitter 超时" in str(excinfo.value)
    assert "粘贴内容" in excinfo.value.suggestion
