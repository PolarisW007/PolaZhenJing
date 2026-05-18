#!/usr/bin/env python3
"""会议创建编排模块 —— 创建日程→加人→订会议室→视频会议。

用法（命令行）：
    python meeting_creator.py \
        --title "Q2 产品复盘" \
        --start "2026-04-15T14:00:00+08:00" \
        --end "2026-04-15T15:00:00+08:00" \
        --users "026828,uid2,uid3" \
        --user-names "王畅,枫华,先雄" \
        [--need-room] \
        [--need-video] \
        [--room-capacity 8]

输出 JSON（stdout）：
    {
        "ok": true,
        "event_id": "evt_xxx",
        "participants_added": true,
        "room": {"room_id": "room_xxx", "name": "6F-春风(8人)"},
        "conference": {"meeting_id": "mtg_xxx", "link": "https://..."},
        "summary": "✅ 会议已创建！..."
    }
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from dws_cli import (
    add_participants,
    book_room,
    create_conference,
    create_event,
    search_available_rooms,
)


def _select_best_room(
    rooms: List[Dict[str, Any]],
    capacity_needed: int,
) -> Optional[Dict[str, Any]]:
    """从空闲会议室列表中选择最合适的。

    选择策略：容量 >= 需求人数，且 <= 需求人数 × 2（避免浪费）。
    同等条件下选容量最小的。
    """
    suitable = []
    for room in rooms:
        cap = room.get("capacity", room.get("roomCapacity", 0))
        if isinstance(cap, str):
            try:
                cap = int(cap)
            except ValueError:
                cap = 0
        if cap >= capacity_needed:
            suitable.append((cap, room))

    if not suitable:
        # 没有满足容量的，取最大的
        if rooms:
            return max(
                rooms,
                key=lambda r: int(r.get("capacity", r.get("roomCapacity", 0)) or 0),
            )
        return None

    # 优先选容量在 [需求, 需求×2] 之间的，再按容量升序
    ideal = [(c, r) for c, r in suitable if c <= capacity_needed * 2]
    if ideal:
        ideal.sort(key=lambda x: x[0])
        return ideal[0][1]

    suitable.sort(key=lambda x: x[0])
    return suitable[0][1]


def _extract_room_id(room: Dict[str, Any]) -> str:
    """提取会议室 ID。"""
    for key in ("roomId", "room_id", "id"):
        if key in room and room[key]:
            return str(room[key])
    return ""


def _extract_room_name(room: Dict[str, Any]) -> str:
    """提取会议室名称。"""
    name = room.get("name", room.get("roomName", room.get("title", "未知会议室")))
    cap = room.get("capacity", room.get("roomCapacity", ""))
    if cap:
        return f"{name}({cap}人间)"
    return name


def run_meeting_creation(
    title: str,
    start: str,
    end: str,
    user_ids: str,
    user_names: str,
    need_room: bool = False,
    need_video: bool = False,
    room_capacity: int = 0,
) -> Dict[str, Any]:
    """执行完整的会议创建流程。

    Returns:
        {
            "ok": bool,
            "event_id": str,
            "participants_added": bool,
            "room": {...} or None,
            "conference": {...} or None,
            "errors": [...],
            "summary": str
        }
    """
    errors: List[str] = []
    result: Dict[str, Any] = {
        "ok": False,
        "event_id": None,
        "participants_added": False,
        "room": None,
        "conference": None,
        "errors": errors,
        "summary": "",
    }

    names_list = [n.strip() for n in user_names.split(",") if n.strip()]
    names_str = "、".join(names_list)

    # ── Step 1: 创建日程 ──────────────────────────────────
    desc_parts = [
        "由智能排会助手自动创建",
        f"参会人：{names_str}",
    ]
    # 如果需要视频会议，预留占位
    if need_video:
        desc_parts.append("🔗 视频会议：创建中...")

    desc = "\n".join(desc_parts)
    event_result = create_event(title=title, start=start, end=end, desc=desc)

    if not event_result.get("ok"):
        errors.append(f"日程创建失败: {event_result.get('error', '未知错误')}")
        result["errors"] = errors
        result["summary"] = "❌ 日程创建失败，请手动创建。"
        return result

    event_data = event_result.get("data", {})
    event_id = ""
    for key in ("eventId", "event_id", "id", "calendarEventId"):
        if key in event_data and event_data[key]:
            event_id = str(event_data[key])
            break
    # 如果 data 是嵌套的
    if not event_id and isinstance(event_data, dict):
        for v in event_data.values():
            if isinstance(v, dict):
                for key in ("eventId", "event_id", "id"):
                    if key in v and v[key]:
                        event_id = str(v[key])
                        break
            if event_id:
                break

    if not event_id:
        # 尝试从 raw 输出提取
        raw = event_data.get("raw", "")
        if "eventId" in str(raw):
            import re
            m = re.search(r'"eventId"\s*:\s*"([^"]+)"', str(raw))
            if m:
                event_id = m.group(1)

    result["event_id"] = event_id

    # ── Step 2: 添加参会人 ────────────────────────────────
    if event_id and user_ids:
        part_result = add_participants(event_id=event_id, user_ids=user_ids)
        if part_result.get("ok"):
            result["participants_added"] = True
        else:
            errors.append(
                f"参会人添加失败: {part_result.get('error', '未知错误')}"
            )
    elif not event_id:
        errors.append("无法添加参会人：缺少 eventId")

    # ── Step 3: 预订会议室（可选）──────────────────────────
    if need_room and event_id:
        room_result = search_available_rooms(start=start, end=end)
        if room_result.get("ok"):
            room_data = room_result.get("data", {})
            rooms = []
            if isinstance(room_data, list):
                rooms = room_data
            else:
                for key in ("rooms", "roomList", "list", "result", "items"):
                    if key in room_data and isinstance(room_data[key], list):
                        rooms = room_data[key]
                        break

            if rooms:
                cap = room_capacity if room_capacity > 0 else len(names_list)
                best_room = _select_best_room(rooms, cap)
                if best_room:
                    room_id = _extract_room_id(best_room)
                    room_name = _extract_room_name(best_room)
                    if room_id:
                        book_result = book_room(
                            event_id=event_id, room_ids=room_id
                        )
                        if book_result.get("ok"):
                            result["room"] = {
                                "room_id": room_id,
                                "name": room_name,
                            }
                        else:
                            errors.append(
                                f"会议室预订失败: {book_result.get('error', '')}"
                            )
                    else:
                        errors.append("无法提取会议室 ID")
                else:
                    errors.append("无合适容量的空闲会议室")
            else:
                errors.append("该时段无空闲会议室")
        else:
            errors.append(
                f"会议室搜索失败: {room_result.get('error', '')}"
            )

    # ── Step 4: 创建视频会议（可选）────────────────────────
    if need_video and event_id:
        conf_result = create_conference(title=title, start=start, end=end)
        if conf_result.get("ok"):
            conf_data = conf_result.get("data", {})
            meeting_id = ""
            link = ""
            for key in ("meetingId", "meeting_id", "id", "conferenceId"):
                if key in conf_data and conf_data[key]:
                    meeting_id = str(conf_data[key])
                    break
            for key in ("meetingLink", "meeting_link", "link", "url", "joinUrl"):
                if key in conf_data and conf_data[key]:
                    link = str(conf_data[key])
                    break
            result["conference"] = {
                "meeting_id": meeting_id,
                "link": link,
            }
        else:
            errors.append(
                f"视频会议创建失败: {conf_result.get('error', '')}"
            )

    # ── 生成摘要 ──────────────────────────────────────────
    result["ok"] = bool(event_id)
    result["summary"] = _build_summary(
        title=title,
        start=start,
        end=end,
        names_str=names_str,
        room=result["room"],
        conference=result["conference"],
        errors=errors,
    )
    return result


def _build_summary(
    title: str,
    start: str,
    end: str,
    names_str: str,
    room: Optional[Dict],
    conference: Optional[Dict],
    errors: List[str],
) -> str:
    """生成最终确认摘要。"""
    from time_utils import format_slot_display, parse_iso

    start_dt = parse_iso(start)
    end_dt = parse_iso(end)
    start_display = format_slot_display(start_dt)
    end_display = end_dt.astimezone(
        __import__("time_utils").TZ_CN
    ).strftime("%H:%M")

    lines = [
        "✅ 会议已创建！",
        "",
        f"📋 {title}",
        f"🕐 {start_display} - {end_display}",
        f"👥 参会人：{names_str}（已发送邀请）",
    ]

    if room:
        lines.append(f"🏢 会议室：{room['name']}")

    if conference:
        link = conference.get("link", "")
        if link:
            lines.append(f"🔗 视频会议：{link}")
        else:
            lines.append("🔗 视频会议：已创建（会议号附在日程描述中）")

    if errors:
        lines.append("")
        lines.append("⚠️ 部分操作有异常：")
        for e in errors:
            lines.append(f"  - {e}")

    return "\n".join(lines)


# ─── CLI 入口 ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="会议创建编排 — 一键创建日程+加人+订会议室+视频会议"
    )
    parser.add_argument("--title", required=True, help="会议主题")
    parser.add_argument("--start", required=True, help="开始时间 (ISO-8601)")
    parser.add_argument("--end", required=True, help="结束时间 (ISO-8601)")
    parser.add_argument(
        "--users", required=True,
        help="参会人 userId 列表，逗号分隔"
    )
    parser.add_argument(
        "--user-names", required=True,
        help="参会人姓名列表，逗号分隔（与 --users 一一对应）"
    )
    parser.add_argument(
        "--need-room", action="store_true", help="是否需要会议室"
    )
    parser.add_argument(
        "--need-video", action="store_true", help="是否需要视频会议"
    )
    parser.add_argument(
        "--room-capacity", type=int, default=0,
        help="会议室容量要求（0=按参会人数自动判断）"
    )
    args = parser.parse_args()

    result = run_meeting_creation(
        title=args.title,
        start=args.start,
        end=args.end,
        user_ids=args.users,
        user_names=args.user_names,
        need_room=args.need_room,
        need_video=args.need_video,
        room_capacity=args.room_capacity,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
