"""Article social publishing center.

First release:
- WeChat Official Account: official API draft sync.
- Xiaohongshu / Toutiao: manual publishing packages with URL backfill.
"""
from __future__ import annotations

import functools
import json
import mimetypes
import os
import re
import sqlite3
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import markdown as md_lib
import requests
from bs4 import BeautifulSoup
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)

from .auth import login_required
from . import jobs

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "wiki.db"

social_publish_bp = Blueprint("social_publish", __name__, url_prefix="/admin/social")

WECHAT_TOKEN_CACHE = {
    "access_token": "",
    "expires_at": 0,
}

X_POST_CHAR_LIMIT = 280

PLATFORMS = {
    "wechat_mp": {
        "name": "微信公众号",
        "mode": "official_api",
        "hint": "官方 API，同步到草稿箱后再确认发布。",
    },
    "x": {
        "name": "X",
        "mode": "official_api",
        "hint": "官方 API，发布短帖并记录 X post ID。",
        "console_url": "https://developer.x.com/",
    },
    "xiaohongshu": {
        "name": "小红书",
        "mode": "manual_package",
        "hint": "第一阶段生成发布包，复制到创作者后台发布。",
        "console_url": "https://creator.xiaohongshu.com/",
    },
    "toutiao": {
        "name": "今日头条",
        "mode": "manual_package",
        "hint": "第一阶段生成发布包，复制到头条号后台发布。",
        "console_url": "https://mp.toutiao.com/",
    },
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS social_publications (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    filename     TEXT NOT NULL,
    platform     TEXT NOT NULL,
    status       TEXT NOT NULL,
    mode         TEXT,
    external_id  TEXT,
    external_url TEXT,
    payload_json TEXT,
    error        TEXT,
    created_by   INTEGER,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_publication_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    publication_id INTEGER NOT NULL,
    event_type     TEXT NOT NULL,
    message        TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(publication_id) REFERENCES social_publications(id)
);
"""


def init_schema() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _is_admin() -> bool:
    return session.get("role") == "admin"


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.path))
        if not _is_admin():
            flash("只有管理员可以使用发布中心。", "error")
            return redirect(url_for("uploader.articles"))
        return view(**kwargs)

    return wrapped_view


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    try:
        data["payload"] = json.loads(data.get("payload_json") or "{}")
    except Exception:
        data["payload"] = {}
    return data


def _create_publication(filename: str, platform: str, status: str,
                        mode: str = "", payload: dict | None = None,
                        external_id: str = "", external_url: str = "",
                        error: str = "") -> int:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO social_publications
            (filename, platform, status, mode, external_id, external_url, payload_json, error, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                platform,
                status,
                mode,
                external_id,
                external_url,
                json.dumps(payload or {}, ensure_ascii=False),
                error,
                session.get("user_id"),
            ),
        )
        pub_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO social_publication_events (publication_id, event_type, message) VALUES (?, ?, ?)",
            (pub_id, status, error or "created"),
        )
        conn.commit()
        return pub_id
    finally:
        conn.close()


def _update_publication(pub_id: int, *, status: str, payload: dict | None = None,
                        external_id: str = "", external_url: str = "",
                        error: str = "", event_message: str = "") -> None:
    fields = ["status=?", "updated_at=CURRENT_TIMESTAMP"]
    values: list[Any] = [status]
    if payload is not None:
        fields.append("payload_json=?")
        values.append(json.dumps(payload, ensure_ascii=False))
    if external_id:
        fields.append("external_id=?")
        values.append(external_id)
    if external_url:
        fields.append("external_url=?")
        values.append(external_url)
    if error:
        fields.append("error=?")
        values.append(error)
    values.append(pub_id)

    conn = _connect()
    try:
        conn.execute(f"UPDATE social_publications SET {', '.join(fields)} WHERE id=?", values)
        conn.execute(
            "INSERT INTO social_publication_events (publication_id, event_type, message) VALUES (?, ?, ?)",
            (pub_id, status, event_message or error or status),
        )
        conn.commit()
    finally:
        conn.close()


def _latest_publications(filename: str | None = None) -> dict[str, dict]:
    conn = _connect()
    try:
        if filename:
            rows = conn.execute(
                """
                SELECT * FROM social_publications
                WHERE filename = ?
                ORDER BY datetime(updated_at) DESC, id DESC
                """,
                (filename,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM social_publications ORDER BY datetime(updated_at) DESC, id DESC LIMIT 100"
            ).fetchall()
    finally:
        conn.close()
    latest: dict[str, dict] = {}
    for row in rows:
        item = _row_to_dict(row)
        if item and item["platform"] not in latest:
            latest[item["platform"]] = item
    return latest


def _get_publication(publication_id: int) -> dict[str, Any] | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM social_publications WHERE id = ?",
            (publication_id,),
        ).fetchone()
    finally:
        conn.close()
    return _row_to_dict(row)


def _publication_events(publication_ids: list[int]) -> list[dict]:
    if not publication_ids:
        return []
    placeholders = ",".join("?" for _ in publication_ids)
    conn = _connect()
    try:
        rows = conn.execute(
            f"""
            SELECT e.*, p.platform
            FROM social_publication_events e
            JOIN social_publications p ON p.id = e.publication_id
            WHERE e.publication_id IN ({placeholders})
            ORDER BY datetime(e.created_at) DESC, e.id DESC
            LIMIT 40
            """,
            publication_ids,
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def _latest_successful_publication(filename: str, platform: str, statuses: set[str]) -> dict[str, Any] | None:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT * FROM social_publications
            WHERE filename = ? AND platform = ? AND external_id IS NOT NULL
            ORDER BY datetime(updated_at) DESC, id DESC
            """,
            (filename, platform),
        ).fetchall()
    finally:
        conn.close()
    for row in rows:
        item = _row_to_dict(row)
        if item and item.get("status") in statuses:
            return item
    return None


def _post_context(filename: str) -> dict[str, Any]:
    from .uploader import (_absolute_asset_url, _article_admin_filename,
                           _build_pages_url, _parse_post, _safe_post_path)

    fpath = _safe_post_path(filename)
    if not fpath:
        raise FileNotFoundError("文章不存在。")
    actual_filename = os.path.basename(fpath)
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    meta, _, body = _parse_post(raw)
    title = meta.get("title") or actual_filename.replace(".md", "")
    description = meta.get("description") or meta.get("summary") or _plain_text(body)[:160]
    cover = meta.get("image") or _first_markdown_image(body)
    return {
        "filename": actual_filename,
        "admin_filename": _article_admin_filename(actual_filename),
        "path": fpath,
        "meta": meta,
        "title": title,
        "description": description,
        "summary": meta.get("summary") or description,
        "body": body,
        "plain_body": _plain_text(body),
        "tags": _parse_tags(meta.get("tags", "")),
        "cover": cover,
        "cover_url": _absolute_asset_url(cover) if cover else "",
        "pages_url": _build_pages_url(actual_filename),
        "public_url": url_for(
            "public_articles.public_article_view",
            filename=_article_admin_filename(actual_filename),
            _external=True,
        ),
    }


def _parse_tags(raw: str) -> list[str]:
    value = (raw or "").strip()
    if not value or value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
        return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
    return [item.strip() for item in value.split(",") if item.strip()]


def _plain_text(markdown_text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", markdown_text or "")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[#>*_`~|-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _wechat_clamp_text(value: str, max_bytes: int) -> str:
    """Clamp text by UTF-8 bytes for strict WeChat draft fields."""
    value = re.sub(r"\s+", " ", value or "").strip()
    out = []
    used = 0
    for ch in value:
        size = len(ch.encode("utf-8"))
        if used + size > max_bytes:
            break
        out.append(ch)
        used += size
    return "".join(out).rstrip()


def _first_markdown_image(markdown_text: str) -> str:
    match = re.search(r"!\[[^\]]*\]\(([^)]+)\)", markdown_text or "")
    return match.group(1).strip() if match else ""


def build_manual_package(ctx: dict[str, Any], platform: str) -> dict[str, Any]:
    title = ctx["title"]
    plain = ctx["plain_body"]
    summary = (ctx.get("summary") or ctx.get("description") or plain[:160]).strip()
    tags = ctx.get("tags") or []
    if platform == "xiaohongshu":
        short_title = title[:20]
        body = "\n\n".join(
            part for part in [
                summary[:120],
                plain[:900],
                " ".join(f"#{tag}" for tag in tags[:8]),
            ] if part
        )
        checklist = [
            "选择图文笔记，上传封面和正文配图。",
            "标题建议控制在 20 字以内。",
            "正文先放结论和个人体验，再放链接或来源说明。",
            "发布后把笔记 URL 回填到本页面。",
        ]
    else:
        short_title = title[:30]
        body = ctx["body"]
        checklist = [
            "进入头条号后台，新建图文。",
            "粘贴 Markdown/正文后检查图片是否成功上传。",
            "选择封面图，确认原创/引用声明。",
            "发布后把文章 URL 回填到本页面。",
        ]
    return {
        "platform": platform,
        "platform_name": PLATFORMS[platform]["name"],
        "title": short_title,
        "original_title": title,
        "description": summary[:180],
        "body": body,
        "tags": tags,
        "cover": ctx.get("cover_url") or ctx.get("cover") or "",
        "source_url": ctx.get("public_url") or ctx.get("pages_url") or "",
        "console_url": PLATFORMS[platform].get("console_url", ""),
        "checklist": checklist,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def _asset_local_path(src: str) -> Path | None:
    value = (src or "").strip().strip("\"'")
    if not value or value.startswith(("http://", "https://")):
        return None
    value = value.replace("{{ site.baseurl }}", "").strip()
    for prefix in ("/PolaZhenjing/assets/", "/PolaZhenJing/assets/", "/assets/", "assets/"):
        if value.startswith(prefix):
            rel = value[len(prefix):]
            path = PROJECT_ROOT / "assets" / rel
            return path if path.is_file() else None
    return None


def _public_source_url(ctx: dict[str, Any]) -> str:
    for key in ("public_url", "pages_url"):
        value = (ctx.get(key) or "").strip()
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            continue
        return value
    return ""


def _wechat_config_status() -> dict[str, Any]:
    app_id = os.getenv("WECHAT_MP_APP_ID", "").strip()
    app_secret = os.getenv("WECHAT_MP_APP_SECRET", "").strip()
    missing = []
    if not app_id:
        missing.append("WECHAT_MP_APP_ID")
    if not app_secret:
        missing.append("WECHAT_MP_APP_SECRET")
    return {
        "configured": not missing,
        "missing": missing,
        "app_id_tail": app_id[-6:] if app_id else "",
    }


def _wechat_access_token() -> str:
    config = _wechat_config_status()
    if not config["configured"]:
        raise RuntimeError("微信公众号未配置 WECHAT_MP_APP_ID / WECHAT_MP_APP_SECRET。")
    now = int(time.time())
    if WECHAT_TOKEN_CACHE["access_token"] and WECHAT_TOKEN_CACHE["expires_at"] > now + 60:
        return WECHAT_TOKEN_CACHE["access_token"]
    params = {
        "grant_type": "client_credential",
        "appid": os.getenv("WECHAT_MP_APP_ID", "").strip(),
        "secret": os.getenv("WECHAT_MP_APP_SECRET", "").strip(),
    }
    resp = requests.get("https://api.weixin.qq.com/cgi-bin/token", params=params, timeout=10)
    data = resp.json()
    if data.get("errcode"):
        raise RuntimeError(data.get("errmsg") or f"WeChat token error {data.get('errcode')}")
    token = data.get("access_token", "")
    if not token:
        raise RuntimeError("微信接口未返回 access_token。")
    WECHAT_TOKEN_CACHE["access_token"] = token
    WECHAT_TOKEN_CACHE["expires_at"] = now + int(data.get("expires_in", 7200))
    return token


def _wechat_post_json(path: str, payload: dict) -> dict:
    token = _wechat_access_token()
    resp = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/{path}",
        params={"access_token": token},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=20,
    )
    data = resp.json()
    if data.get("errcode"):
        raise RuntimeError(data.get("errmsg") or f"WeChat API error {data.get('errcode')}")
    return data


def summarize_wechat_publish_result(data: dict[str, Any]) -> dict[str, str]:
    """Normalize WeChat freepublish/get responses without assuming one schema."""
    status_value = str(data.get("publish_status", "")).strip()
    if status_value in {"0", "success", "SUCCESS"}:
        status = "published"
    elif status_value:
        status = f"publish_status_{status_value}"
    else:
        status = "publish_checked"

    article_url = ""
    details = data.get("article_detail") or data.get("article_detail_list") or {}
    items = []
    if isinstance(details, dict):
        items = details.get("item") or details.get("items") or []
    elif isinstance(details, list):
        items = details
    if isinstance(items, dict):
        items = [items]
    for item in items:
        if isinstance(item, dict) and item.get("article_url"):
            article_url = item["article_url"]
            break
        if isinstance(item, dict) and item.get("content_url"):
            article_url = item["content_url"]
            break
    return {"status": status, "article_url": article_url}


def _wechat_content_source_url(ctx: dict[str, Any]) -> str:
    return _public_source_url(ctx)


def _wechat_uploadable_image(path: Path) -> tuple[Path, bool]:
    """Return a WeChat-compatible image path, converting raster formats if needed."""
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif"}:
        return path, False
    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError(f"微信不支持该图片格式且 Pillow 不可用：{path.name}") from exc
    try:
        with Image.open(path) as image:
            image.load()
            converted = image.convert("RGB")
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp.close()
            converted.save(tmp.name, format="PNG")
            return Path(tmp.name), True
    except Exception as exc:
        raise RuntimeError(f"微信不支持该图片格式且无法转换：{path.name}") from exc


def _wechat_upload_image(path: Path, *, permanent: bool) -> dict:
    token = _wechat_access_token()
    if permanent:
        url = "https://api.weixin.qq.com/cgi-bin/material/add_material"
        params = {"access_token": token, "type": "image"}
    else:
        url = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
        params = {"access_token": token}
    upload_path, temporary = _wechat_uploadable_image(path)
    try:
        with upload_path.open("rb") as f:
            resp = requests.post(url, params=params, files={"media": f}, timeout=60)
    finally:
        if temporary:
            try:
                upload_path.unlink(missing_ok=True)
            except Exception:
                pass
    data = resp.json()
    if data.get("errcode"):
        raise RuntimeError(data.get("errmsg") or f"WeChat upload error {data.get('errcode')}")
    return data


def build_wechat_html(ctx: dict[str, Any], image_replacements: dict[str, str] | None = None) -> str:
    body = ctx["body"]
    for src, replacement in (image_replacements or {}).items():
        body = body.replace(src, replacement)
    body = body.replace("{{ site.baseurl }}", "")
    body_html = md_lib.markdown(body, extensions=["extra", "tables"])
    soup = BeautifulSoup(body_html, "html.parser")
    for tag in soup(["script", "style", "iframe"]):
        tag.decompose()
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src in (image_replacements or {}):
            img["src"] = image_replacements[src]
        img.attrs = {k: v for k, v in img.attrs.items() if k in {"src", "alt", "title"}}
    return str(soup)


def _create_wechat_draft(ctx: dict[str, Any]) -> dict[str, Any]:
    cover_path = _asset_local_path(ctx.get("cover") or "")
    if not cover_path:
        cover_path = PROJECT_ROOT / "assets" / "images" / "test_cover.jpg"
    if not cover_path.is_file():
        raise RuntimeError("未找到可上传到微信的封面图。")
    thumb = _wechat_upload_image(cover_path, permanent=True)
    thumb_media_id = thumb.get("media_id")
    if not thumb_media_id:
        raise RuntimeError("微信封面素材上传成功但未返回 media_id。")

    replacements: dict[str, str] = {}
    for src in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", ctx["body"]):
        local_path = _asset_local_path(src)
        if not local_path:
            continue
        try:
            data = _wechat_upload_image(local_path, permanent=False)
            if data.get("url"):
                replacements[src] = data["url"]
        except RuntimeError:
            continue

    content_html = build_wechat_html(ctx, replacements)
    digest = _wechat_clamp_text(
        ctx.get("description") or ctx.get("summary") or ctx["plain_body"],
        54,
    )
    payload = {
        "articles": [
            {
                "title": _wechat_clamp_text(ctx["title"], 64),
                "digest": digest,
                "content": content_html,
                "content_source_url": _wechat_content_source_url(ctx),
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            }
        ]
    }
    data = _wechat_post_json("draft/add", payload)
    media_id = data.get("media_id")
    if not media_id:
        raise RuntimeError("微信草稿接口未返回 media_id。")
    return {
        "media_id": media_id,
        "uploaded_images": len(replacements),
        "thumb_media_id": thumb_media_id,
    }


def _run_wechat_draft_job(job_id: str, publication_id: int, ctx: dict[str, Any]) -> None:
    jobs.update_job(job_id, status=jobs.RUNNING, stage="解析文章内容…", progress=10)
    jobs.update_job(job_id, stage="上传封面和正文图片到微信…", progress=35)
    result = _create_wechat_draft(ctx)
    jobs.update_job(job_id, stage="写入发布记录…", progress=80)
    _update_publication(
        publication_id,
        status="draft_created",
        payload={
            "wechat": {
                "media_id": result["media_id"],
                "uploaded_images": result["uploaded_images"],
            },
            "title": ctx["title"],
            "source_url": ctx.get("public_url") or ctx.get("pages_url") or "",
        },
        external_id=result["media_id"],
        event_message="微信公众号草稿已创建。",
    )
    jobs.append_message(job_id, "success", "微信公众号草稿已创建，请到公众号后台检查后发布。")
    jobs.update_job(job_id, status=jobs.DONE, stage="已完成", progress=100, result_filename=ctx["admin_filename"])


def _x_config_status() -> dict[str, Any]:
    token = os.getenv("X_USER_ACCESS_TOKEN", "").strip()
    return {
        "configured": bool(token),
        "missing": [] if token else ["X_USER_ACCESS_TOKEN"],
        "token_tail": token[-6:] if token else "",
    }


def build_x_post_text(ctx: dict[str, Any]) -> str:
    title = re.sub(r"\s+", " ", ctx.get("title") or "").strip()
    summary = re.sub(r"\s+", " ", ctx.get("description") or ctx.get("summary") or "").strip()
    source_url = _public_source_url(ctx)
    parts = [part for part in [title, summary, source_url] if part]
    text = "\n\n".join(parts)
    if len(text) <= X_POST_CHAR_LIMIT:
        return text

    fixed_parts = [part for part in [title, source_url] if part]
    fixed_text = "\n\n".join(fixed_parts)
    separator_size = 4 if fixed_text and summary else 0
    budget = X_POST_CHAR_LIMIT - len(fixed_text) - separator_size
    if budget > 1 and summary:
        summary = summary[: max(0, budget - 1)].rstrip() + "…"
        return "\n\n".join(part for part in [title, summary, source_url] if part)[:X_POST_CHAR_LIMIT]
    return fixed_text[:X_POST_CHAR_LIMIT]


def _x_bearer_headers() -> dict[str, str]:
    token = os.getenv("X_USER_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("X 未配置 X_USER_ACCESS_TOKEN。")
    return {"Authorization": f"Bearer {token}"}


def _x_post_json(path: str, payload: dict) -> dict:
    resp = requests.post(
        f"https://api.x.com/2/{path.lstrip('/')}",
        headers={**_x_bearer_headers(), "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=20,
    )
    try:
        data = resp.json()
    except Exception:
        data = {}
    if resp.status_code >= 400 or data.get("errors"):
        message = data.get("detail") or data.get("title") or resp.text[:200] or f"X API HTTP {resp.status_code}"
        raise RuntimeError(message)
    return data


def _x_upload_media(path: Path) -> str:
    upload_path, temporary = _wechat_uploadable_image(path)
    media_type = mimetypes.guess_type(str(upload_path))[0] or "image/png"
    try:
        with upload_path.open("rb") as f:
            resp = requests.post(
                "https://api.x.com/2/media/upload",
                headers=_x_bearer_headers(),
                data={"media_category": "tweet_image", "media_type": media_type},
                files={"media": f},
                timeout=60,
            )
    finally:
        if temporary:
            try:
                upload_path.unlink(missing_ok=True)
            except Exception:
                pass
    try:
        data = resp.json()
    except Exception:
        data = {}
    if resp.status_code >= 400 or data.get("errors"):
        message = data.get("detail") or data.get("title") or resp.text[:200] or f"X media upload HTTP {resp.status_code}"
        raise RuntimeError(message)
    media_id = str((data.get("data") or {}).get("id") or data.get("media_id") or "")
    if not media_id:
        raise RuntimeError("X 媒体上传成功但未返回 media id。")
    return media_id


def _create_x_post(ctx: dict[str, Any]) -> dict[str, Any]:
    text = build_x_post_text(ctx)
    if not text:
        raise RuntimeError("没有可发布到 X 的文本内容。")
    payload: dict[str, Any] = {"text": text}
    uploaded_media_id = ""
    cover_path = _asset_local_path(ctx.get("cover") or "")
    if cover_path:
        uploaded_media_id = _x_upload_media(cover_path)
        payload["media"] = {"media_ids": [uploaded_media_id]}
    data = _x_post_json("tweets", payload)
    post = data.get("data") or {}
    post_id = str(post.get("id") or "")
    if not post_id:
        raise RuntimeError("X 发帖接口未返回 post id。")
    return {
        "post_id": post_id,
        "text": text,
        "media_id": uploaded_media_id,
        "raw": data,
        "url": f"https://x.com/i/web/status/{post_id}",
    }


def _run_x_post_job(job_id: str, publication_id: int, ctx: dict[str, Any]) -> None:
    try:
        jobs.update_job(job_id, status=jobs.RUNNING, stage="检查 X 重复发布记录…", progress=10)
        existing = _latest_successful_publication(ctx["filename"], "x", {"posted"})
        if existing:
            _update_publication(
                publication_id,
                status="skipped_duplicate",
                payload={"duplicate_of": existing["id"], "external_id": existing.get("external_id")},
                external_id=existing.get("external_id") or "",
                external_url=existing.get("external_url") or "",
                event_message="X 已存在成功发布记录，跳过重复发送。",
            )
            jobs.append_message(job_id, "info", "X 已存在成功发布记录，已跳过重复发送。")
            jobs.update_job(job_id, status=jobs.DONE, stage="已跳过", progress=100, result_filename=ctx["admin_filename"])
            return

        jobs.update_job(job_id, stage="生成 X 文案并上传封面…", progress=35)
        result = _create_x_post(ctx)
        jobs.update_job(job_id, stage="写入 X 发布记录…", progress=80)
        _update_publication(
            publication_id,
            status="posted",
            payload={
                "x": {
                    "post_id": result["post_id"],
                    "media_id": result["media_id"],
                    "text": result["text"],
                },
                "title": ctx["title"],
                "source_url": _public_source_url(ctx),
            },
            external_id=result["post_id"],
            external_url=result["url"],
            event_message="X post 已发布。",
        )
        jobs.append_message(job_id, "success", "X post 已发布。")
        jobs.update_job(job_id, status=jobs.DONE, stage="已完成", progress=100, result_filename=ctx["admin_filename"])
    except Exception as exc:
        _update_publication(
            publication_id,
            status="failed",
            error=str(exc),
            event_message="X 发布失败。",
        )
        raise


def _run_wechat_publish_job(job_id: str, publication_id: int, filename: str, media_id: str) -> None:
    jobs.update_job(job_id, status=jobs.RUNNING, stage="提交微信公众号发布…", progress=20)
    data = _wechat_post_json("freepublish/submit", {"media_id": media_id})
    publish_id = data.get("publish_id") or data.get("publishid") or ""
    if not publish_id:
        raise RuntimeError("微信发布接口未返回 publish_id。")
    publication = _get_publication(publication_id) or {}
    payload = publication.get("payload") or {}
    payload.setdefault("wechat", {})
    payload["wechat"].update({
        "media_id": media_id,
        "publish_id": publish_id,
        "submit_response": data,
    })
    _update_publication(
        publication_id,
        status="publish_submitted",
        payload=payload,
        external_id=publish_id,
        event_message="微信公众号发布已提交，等待平台处理。",
    )
    jobs.append_message(job_id, "success", "微信公众号发布已提交，可稍后查询发布状态。")
    jobs.update_job(job_id, status=jobs.DONE, stage="已提交", progress=100, result_filename=filename)


def _check_wechat_publish(publication_id: int, publish_id: str) -> dict[str, str]:
    data = _wechat_post_json("freepublish/get", {"publish_id": publish_id})
    summary = summarize_wechat_publish_result(data)
    publication = _get_publication(publication_id) or {}
    payload = publication.get("payload") or {}
    payload.setdefault("wechat", {})
    payload["wechat"].update({
        "publish_id": publish_id,
        "status_response": data,
    })
    _update_publication(
        publication_id,
        status=summary["status"],
        payload=payload,
        external_url=summary["article_url"],
        event_message="已查询微信公众号发布状态。",
    )
    return summary


@social_publish_bp.route("/")
@login_required
@admin_required
def index():
    from .uploader import _scan_posts

    posts = _scan_posts()[:40]
    all_latest = {}
    for post in posts:
        all_latest[post["filename"]] = _latest_publications(post["filename"])
    return render_template(
        "social_publish_index.html",
        posts=posts,
        platforms=PLATFORMS,
        all_latest=all_latest,
    )


@social_publish_bp.route("/articles/<filename>")
@login_required
@admin_required
def article(filename):
    try:
        ctx = _post_context(filename)
    except FileNotFoundError:
        flash("文章未找到。", "error")
        return redirect(url_for("uploader.articles"))
    latest = _latest_publications(ctx["filename"])
    events = _publication_events([item["id"] for item in latest.values()])
    packages = {
        platform: build_manual_package(ctx, platform)
        for platform, spec in PLATFORMS.items()
        if spec["mode"] == "manual_package"
    }
    return render_template(
        "social_publish_article.html",
        ctx=ctx,
        platforms=PLATFORMS,
        latest=latest,
        events=events,
        packages=packages,
        wechat_config=_wechat_config_status(),
        x_config=_x_config_status(),
    )


@social_publish_bp.route("/articles/<filename>/wechat/draft", methods=["POST"])
@login_required
@admin_required
def wechat_draft(filename):
    try:
        ctx = _post_context(filename)
    except FileNotFoundError:
        flash("文章未找到。", "error")
        return redirect(url_for("uploader.articles"))
    if not _wechat_config_status()["configured"]:
        pub_id = _create_publication(
            ctx["filename"],
            "wechat_mp",
            "not_configured",
            mode="draft",
            error="缺少微信公众号 AppID 或 AppSecret。",
        )
        flash(f"微信公众号未配置，已记录发布项 #{pub_id}。", "warning")
        return redirect(url_for("social_publish.article", filename=ctx["admin_filename"]))

    pub_id = _create_publication(ctx["filename"], "wechat_mp", "pending", mode="draft")
    job_id = jobs.create_job(kind="social_publish_wechat", user_id=session.get("user_id"), title=ctx["title"])
    jobs.submit(_run_wechat_draft_job, job_id, pub_id, ctx)
    return redirect(url_for("social_publish.job_status", job_id=job_id))


@social_publish_bp.route("/articles/<filename>/x/post", methods=["POST"])
@login_required
@admin_required
def x_post(filename):
    try:
        ctx = _post_context(filename)
    except FileNotFoundError:
        flash("文章未找到。", "error")
        return redirect(url_for("uploader.articles"))
    if not _x_config_status()["configured"]:
        pub_id = _create_publication(
            ctx["filename"],
            "x",
            "not_configured",
            mode="post",
            error="缺少 X_USER_ACCESS_TOKEN。",
        )
        flash(f"X 未配置，已记录发布项 #{pub_id}。", "warning")
        return redirect(url_for("social_publish.article", filename=ctx["admin_filename"]))

    pub_id = _create_publication(ctx["filename"], "x", "pending", mode="post")
    job_id = jobs.create_job(kind="social_publish_x", user_id=session.get("user_id"), title=ctx["title"])
    jobs.submit(_run_x_post_job, job_id, pub_id, ctx)
    return redirect(url_for("social_publish.job_status", job_id=job_id))


@social_publish_bp.route("/publications/<int:publication_id>/wechat/publish", methods=["POST"])
@login_required
@admin_required
def wechat_publish(publication_id: int):
    publication = _get_publication(publication_id)
    if not publication or publication.get("platform") != "wechat_mp":
        flash("微信公众号发布记录不存在。", "error")
        return redirect(url_for("social_publish.index"))
    media_id = publication.get("external_id") or (publication.get("payload") or {}).get("wechat", {}).get("media_id", "")
    if not media_id:
        flash("没有可发布的公众号草稿 media_id。", "error")
        return redirect(url_for("social_publish.article", filename=publication["filename"]))
    job_id = jobs.create_job(
        kind="social_publish_wechat_publish",
        user_id=session.get("user_id"),
        title=f"发布 {publication['filename']}",
    )
    jobs.submit(_run_wechat_publish_job, job_id, publication_id, publication["filename"], media_id)
    return redirect(url_for("social_publish.job_status", job_id=job_id))


@social_publish_bp.route("/publications/<int:publication_id>/wechat/check", methods=["POST"])
@login_required
@admin_required
def wechat_check(publication_id: int):
    publication = _get_publication(publication_id)
    if not publication or publication.get("platform") != "wechat_mp":
        flash("微信公众号发布记录不存在。", "error")
        return redirect(url_for("social_publish.index"))
    payload = publication.get("payload") or {}
    publish_id = publication.get("external_id") or payload.get("wechat", {}).get("publish_id", "")
    if not publish_id:
        flash("没有可查询的 publish_id。", "error")
        return redirect(url_for("social_publish.article", filename=publication["filename"]))
    try:
        summary = _check_wechat_publish(publication_id, publish_id)
        if summary.get("article_url"):
            flash("微信公众号发布状态已更新，并记录文章链接。", "success")
        else:
            flash(f"微信公众号发布状态已更新：{summary['status']}。", "info")
    except Exception as exc:
        _update_publication(
            publication_id,
            status="failed",
            error=str(exc),
            event_message="微信公众号发布状态查询失败。",
        )
        flash(f"查询失败：{exc}", "error")
    return redirect(url_for("social_publish.article", filename=publication["filename"]))


@social_publish_bp.route("/articles/<filename>/package/<platform>", methods=["POST"])
@login_required
@admin_required
def create_package(filename, platform):
    if platform not in PLATFORMS or PLATFORMS[platform]["mode"] != "manual_package":
        flash("该平台暂不支持发布包。", "error")
        return redirect(url_for("social_publish.article", filename=filename))
    try:
        ctx = _post_context(filename)
    except FileNotFoundError:
        flash("文章未找到。", "error")
        return redirect(url_for("uploader.articles"))
    package = build_manual_package(ctx, platform)
    _create_publication(
        ctx["filename"],
        platform,
        "package_ready",
        mode="manual",
        payload=package,
    )
    flash(f"{PLATFORMS[platform]['name']}发布包已生成。", "success")
    return redirect(url_for("social_publish.article", filename=ctx["admin_filename"]))


@social_publish_bp.route("/publications/<int:publication_id>/manual-url", methods=["POST"])
@login_required
@admin_required
def manual_url(publication_id: int):
    external_url = request.form.get("external_url", "").strip()
    filename = request.form.get("filename", "").strip()
    if not external_url.startswith(("http://", "https://")):
        flash("请输入有效的发布链接。", "error")
        return redirect(url_for("social_publish.article", filename=filename))
    _update_publication(
        publication_id,
        status="manual_published",
        external_url=external_url,
        event_message="已人工回填发布链接。",
    )
    flash("发布链接已记录。", "success")
    return redirect(url_for("social_publish.article", filename=filename))


@social_publish_bp.route("/jobs/<job_id>")
@login_required
@admin_required
def job_status(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        flash("发布任务不存在或已过期。", "error")
        return redirect(url_for("social_publish.index"))
    return render_template("social_publish_status.html", job=job, job_id=job_id)


@social_publish_bp.route("/jobs/<job_id>/progress")
@login_required
@admin_required
def job_progress(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        return jsonify({"status": "not_found"}), 404
    filename = job.get("result_filename") or ""
    return jsonify({
        "status": job["status"],
        "stage": job.get("stage") or "",
        "progress": job.get("progress") or 0,
        "error": job.get("error"),
        "messages": job.get("messages") or [],
        "social_url": url_for("social_publish.article", filename=filename) if filename else url_for("social_publish.index"),
    })
