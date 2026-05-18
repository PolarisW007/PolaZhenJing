#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
千里眼 v3 —— 悟空平台入口适配器。

悟空平台通过 `python run.py [args]` 调用技能。
本文件确保 scripts/ 在 sys.path 中，然后调用 fetch_and_save.main()。
v3 升级：时间段全群检索 + 群链接生成 + JSON 结构化输出。
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from fetch_and_save import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
