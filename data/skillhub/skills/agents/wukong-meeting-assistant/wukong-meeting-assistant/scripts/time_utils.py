#!/usr/bin/env python3
"""时间工具模块 —— ISO-8601 生成、工作时间判断、时间范围辅助。"""

from datetime import datetime, timedelta, timezone

TZ_CN = timezone(timedelta(hours=8))

# 工作时间定义
WORK_MORNING_START = 9   # 09:00
WORK_MORNING_END = 12    # 12:00
WORK_AFTERNOON_START = 13 # 13:00
WORK_AFTERNOON_END = 18   # 18:00

SLOT_MINUTES = 30  # 时间槽粒度


def now_cn() -> datetime:
    """返回当前中国标准时间。"""
    return datetime.now(TZ_CN)


def to_iso(dt: datetime) -> str:
    """将 datetime 转为 ISO-8601 字符串（+08:00 时区）。"""
    dt_cn = dt.astimezone(TZ_CN)
    return dt_cn.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def parse_iso(s: str) -> datetime:
    """解析 ISO-8601 字符串为 datetime（带时区）。"""
    # 处理 +08:00 格式
    s = s.strip()
    if s.endswith("+08:00"):
        s_clean = s.replace("+08:00", "+0800")
    elif s.endswith("Z"):
        s_clean = s.replace("Z", "+0000")
    else:
        s_clean = s
    try:
        return datetime.strptime(s_clean, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        # 尝试不带秒
        return datetime.strptime(s_clean, "%Y-%m-%dT%H:%M%z")


def is_work_hour(dt: datetime) -> bool:
    """判断是否在工作时间内（09:00-12:00, 13:00-18:00）。"""
    h = dt.astimezone(TZ_CN).hour
    m = dt.astimezone(TZ_CN).minute
    t = h + m / 60.0
    return (WORK_MORNING_START <= t < WORK_MORNING_END or
            WORK_AFTERNOON_START <= t < WORK_AFTERNOON_END)


def is_morning(dt: datetime) -> bool:
    """判断是否在上午。"""
    h = dt.astimezone(TZ_CN).hour
    return WORK_MORNING_START <= h < WORK_MORNING_END


def generate_work_slots(start: datetime, end: datetime) -> list:
    """在 start~end 范围内生成工作时间 slot 列表。

    每个 slot 为 (slot_start: datetime, slot_end: datetime) 元组。
    仅包含工作时间段（09:00-12:00, 13:00-18:00），排除午休和非工作时间。

    Returns:
        List of (slot_start, slot_end) tuples
    """
    slots = []
    current_day = start.astimezone(TZ_CN).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_cn = end.astimezone(TZ_CN)

    while current_day.date() <= end_cn.date():
        # 跳过周末
        if current_day.weekday() < 5:  # 0=Mon, 4=Fri
            # 上午 slots
            for work_start_h, work_end_h in [
                (WORK_MORNING_START, WORK_MORNING_END),
                (WORK_AFTERNOON_START, WORK_AFTERNOON_END),
            ]:
                slot_time = current_day.replace(hour=work_start_h, minute=0)
                work_end_time = current_day.replace(hour=work_end_h, minute=0)

                while slot_time + timedelta(minutes=SLOT_MINUTES) <= work_end_time:
                    slot_end = slot_time + timedelta(minutes=SLOT_MINUTES)
                    # 确保在用户指定的范围内
                    if slot_end > start.astimezone(TZ_CN) and slot_time < end_cn:
                        slots.append((
                            max(slot_time, start.astimezone(TZ_CN)),
                            min(slot_end, end_cn),
                        ))
                    slot_time = slot_end

        current_day += timedelta(days=1)

    return slots


def format_slot_display(dt: datetime) -> str:
    """格式化时间用于展示：周X MM/DD HH:MM。"""
    dt_cn = dt.astimezone(TZ_CN)
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    wd = weekdays[dt_cn.weekday()]
    return f"{wd} {dt_cn.strftime('%m/%d %H:%M')}"


def get_next_workdays(n: int = 5) -> tuple:
    """获取从明天起的 N 个工作日范围。

    Returns:
        (start_iso, end_iso) 元组
    """
    now = now_cn()
    current = now + timedelta(days=1)
    count = 0
    end_day = current

    while count < n:
        if current.weekday() < 5:
            count += 1
            end_day = current
        current += timedelta(days=1)

    start_dt = (now + timedelta(days=1)).replace(
        hour=WORK_MORNING_START, minute=0, second=0, microsecond=0
    )
    # 如果今天还在工作时间内，从今天开始
    if is_work_hour(now):
        start_dt = now

    end_dt = end_day.replace(
        hour=WORK_AFTERNOON_END, minute=0, second=0, microsecond=0
    )

    return to_iso(start_dt), to_iso(end_dt)
