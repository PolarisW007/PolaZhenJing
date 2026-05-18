# 🗓 智能排会助手（Wukong Meeting Assistant）

> 输入会议主题和参会人（支持 @人名/@群/@部门），自动查询所有人闲忙状态，推荐最优时间段，一键创建日程并发送邀请。

## 功能特性

- **自然语言输入**：支持「帮我找下周产品部和设计部都有空的1小时」等自然语言
- **多源参会人解析**：@人名 → userId、@部门 → 展开全部成员、@群 → 展开群成员
- **智能闲忙分析**：30 分钟粒度 slot 矩阵 + 评分排序，推荐 Top-3 最优时段
- **一站式创建**：日程创建 → 添加参会人 → 预订会议室 → 创建视频会议
- **全 dws CLI 驱动**：所有钉钉操作通过 dws CLI 完成，无额外 SDK 依赖

## 文件结构

```
wukong-meeting-assistant/
├── PRD.md                          # 产品需求文档
├── SKILL.md                        # 悟空技能描述文件
├── README.md                       # 本文件
├── requirements.txt                # 依赖说明（纯标准库）
└── scripts/
    ├── __init__.py
    ├── dws_cli.py                  # dws CLI 封装层（统一执行/JSON解析/重试）
    ├── time_utils.py               # 时间工具（ISO-8601/工作时间/slot生成）
    ├── participant_resolver.py     # 参会人解析（@人名/@部门/@群 → userId列表）
    ├── free_slot_calc.py           # 空闲窗口算法（slot矩阵/评分排序/Top-N）
    └── meeting_creator.py          # 会议创建编排（日程+加人+会议室+视频会议）
```

## 脚本说明

所有脚本均支持独立 CLI 调用，输入输出为 JSON，便于 Agent 编排。

### participant_resolver.py — 参会人解析

```bash
python scripts/participant_resolver.py --input '{
  "participants": [
    {"type": "user", "name": "福锤"},
    {"type": "department", "name": "开放平台"},
    {"type": "group", "name": "悟空核心群"}
  ]
}' --include-self
```

### free_slot_calc.py — 空闲窗口计算

```bash
python scripts/free_slot_calc.py \
  --busy '<dws calendar busy search 返回的 JSON>' \
  --start '2026-04-14T09:00:00+08:00' \
  --end '2026-04-18T18:00:00+08:00' \
  --duration 60 \
  --users '{"uid1":"张三","uid2":"李四"}' \
  --top 3
```

### meeting_creator.py — 会议创建

```bash
python scripts/meeting_creator.py \
  --title "Q2 产品复盘" \
  --start "2026-04-15T14:00:00+08:00" \
  --end "2026-04-15T15:00:00+08:00" \
  --users "uid1,uid2,uid3" \
  --user-names "王畅,枫华,先雄" \
  --need-room \
  --need-video
```

## 前置条件

- Python >= 3.9
- dws CLI 已安装并完成 `dws auth login` 认证
- 无额外第三方 Python 依赖

## 作者

王畅（福锤）— 2026-04-11
