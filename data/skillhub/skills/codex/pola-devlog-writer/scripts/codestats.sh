#!/usr/bin/env bash
# pola-devlog-writer · 代码统计一键脚本
# 用法：
#   bash codestats.sh [src_dir] [scripts_dir]
#   默认 src_dir = app/src，scripts_dir = app/scripts
# 输出：
#   1) 代码快照（按扩展名）
#   2) 代码快照（按目录）
#   3) 阶段增量（按 commit 日期分组）
#   4) 总计
set -uo pipefail

SRC="${1:-app/src}"
SCRIPTS="${2:-app/scripts}"

ROOTS=()
[ -d "$SRC" ] && ROOTS+=("$SRC")
[ -d "$SCRIPTS" ] && ROOTS+=("$SCRIPTS")

if [ "${#ROOTS[@]}" -eq 0 ]; then
  echo "[错误] 源码目录均不存在：$SRC / $SCRIPTS" >&2
  echo "       请通过参数指定，例如：bash codestats.sh src ." >&2
  exit 1
fi

echo "=== 代码快照（按扩展名）==="
for ext in ts tsx js jsx vue py go rs java rb php cs swift kt css scss sh; do
  files=$(find "${ROOTS[@]}" -type f -name "*.$ext" 2>/dev/null | wc -l | tr -d ' ')
  if [ "${files:-0}" -gt 0 ]; then
    lines=$(find "${ROOTS[@]}" -type f -name "*.$ext" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1+0}')
    printf "%-6s %4d files, %6d lines\n" "$ext:" "$files" "${lines:-0}"
  fi
done

echo
echo "=== 代码快照（按目录）==="
DIRS=("$SRC/app" "$SRC/lib" "$SRC/components" "$SRC/pages" "$SRC/services" "$SRC/utils" "$SRC/hooks" "$SCRIPTS")
for dir in "${DIRS[@]}"; do
  [ -d "$dir" ] || continue
  files=$(find "$dir" -type f \( \
      -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
      -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.java" \
      -o -name "*.css" -o -name "*.scss" -o -name "*.vue" \
    \) 2>/dev/null | wc -l | tr -d ' ')
  lines=$(find "$dir" -type f \( \
      -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
      -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.java" \
      -o -name "*.css" -o -name "*.scss" -o -name "*.vue" \
    \) 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1+0}')
  if [ "${files:-0}" -gt 0 ]; then
    printf "%-40s %4d files, %6d lines\n" "$dir" "$files" "${lines:-0}"
  fi
done

echo
echo "=== 阶段增量（按日期分组）==="
if git rev-parse --git-dir >/dev/null 2>&1; then
  git log --pretty=tformat:'BOUNDARY %h %ad' --date=short --shortstat --no-merges \
    | awk '/^BOUNDARY/{date=$3;next}
           /file.*changed/{a=0;d=0;f=0;
             for(i=1;i<=NF;i++){if($i~/insertion/)a=$(i-1);
               else if($i~/deletion/)d=$(i-1);
               else if($i~/file/)f=$(i-1)}
             A[date]+=a;D[date]+=d;F[date]+=f;C[date]++}
           END{for(d in C) printf "%s: %d commits, %d files, +%d/-%d\n",d,C[d],F[d],A[d],D[d]}' \
    | sort
else
  echo "[跳过] 当前目录不是 git 仓库"
fi

echo
echo "=== 总计 ==="
if git rev-parse --git-dir >/dev/null 2>&1; then
  git log --pretty=tformat:'%h' --shortstat --no-merges \
    | awk '/file.*changed/{a=0;d=0;f=0;
             for(i=1;i<=NF;i++){if($i~/insertion/)a=$(i-1);
               else if($i~/deletion/)d=$(i-1);
               else if($i~/file/)f=$(i-1)}
             TA+=a;TD+=d;TF+=f;TC++}
           END{printf "%d commits, %d files, +%d/-%d, 净 +%d\n",TC,TF,TA,TD,TA-TD}'
else
  echo "[跳过] 当前目录不是 git 仓库"
fi
