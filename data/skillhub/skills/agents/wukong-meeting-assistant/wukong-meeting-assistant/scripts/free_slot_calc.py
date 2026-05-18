#!/usr/bin/env python3
"""空闲窗口计算算法 —— 30min 粒度 slot 矩阵、评分排序、Top-N 推荐。

用法（命令行）：
    python free_slot_calc.py \
        --busy '<闲忙查询 JSON>' \
        --start '2026-04-14T09:00:00+08:00' \
        --end '2026-04-18T18:00:00+08:00' \
        --duration 60 \
        --users '{"uid1":"张三","uid2":"李四"}' \
        --top 3

输出 JSON（stdout）：
    {
        "ok": true,
        "slots": [
            {
                "rank": 1,
                "start": "2026-04-15T14:00:00+08:00",
                "end": "2026-04-15T15:00:00+08:00",
                "display": "周二 04/15 14:00 - 15:00",
                "available_count": 6,
                "total_count": 6,
                "conflicts": [],
                "score": 1000
            }
        ],
        "total_users": 6,
        "all_free_exists": true
    }
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from time_utils import (
    TZ_CN,
    SLOT_MINUTES,
    format_slot_display,
    generate_work_slots,
    is_morning,
    is_work_hour,
    now_cn,
    parse_iso,
    to_iso,
)


# ─── 闲忙数据解析 ─────────────────────────────────────────

def _parse_busy_periods(
    busy_data: Any,
) -> Dict[str, List[Tuple[datetime, datetime]]]:
    """解析 dws calendar busy search 返回的闲忙数据。

    返回: {userId: [(busy_start, busy_end), ...]}

    dws 返回格式可能为:
      - {"busyList": {"userId1": [{"start":.., "end":..}], ...}}
      - [{"userId":"uid1", "busyPeriods": [{"start":.., "end":..}]}]
      - 其他变体
    """
    result: Dict[str, List[Tuple[datetime, datetime]]] = {}

    if isinstance(busy_data, dict):
        container = busy_data
        for key in ("busyList", "busy", "data", "result"):
            if key in busy_data and isinstance(busy_data[key], dict):
                container = busy_data[key]
                break

        for uid, periods in container.items():
            if isinstance(periods, list):
                parsed = []
                for p in periods:
                    if isinstance(p, dict):
                        s = p.get("start", p.get("startTime", ""))
                        e = p.get("end", p.get("endTime", ""))
                        if s and e:
                            try:
                                parsed.append((parse_iso(s), parse_iso(e)))
                            except (ValueError, TypeError):
                                continue
                result[uid] = parsed

    elif isinstance(busy_data, list):
        for item in busy_data:
            if not isinstance(item, dict):
                continue
            uid = item.get("userId", item.get("userid", item.get("uid", "")))
            periods = item.get(
                "busyPeriods",
                item.get("busy", item.get("periods", [])),
            )
            if uid and isinstance(periods, list):
                parsed = []
                for p in periods:
                    if isinstance(p, dict):
                        s = p.get("start", p.get("startTime", ""))
                        e = p.get("end", p.get("endTime", ""))
                        if s and e:
                            try:
                                parsed.append((parse_iso(s), parse_iso(e)))
                            except (ValueError, TypeError):
                                continue
                result[uid] = parsed

    return result


def _is_slot_busy(
    slot_start: datetime,
    slot_end: datetime,
    busy_periods: List[Tuple[datetime, datetime]],
) -> bool:
    """判断一个 slot 是否与任意忙碌时段重叠。"""
    for busy_start, busy_end in busy_periods:
        if slot_start < busy_end and slot_end > busy_start:
            return True
    return False


# ─── 核心算法：空闲窗口计算 ─────────────────────────────────

def calculate_free_windows(
    busy_data: Any,
    range_start: str,
    range_end: str,
    duration_minutes: int,
    user_map: Dict[str, str],
    top_n: int = 3,
) -> Dict[str, Any]:
    """计算所有参会人的共同空闲窗口并评分排序。

    Args:
        busy_data: dws calendar busy search 的原始返回数据
        range_start: 搜索范围开始时间 (ISO-8601)
        range_end: 搜索范围结束时间 (ISO-8601)
        duration_minutes: 所需会议时长（分钟）
        user_map: {userId: userName} 映射
        top_n: 返回推荐数量

    Returns:
        {"ok": True, "slots": [...], "total_users": N, "all_free_exists": bool}
    """
    start_dt = parse_iso(range_start)
    end_dt = parse_iso(range_end)
    all_user_ids = list(user_map.keys())
    total_users = len(all_user_ids)

    # 1) 解析忙碌时段
    busy_periods = _parse_busy_periods(busy_data)

    # 2) 生成工作时间 slot 列表
    work_slots = generate_work_slots(start_dt, end_dt)
    if not work_slots:
        return {
            "ok": False,
            "error": "指定时间范围内无可用工作时间 slot",
            "slots": [],
            "total_users": total_users,
            "all_free_exists": False,
        }

    # 3) 对每个 slot 计算每个用户是否空闲
    #    slot_availability[i] = set of available userIds
    slots_needed = duration_minutes // SLOT_MINUTES
    if slots_needed < 1:
        slots_needed = 1

    slot_availability: List[Set[str]] = []
    for slot_start, slot_end in work_slots:
        available = set()
        for uid in all_user_ids:
            user_busy = busy_periods.get(uid, [])
            if not _is_slot_busy(slot_start, slot_end, user_busy):
                available.add(uid)
        slot_availability.append(available)

    # 4) 滑动窗口：找到连续 slots_needed 个 slot 的窗口
    windows: List[Dict[str, Any]] = []
    for i in range(len(work_slots) - slots_needed + 1):
        # 检查连续性：所有 slot 必须在同一天且时间连续
        window_start = work_slots[i][0]
        window_end = work_slots[i + slots_needed - 1][1]

        # 验证连续性（slot 之间无间隔）
        is_continuous = True
        for j in range(i, i + slots_needed - 1):
            if work_slots[j][1] != work_slots[j + 1][0]:
                is_continuous = False
                break
        if not is_continuous:
            continue

        # 窗口内所有 slot 都空闲的用户 = 交集
        available_in_window = slot_availability[i].copy()
        for j in range(i + 1, i + slots_needed):
            available_in_window &= slot_availability[j]

        available_count = len(available_in_window)
        conflict_uids = set(all_user_ids) - available_in_window
        conflict_names = [user_map.get(uid, uid) for uid in conflict_uids]

        # 5) 评分
        score = _score_window(
            window_start, window_end, available_count, total_users
        )

        windows.append({
            "start": to_iso(window_start),
            "end": to_iso(window_end),
            "display_start": format_slot_display(window_start),
            "display_end": window_end.astimezone(TZ_CN).strftime("%H:%M"),
            "display": (
                f"{format_slot_display(window_start)} - "
                f"{window_end.astimezone(TZ_CN).strftime('%H:%M')}"
            ),
            "available_count": available_count,
            "total_count": total_users,
            "conflicts": sorted(conflict_names),
            "score": score,
        })

    # 6) 排序（score 降序）并取 Top-N
    windows.sort(key=lambda w: w["score"], reverse=True)
    top_windows = windows[:top_n]

    # 添加排名
    for idx, w in enumerate(top_windows, 1):
        w["rank"] = idx

    all_free_exists = any(w["available_count"] == total_users for w in top_windows)

    return {
        "ok": len(top_windows) > 0,
        "slots": top_windows,
        "total_users": total_users,
        "all_free_exists": all_free_exists,
        "total_candidates": len(windows),
    }


def _score_window(
    start: datetime,
    end: datetime,
    available_count: int,
    total_count: int,
) -> float:
    """为一个候选窗口计算综合评分。

    评分规则（权重从高到低）：
    1. 全员可参加 >> 部分人可参加（可参加人数 × 100）
    2. 工作时间 > 非工作时间（+50）
    3. 上午 > 下午（+20）
    4. 离当前时间越近越优先（距今天数越少分越高）
    """
    score = 0.0

    # 维度1：可参加人数（最高权重）
    score += available_count * 100
    # 全员额外加分
    if available_count == total_count:
        score += 500

    # 维度2：工作时间
    if is_work_hour(start):
        score += 50

    # 维度3：上午优先
    if is_morning(start):
        score += 20

    # 维度4：时间越近越好（以天为单位衰减）
    days_from_now = (start.astimezone(TZ_CN) - now_cn()).total_seconds() / 86400
    if days_from_now > 0:
        score += max(0, 30 - days_from_now * 3)

    return round(score, 2)


# ─── CLI 入口 ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="空闲窗口计算 — 输入闲忙数据，输出 Top-N 推荐时段"
    )
    parser.add_argument(
        "--busy", required=True,
        help="dws calendar busy search 返回的 JSON 字符串"
    )
    parser.add_argument(
        "--start", required=True,
        help="搜索范围开始时间 (ISO-8601)"
    )
    parser.add_argument(
        "--end", required=True,
        help="搜索范围结束时间 (ISO-8601)"
    )
    parser.add_argument(
        "--duration", type=int, default=60,
        help="会议时长（分钟），默认 60"
    )
    parser.add_argument(
        "--users", required=True,
        help='用户映射 JSON: {"userId":"userName",...}'
    )
    parser.add_argument(
        "--top", type=int, default=3,
        help="推荐数量，默认 3"
    )
    args = parser.parse_args()

    try:
        busy_data = json.loads(args.busy)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"Invalid busy JSON: {e}"}))
        sys.exit(1)

    try:
        user_map = json.loads(args.users)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"Invalid users JSON: {e}"}))
        sys.exit(1)

    result = calculate_free_windows(
        busy_data=busy_data,
        range_start=args.start,
        range_end=args.end,
        duration_minutes=args.duration,
        user_map=user_map,
        top_n=args.top,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
