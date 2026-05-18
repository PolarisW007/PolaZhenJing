#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
千里眼 v3 —— 群消息采集 + Markdown 写入（时间段全群检索版）

【v3 升级要点】
1. 时间段全群检索：不再"搜群→逐群拉消息"，改用 `dws chat message search --keyword`
   跨全会话 + 时间窗搜索，彻底解除"群枚举不全"的历史问题。
2. 为每个群生成钉钉深链（dingtalk://dingtalkclient/action/openconversation?conversationId=xxx）
   和网页兜底链接（https://im.dingtalk.com/?conversationId=xxx），写入 Markdown 与 JSON。
3. 额外输出 JSON 结构化文件，方便 Agent 做跨会话语义合并 + 多维表写入。
4. CLI 兼容 v2：--date / --start-date / --end-date / --week / --customer 等参数不变；
   新增 --keywords（默认 "悟空"）、--limit-per-page 等。

脚本职责：采集 + 原始聚合，不做 LLM 分析。
Agent 职责：读 JSON → LLM 分簇合并 → 按目标列顺序写多维表 z2uCFiw。
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

logging.basicConfig(
    level=os.environ.get("KEEN_LOG_LEVEL", "INFO"),
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("keen-v3")

# ---------------------------------------------------------------------------
# 常量与默认值
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_ROOT = _SCRIPT_DIR.parent
_DEFAULT_OUT_DIR = Path(os.environ.get("KEEN_V3_OUT_DIR", _SKILL_ROOT / "out"))

# 默认搜索关键词（v3 倾向于单词搜索+时间窗，关键词用于跨全会话过滤）
_DEFAULT_KEYWORDS: List[str] = ["悟空"]

# 搜索分页
_SEARCH_LIMIT = 100
_MAX_PAGES = 50  # 单关键词最多翻 50 页（5000 条），防止无限循环
_PAGE_SLEEP = 0.3  # 翻页间隔秒

# 时间范围上限
_MAX_RANGE_DAYS = 14


class DateRangeError(ValueError):
    pass


# ---------------------------------------------------------------------------
# dws CLI 封装
# ---------------------------------------------------------------------------


def _find_dws() -> str:
    override = os.environ.get("DWS_EXECUTABLE", "").strip()
    if override and Path(override).exists():
        return override
    found = shutil.which("dws")
    if found:
        return found
    raise RuntimeError("未找到 dws CLI，请安装或设置环境变量 DWS_EXECUTABLE。")


def _run_cmd(cmd: List[str], timeout: int = 90) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"timeout after {timeout}s"


def _parse_json(text: str, ctx: str = "") -> Union[dict, list]:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析 JSON 失败[{ctx}]: {e}; text head: {text[:200]}")


def _unwrap(data: Union[dict, list]) -> dict:
    """剥掉 dws 外层 {arguments/errorCode/result/success} 包装。"""
    if isinstance(data, dict):
        if "result" in data and isinstance(data["result"], dict):
            return data["result"]
        if "data" in data and isinstance(data["data"], dict):
            return data["data"]
    if isinstance(data, list):
        return {"items": data}
    return data if isinstance(data, dict) else {}


# ---------------------------------------------------------------------------
# 日期解析
# ---------------------------------------------------------------------------


def _today() -> date:
    return datetime.now().date()


def _parse_date(text: str) -> date:
    text = text.strip()
    today = _today()
    mapping = {
        "今天": 0, "today": 0,
        "昨天": -1, "yesterday": -1,
        "前天": -2,
    }
    if text.lower() in mapping:
        return today + timedelta(days=mapping[text.lower()])
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise DateRangeError(f"无法解析日期: {text}")


def _resolve_date_range(
    date_str: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    week: Optional[str],
) -> Tuple[date, date]:
    today = _today()
    if week:
        wk = week.strip()
        # 周一为 monday=0
        this_monday = today - timedelta(days=today.weekday())
        if wk in ("本周", "this_week"):
            start = this_monday
            end = min(this_monday + timedelta(days=4), today)
        elif wk in ("上周", "last_week"):
            start = this_monday - timedelta(days=7)
            end = start + timedelta(days=4)
        else:
            raise DateRangeError(f"未知 --week 值: {week}")
        return start, end
    if start_date and end_date:
        s = _parse_date(start_date)
        e = _parse_date(end_date)
        if e < s:
            raise DateRangeError("--end-date 早于 --start-date")
        if (e - s).days + 1 > _MAX_RANGE_DAYS:
            raise DateRangeError(f"时间段超过 {_MAX_RANGE_DAYS} 天上限")
        return s, e
    if date_str:
        d = _parse_date(date_str)
        return d, d
    # 默认今天
    return today, today


def _format_range_label(start: date, end: date) -> str:
    if start == end:
        return start.isoformat()
    return f"{start.isoformat()}~{end.isoformat()}"


# ---------------------------------------------------------------------------
# 关键词解析
# ---------------------------------------------------------------------------


def _parse_keywords(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    # 支持多种分隔符
    tokens = re.split(r"[,，、/|\s]+", raw)
    result = [t.strip() for t in tokens if t.strip()]
    return result[:20]


# ---------------------------------------------------------------------------
# 核心：跨全会话时间窗搜索
# ---------------------------------------------------------------------------


def _search_keyword_window(
    dws: str,
    keyword: str,
    start_iso: str,
    end_iso: str,
) -> List[dict]:
    """
    调用 dws chat message search，分页拉取指定关键词在时间窗内命中的所有消息。
    返回的 list 元素结构：
      {
        "conversation_id": str,
        "group_name": str,
        "is_single_chat": bool,
        "sender": str,
        "create_time": str,    # 2026-04-20 18:45:04
        "content": str,        # 纯文本
        "content_type": int,
        "keyword": str,        # 命中关键词
      }
    """
    results: List[dict] = []
    cursor = "0"
    for page in range(_MAX_PAGES):
        cmd = [
            dws, "chat", "message", "search",
            "--keyword", keyword,
            "--start", start_iso,
            "--end", end_iso,
            "--limit", str(_SEARCH_LIMIT),
            "--cursor", cursor,
            "--format", "json",
        ]
        rc, out, err = _run_cmd(cmd, timeout=90)
        if rc != 0:
            log.warning("搜索 [%s] page %d 失败 rc=%s err=%s", keyword, page, rc, err[:200])
            break
        data = _unwrap(_parse_json(out, ctx=f"search:{keyword}:p{page}"))
        conv_list = data.get("conversationMessagesList") or []
        for conv in conv_list:
            conv_id = conv.get("openConversationId", "")
            title = conv.get("title", "")
            is_single = bool(conv.get("singleChat", False))
            messages = conv.get("messages") or []
            for m in messages:
                content_raw = m.get("content", "") or ""
                # 钉钉消息 content 是嵌套 JSON 字符串
                text = ""
                ctype = 0
                try:
                    if isinstance(content_raw, str) and content_raw.startswith("{"):
                        cj = json.loads(content_raw)
                        ctype = cj.get("contentType", 0)
                        tc = cj.get("textContent") or {}
                        text = (tc.get("text") or "").strip()
                        if not text:
                            # 富文本 / 文件 / markdown 等
                            text = (cj.get("content") or
                                    cj.get("markdown") or
                                    str(cj.get("fileContent") or "") or
                                    "").strip()
                    else:
                        text = str(content_raw).strip()
                except (json.JSONDecodeError, TypeError):
                    text = str(content_raw).strip()
                if not text:
                    continue
                results.append({
                    "conversation_id": conv_id,
                    "group_name": title,
                    "is_single_chat": is_single,
                    "sender": m.get("sender", ""),
                    "create_time": m.get("createTime", ""),
                    "content": text[:5000],
                    "content_type": ctype,
                    "keyword": keyword,
                })
        has_more = bool(data.get("hasMore", False))
        next_cursor = data.get("nextCursor", "")
        if not has_more or not next_cursor:
            break
        cursor = str(next_cursor)
        time.sleep(_PAGE_SLEEP)
    log.info("关键词 [%s] 命中 %d 条消息（%d 页）", keyword, len(results), page + 1)
    return results


# ---------------------------------------------------------------------------
# 去重 + 群链接生成
# ---------------------------------------------------------------------------


def _dedup_by_conv_time_sender(messages: List[dict]) -> List[dict]:
    """
    同一关键词循环命中 + 多关键词命中同一条消息时去重。
    key = (conversation_id, create_time, sender, content[:200])
    """
    seen = set()
    out = []
    for m in messages:
        k = (m["conversation_id"], m["create_time"], m["sender"], m["content"][:200])
        if k in seen:
            continue
        seen.add(k)
        out.append(m)
    return out


def _build_group_link(conversation_id: str) -> Dict[str, str]:
    """生成钉钉深链和网页兜底链接。"""
    if not conversation_id:
        return {"deep_link": "", "web_link": ""}
    encoded = urllib.parse.quote(conversation_id, safe="")
    return {
        "deep_link": f"dingtalk://dingtalkclient/action/openconversation?conversationId={encoded}",
        "web_link": f"https://im.dingtalk.com/?conversationId={encoded}",
    }


def _group_by_conversation(messages: List[dict]) -> List[dict]:
    """按 conversation_id 聚合，同时按时间正序排列。"""
    buckets: Dict[str, List[dict]] = defaultdict(list)
    name_map: Dict[str, str] = {}
    is_single_map: Dict[str, bool] = {}
    for m in messages:
        cid = m["conversation_id"]
        buckets[cid].append(m)
        name_map[cid] = m["group_name"]
        is_single_map[cid] = m["is_single_chat"]

    result = []
    for cid, msgs in buckets.items():
        # 按时间正序（老→新）
        msgs_sorted = sorted(msgs, key=lambda x: x["create_time"])
        links = _build_group_link(cid)
        result.append({
            "conversation_id": cid,
            "group_name": name_map[cid] or "(未命名会话)",
            "is_single_chat": is_single_map[cid],
            "message_count": len(msgs_sorted),
            "deep_link": links["deep_link"],
            "web_link": links["web_link"],
            "messages": msgs_sorted,
        })
    # 按消息数降序，单聊排后面
    result.sort(key=lambda x: (x["is_single_chat"], -x["message_count"]))
    return result


# ---------------------------------------------------------------------------
# 输出：Markdown + JSON
# ---------------------------------------------------------------------------


def _write_markdown(
    out_dir: Path,
    customer: str,
    user: str,
    date_label: str,
    keywords: List[str],
    start_iso: str,
    end_iso: str,
    groups_data: List[dict],
) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    fp = out_dir / f"keen-v3-{ts}.md"
    out_dir.mkdir(parents=True, exist_ok=True)

    total_groups = len(groups_data)
    total_msgs = sum(g["message_count"] for g in groups_data)

    lines: List[str] = []
    lines.append("# 千里眼 v3 群消息情报采集\n")
    lines.append(f"- 客户/主题：{customer}")
    lines.append(f"- 采集人：{user}")
    lines.append(f"- 时间窗口：{start_iso} ~ {end_iso}")
    lines.append(f"- 目标日期标签：{date_label}")
    lines.append(f"- 搜索关键词：{', '.join(keywords)}")
    lines.append(f"- 会话数：{total_groups}")
    lines.append(f"- 消息总数：{total_msgs}")
    lines.append(f"- 采集时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    if total_msgs == 0:
        lines.append("> 本次采集未命中任何消息。\n")
    else:
        for gd in groups_data:
            tag = "单聊" if gd["is_single_chat"] else "群聊"
            lines.append("---\n")
            lines.append(f"## [{tag}] {gd['group_name']} · {gd['message_count']} 条\n")
            lines.append(f"- 钉钉深链：{gd['deep_link']}")
            lines.append(f"- 网页链接：{gd['web_link']}")
            lines.append("")
            for m in gd["messages"]:
                lines.append(f"### {m['sender']} · {m['create_time']}")
                content = m["content"].replace("\n", "\n> ")
                lines.append(f"> {content}")
                lines.append("")

    fp.write_text("\n".join(lines), encoding="utf-8")
    return fp


def _write_json(
    out_dir: Path,
    customer: str,
    user: str,
    date_label: str,
    keywords: List[str],
    start_iso: str,
    end_iso: str,
    groups_data: List[dict],
) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    fp = out_dir / f"keen-v3-{ts}.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "v3",
        "customer": customer,
        "user": user,
        "date_label": date_label,
        "start_iso": start_iso,
        "end_iso": end_iso,
        "keywords": keywords,
        "collected_at": datetime.now().isoformat(),
        "total_groups": len(groups_data),
        "total_messages": sum(g["message_count"] for g in groups_data),
        "groups": groups_data,
    }
    fp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp


# ---------------------------------------------------------------------------
# CLI + 主流程
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="千里眼 v3 —— 时间段全群检索采集")
    p.add_argument("--customer", default=os.environ.get("DINGTALK_CUSTOMER", "自定义"),
                   help="客户/主题名")
    p.add_argument("--user", default=os.environ.get("KEEN_USER_NAME", ""),
                   help="采集人名字")
    p.add_argument("--keywords", default=None,
                   help="跨会话搜索关键词（, / | 分隔，最多20个；默认'悟空'）")
    p.add_argument("--date", default=None, dest="date_str",
                   help="目标日期（YYYY-MM-DD/今天/昨天/前天）")
    p.add_argument("--start-date", default=None, help="起始日期")
    p.add_argument("--end-date", default=None, help="结束日期")
    p.add_argument("--week", default=None, help="本周 / 上周")
    p.add_argument("--start-time", default="00:00:00",
                   help="起始时间 HH:MM:SS（默认 00:00:00）")
    p.add_argument("--end-time", default=None,
                   help="结束时间 HH:MM:SS（默认今天=当前时刻，过去日=23:59:59）")
    p.add_argument("--out-dir", default=str(_DEFAULT_OUT_DIR),
                   help=f"输出目录（默认 {_DEFAULT_OUT_DIR}）")
    p.add_argument("--tz-offset", default="+08:00",
                   help="时区偏移（默认 +08:00）")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    customer = args.customer.strip()
    user = args.user.strip() or customer

    # 1. 时间范围
    try:
        start_d, end_d = _resolve_date_range(
            date_str=args.date_str,
            start_date=args.start_date,
            end_date=args.end_date,
            week=args.week,
        )
    except DateRangeError as e:
        log.error("时间范围错误: %s", e)
        return 1

    # 2. 拼 ISO 时间窗
    today = _today()
    start_iso = f"{start_d.isoformat()}T{args.start_time}{args.tz_offset}"
    if args.end_time:
        end_iso = f"{end_d.isoformat()}T{args.end_time}{args.tz_offset}"
    elif end_d == today:
        now_str = datetime.now().strftime("%H:%M:%S")
        end_iso = f"{end_d.isoformat()}T{now_str}{args.tz_offset}"
    else:
        end_iso = f"{end_d.isoformat()}T23:59:59{args.tz_offset}"
    date_label = _format_range_label(start_d, end_d)
    log.info("时间窗口: %s ~ %s（标签 %s）", start_iso, end_iso, date_label)

    # 3. 关键词
    keywords = _parse_keywords(args.keywords) or list(_DEFAULT_KEYWORDS)
    log.info("关键词: %s", keywords)

    # 4. 找 dws
    try:
        dws = _find_dws()
    except RuntimeError as e:
        log.error(str(e))
        return 1

    # 5. 逐关键词跨全会话搜索
    all_msgs: List[dict] = []
    for kw in keywords:
        msgs = _search_keyword_window(dws, kw, start_iso, end_iso)
        all_msgs.extend(msgs)

    log.info("合计命中 %d 条（去重前）", len(all_msgs))
    deduped = _dedup_by_conv_time_sender(all_msgs)
    log.info("去重后 %d 条", len(deduped))

    # 6. 按会话聚合
    groups_data = _group_by_conversation(deduped)

    # 7. 写输出
    out_dir = Path(args.out_dir)
    md_path = _write_markdown(out_dir, customer, user, date_label,
                              keywords, start_iso, end_iso, groups_data)
    json_path = _write_json(out_dir, customer, user, date_label,
                            keywords, start_iso, end_iso, groups_data)

    log.info("Markdown: %s", md_path)
    log.info("JSON: %s", json_path)

    # 8. stdout 信号（Agent 捕获）
    print(f"KEEN_V3_MARKDOWN_FILE:{md_path}")
    print(f"KEEN_V3_JSON_FILE:{json_path}")
    print(f"KEEN_V3_TOTAL_GROUPS:{len(groups_data)}")
    print(f"KEEN_V3_TOTAL_MESSAGES:{sum(g['message_count'] for g in groups_data)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
