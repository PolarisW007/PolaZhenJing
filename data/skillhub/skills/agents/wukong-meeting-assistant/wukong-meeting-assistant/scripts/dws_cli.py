#!/usr/bin/env python3
"""dws CLI 封装层 —— 统一执行、JSON 解析、错误处理、重试。

所有钉钉操作通过此模块调用 dws CLI 完成，不走 shell。
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

DWS_EXECUTABLE = os.environ.get("DWS_EXECUTABLE", "dws")
MAX_RETRIES = 1
RETRY_DELAY = 1  # seconds


def run_dws(
    *args: str,
    json_output: bool = True,
    auto_yes: bool = False,
    retries: int = MAX_RETRIES,
    timeout: int = 30,
) -> Dict[str, Any]:
    """执行 dws CLI 命令并返回解析后的结果。

    Args:
        *args: dws 子命令和参数，如 ("calendar", "busy", "search", "--users", "uid1,uid2")
        json_output: 是否添加 -f json（默认 True）
        auto_yes: 是否添加 -y（写操作需要）
        retries: 失败重试次数
        timeout: 超时秒数

    Returns:
        {"ok": True, "data": <parsed JSON>} 或
        {"ok": False, "error": "<error message>", "stderr": "<raw stderr>"}
    """
    cmd: List[str] = [DWS_EXECUTABLE] + list(args)
    if json_output:
        cmd.extend(["-f", "json"])
    if auto_yes:
        cmd.append("-y")

    last_error = ""
    for attempt in range(1 + retries):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                stdout = result.stdout.strip()
                if json_output and stdout:
                    try:
                        data = json.loads(stdout)
                        return {"ok": True, "data": data}
                    except json.JSONDecodeError:
                        return {"ok": True, "data": {"raw": stdout}}
                return {"ok": True, "data": {"raw": stdout}}
            else:
                last_error = result.stderr.strip() or result.stdout.strip()
                if attempt < retries:
                    time.sleep(RETRY_DELAY)
                    continue
        except subprocess.TimeoutExpired:
            last_error = f"Command timed out after {timeout}s"
            if attempt < retries:
                time.sleep(RETRY_DELAY)
                continue
        except FileNotFoundError:
            return {
                "ok": False,
                "error": f"dws executable not found: {DWS_EXECUTABLE}",
                "stderr": "",
            }

    return {"ok": False, "error": last_error, "stderr": last_error}


# ─── 通讯录 ───────────────────────────────────────────────

def search_user(keyword: str) -> Dict[str, Any]:
    """按关键词搜索用户，返回用户列表。"""
    return run_dws("contact", "user", "search", "--query", keyword)


def get_self() -> Dict[str, Any]:
    """获取当前登录用户信息。"""
    return run_dws("contact", "user", "get-self")


def search_dept(keyword: str) -> Dict[str, Any]:
    """按关键词搜索部门。"""
    return run_dws("contact", "dept", "search", "--query", keyword)


def list_dept_members(dept_ids: str) -> Dict[str, Any]:
    """获取部门成员列表。dept_ids 为逗号分隔的部门 ID。"""
    return run_dws("contact", "dept", "list-members", "--ids", dept_ids)


# ─── 群聊 ─────────────────────────────────────────────────

def search_chat(keyword: str) -> Dict[str, Any]:
    """按名称搜索群聊。"""
    return run_dws("chat", "search", "--query", keyword)


def list_group_members(conversation_id: str, cursor: str = "0") -> Dict[str, Any]:
    """获取群成员列表（支持分页）。"""
    return run_dws(
        "chat", "group", "members",
        "--id", conversation_id,
        "--cursor", cursor,
    )


# ─── 日程 ─────────────────────────────────────────────────

def search_busy(user_ids: str, start: str, end: str) -> Dict[str, Any]:
    """批量查询用户闲忙状态。

    Args:
        user_ids: 逗号分隔的 userId 列表
        start: ISO-8601 开始时间
        end: ISO-8601 结束时间
    """
    return run_dws(
        "calendar", "busy", "search",
        "--users", user_ids,
        "--start", start,
        "--end", end,
    )


def create_event(title: str, start: str, end: str, desc: str = "") -> Dict[str, Any]:
    """创建日程。"""
    args = [
        "calendar", "event", "create",
        "--title", title,
        "--start", start,
        "--end", end,
    ]
    if desc:
        args.extend(["--desc", desc])
    return run_dws(*args, auto_yes=True)


def add_participants(event_id: str, user_ids: str) -> Dict[str, Any]:
    """为日程添加参会人。"""
    return run_dws(
        "calendar", "participant", "add",
        "--event", event_id,
        "--users", user_ids,
        auto_yes=True,
    )


# ─── 会议室 ───────────────────────────────────────────────

def search_available_rooms(start: str, end: str) -> Dict[str, Any]:
    """搜索指定时段的空闲会议室。"""
    return run_dws(
        "calendar", "room", "search",
        "--start", start,
        "--end", end,
        "--available",
    )


def book_room(event_id: str, room_ids: str) -> Dict[str, Any]:
    """为日程预订会议室。"""
    return run_dws(
        "calendar", "room", "add",
        "--event", event_id,
        "--rooms", room_ids,
        auto_yes=True,
    )


def list_room_groups() -> Dict[str, Any]:
    """获取会议室分组列表。"""
    return run_dws("calendar", "room", "list-groups")


# ─── 视频会议 ─────────────────────────────────────────────

def create_conference(title: str, start: str, end: str) -> Dict[str, Any]:
    """创建预约视频会议（不关联日历日程）。"""
    return run_dws(
        "conference", "meeting", "create",
        "--title", title,
        "--start", start,
        "--end", end,
        auto_yes=True,
    )
