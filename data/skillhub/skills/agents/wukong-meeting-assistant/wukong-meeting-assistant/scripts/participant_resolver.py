#!/usr/bin/env python3
"""参会人解析模块 —— 将 @人名/@部门/@群 解析为 userId 列表。

用法（命令行）：
    python participant_resolver.py --input '<JSON>' --include-self

输入 JSON 格式：
    {
        "participants": [
            {"type": "user", "name": "福锤"},
            {"type": "department", "name": "开放平台"},
            {"type": "group", "name": "悟空核心群"}
        ]
    }

输出 JSON（stdout）：
    {
        "ok": true,
        "users": [
            {"userId": "026828", "name": "王畅", "source": "user:福锤"}
        ],
        "ambiguous": [
            {"type": "user", "name": "张伟", "candidates": [...]}
        ],
        "not_found": ["xxx"],
        "warnings": ["群'悟空核心群'有 82 人，已全部展开"]
    }
"""

import argparse
import json
import sys
from typing import Any, Dict, List

from dws_cli import (
    get_self,
    list_dept_members,
    list_group_members,
    search_chat,
    search_dept,
    search_user,
)

LARGE_GROUP_THRESHOLD = 50


def _extract_users_from_result(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从 dws CLI 返回结果中提取用户列表。"""
    if not result.get("ok"):
        return []
    data = result.get("data", {})
    # dws 返回格式可能是 list 或 dict with users/members key
    if isinstance(data, list):
        return data
    for key in ("users", "members", "userList", "memberList", "list", "result"):
        if key in data and isinstance(data[key], list):
            return data[key]
    return []


def _extract_id(item: Dict[str, Any], key_candidates: list) -> str:
    """从返回项中提取 ID 字段。"""
    for k in key_candidates:
        if k in item and item[k]:
            return str(item[k])
    return ""


def resolve_user(name: str) -> Dict[str, Any]:
    """解析单个用户名 → userId。

    Returns:
        {"ok": True, "users": [{"userId":..., "name":...}]}
        {"ok": False, "ambiguous": True, "candidates": [...]}
        {"ok": False, "not_found": True}
    """
    result = search_user(name)
    if not result.get("ok"):
        return {"ok": False, "not_found": True, "error": result.get("error", "")}

    users = _extract_users_from_result(result)
    if not users:
        return {"ok": False, "not_found": True}

    if len(users) == 1:
        u = users[0]
        uid = _extract_id(u, ["userId", "userid", "uid", "id"])
        uname = u.get("name", u.get("nick", u.get("nickName", name)))
        return {"ok": True, "users": [{"userId": uid, "name": uname}]}

    # 多个匹配 → 需要用户消歧
    candidates = []
    for u in users:
        uid = _extract_id(u, ["userId", "userid", "uid", "id"])
        uname = u.get("name", u.get("nick", ""))
        dept = u.get("dept", u.get("deptName", u.get("department", "")))
        candidates.append({"userId": uid, "name": uname, "dept": dept})
    return {"ok": False, "ambiguous": True, "candidates": candidates}


def resolve_department(dept_name: str) -> Dict[str, Any]:
    """解析部门名 → 展开全部成员。

    Returns:
        {"ok": True, "users": [...], "dept_name": ..., "dept_id": ...}
        {"ok": False, "ambiguous": True, "candidates": [...]}
        {"ok": False, "not_found": True}
    """
    result = search_dept(dept_name)
    if not result.get("ok"):
        return {"ok": False, "not_found": True, "error": result.get("error", "")}

    depts = _extract_users_from_result(result)
    if not depts:
        return {"ok": False, "not_found": True}

    if len(depts) > 1:
        candidates = []
        for d in depts:
            did = _extract_id(d, ["deptId", "dept_id", "id"])
            dname = d.get("name", d.get("deptName", ""))
            candidates.append({"deptId": did, "name": dname})
        return {"ok": False, "ambiguous": True, "candidates": candidates}

    dept = depts[0]
    dept_id = _extract_id(dept, ["deptId", "dept_id", "id"])
    actual_name = dept.get("name", dept.get("deptName", dept_name))

    # 展开成员
    members_result = list_dept_members(dept_id)
    members = _extract_users_from_result(members_result)

    users = []
    for m in members:
        uid = _extract_id(m, ["userId", "userid", "uid", "id"])
        uname = m.get("name", m.get("nick", ""))
        if uid:
            users.append({"userId": uid, "name": uname})

    return {
        "ok": True,
        "users": users,
        "dept_name": actual_name,
        "dept_id": dept_id,
    }


def resolve_group(group_name: str) -> Dict[str, Any]:
    """解析群名 → 展开全部成员。

    Returns:
        {"ok": True, "users": [...], "group_name": ..., "conversation_id": ...}
        {"ok": False, "ambiguous": True, "candidates": [...]}
        {"ok": False, "not_found": True}
    """
    result = search_chat(group_name)
    if not result.get("ok"):
        return {"ok": False, "not_found": True, "error": result.get("error", "")}

    data = result.get("data", {})
    groups = []
    if isinstance(data, list):
        groups = data
    else:
        for key in ("conversations", "groups", "list", "result", "items"):
            if key in data and isinstance(data[key], list):
                groups = data[key]
                break

    if not groups:
        return {"ok": False, "not_found": True}

    if len(groups) > 1:
        candidates = []
        for g in groups:
            cid = _extract_id(g, ["openConversationId", "conversationId", "id"])
            gname = g.get("name", g.get("title", ""))
            candidates.append({"conversationId": cid, "name": gname})
        return {"ok": False, "ambiguous": True, "candidates": candidates}

    group = groups[0]
    conv_id = _extract_id(
        group, ["openConversationId", "conversationId", "id"]
    )
    actual_name = group.get("name", group.get("title", group_name))

    # 展开成员（支持分页）
    all_members = []
    cursor = "0"
    while True:
        members_result = list_group_members(conv_id, cursor)
        if not members_result.get("ok"):
            break
        members_data = members_result.get("data", {})
        page_members = []
        if isinstance(members_data, list):
            page_members = members_data
        else:
            for key in ("members", "memberList", "list", "result"):
                if key in members_data and isinstance(members_data[key], list):
                    page_members = members_data[key]
                    break

        for m in page_members:
            uid = _extract_id(m, ["userId", "userid", "uid", "id"])
            uname = m.get("name", m.get("nick", m.get("nickName", "")))
            if uid:
                all_members.append({"userId": uid, "name": uname})

        # 检查是否有下一页
        has_more = members_data.get("hasMore", False) if isinstance(members_data, dict) else False
        next_cursor = members_data.get("nextCursor", "") if isinstance(members_data, dict) else ""
        if has_more and next_cursor:
            cursor = str(next_cursor)
        else:
            break

    return {
        "ok": True,
        "users": all_members,
        "group_name": actual_name,
        "conversation_id": conv_id,
    }


def resolve_all(
    participants: List[Dict[str, str]],
    include_self: bool = True,
) -> Dict[str, Any]:
    """批量解析所有参会人，合并去重。

    Args:
        participants: [{"type": "user"|"department"|"group", "name": "..."}]
        include_self: 是否自动包含当前用户

    Returns:
        {
            "ok": True,
            "users": [{"userId": ..., "name": ..., "source": ...}],
            "ambiguous": [...],
            "not_found": [...],
            "warnings": [...]
        }
    """
    all_users: Dict[str, Dict[str, Any]] = {}  # userId → info
    ambiguous: List[Dict[str, Any]] = []
    not_found: List[str] = []
    warnings: List[str] = []

    for p in participants:
        p_type = p.get("type", "user")
        p_name = p.get("name", "")

        if p_type == "user":
            result = resolve_user(p_name)
            if result.get("ok"):
                for u in result["users"]:
                    uid = u["userId"]
                    if uid not in all_users:
                        all_users[uid] = {
                            "userId": uid,
                            "name": u["name"],
                            "source": f"user:{p_name}",
                        }
            elif result.get("ambiguous"):
                ambiguous.append({
                    "type": "user",
                    "name": p_name,
                    "candidates": result["candidates"],
                })
            else:
                not_found.append(p_name)

        elif p_type == "department":
            result = resolve_department(p_name)
            if result.get("ok"):
                dept_name = result.get("dept_name", p_name)
                member_count = len(result["users"])
                if member_count > LARGE_GROUP_THRESHOLD:
                    warnings.append(
                        f"部门'{dept_name}'有 {member_count} 人，已全部展开"
                    )
                for u in result["users"]:
                    uid = u["userId"]
                    if uid not in all_users:
                        all_users[uid] = {
                            "userId": uid,
                            "name": u["name"],
                            "source": f"dept:{dept_name}",
                        }
            elif result.get("ambiguous"):
                ambiguous.append({
                    "type": "department",
                    "name": p_name,
                    "candidates": result["candidates"],
                })
            else:
                not_found.append(f"部门:{p_name}")

        elif p_type == "group":
            result = resolve_group(p_name)
            if result.get("ok"):
                group_name = result.get("group_name", p_name)
                member_count = len(result["users"])
                if member_count > LARGE_GROUP_THRESHOLD:
                    warnings.append(
                        f"群'{group_name}'有 {member_count} 人，已全部展开"
                    )
                for u in result["users"]:
                    uid = u["userId"]
                    if uid not in all_users:
                        all_users[uid] = {
                            "userId": uid,
                            "name": u["name"],
                            "source": f"group:{group_name}",
                        }
            elif result.get("ambiguous"):
                ambiguous.append({
                    "type": "group",
                    "name": p_name,
                    "candidates": result["candidates"],
                })
            else:
                not_found.append(f"群:{p_name}")

    # 自动包含当前用户
    if include_self:
        self_result = get_self()
        if self_result.get("ok"):
            self_data = self_result.get("data", {})
            self_uid = _extract_id(self_data, ["userId", "userid", "uid", "id"])
            self_name = self_data.get("name", self_data.get("nick", "我"))
            if self_uid and self_uid not in all_users:
                all_users[self_uid] = {
                    "userId": self_uid,
                    "name": self_name,
                    "source": "self",
                }

    return {
        "ok": len(all_users) > 0,
        "users": list(all_users.values()),
        "ambiguous": ambiguous,
        "not_found": not_found,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="参会人解析")
    parser.add_argument("--input", required=True, help="输入 JSON 字符串")
    parser.add_argument(
        "--include-self",
        action="store_true",
        default=True,
        help="自动包含当前用户",
    )
    args = parser.parse_args()

    try:
        input_data = json.loads(args.input)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    participants = input_data.get("participants", [])
    result = resolve_all(participants, include_self=args.include_self)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
