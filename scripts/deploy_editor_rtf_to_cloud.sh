#!/usr/bin/env bash
# =============================================================================
#  PolaZhenjing 云端部署脚本:文章编辑页 TinyMCE + 上传页稳定性 + skillhub 守卫
#  目标 5 commit: 296e6f9..360deb3(本地 / 远端 origin/main 已同步到 360deb3)
#  服务:    /PolaZhenjing  (Flask 后端)
#  进程:    polazj.service
#  备份:    /opt/backups/polazj-editor-rtf-<timestamp>/
#  回滚:    见末尾 ROLLBACK 段
# =============================================================================
set -euo pipefail

SERVICE_NAME=polazj
APP_DIR=/PolaZhenjing
BACKUP_ROOT=/opt/backups
TARGET_HEAD=360deb3   # 本次部署到的 commit
ROLLBACK_HEAD=ee4c10b # 上一稳定 commit

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
say()  { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "请用 sudo 或 root 执行该脚本。"

# ---------- 0. pre-release ----------
say "step 0  pre-release 检查"
[[ -d "$APP_DIR" ]] || die "$APP_DIR 不存在,请确认挂载点。"
cd "$APP_DIR"

say "  服务状态 (期望 active):"
systemctl is-active "$SERVICE_NAME" || warn "  当前服务非 active,仍继续,但后续 restart 会短时中断。"

say "  当前 HEAD:"
git rev-parse --short HEAD
git log --oneline -3

say "  远端 origin/main 是否包含目标 $TARGET_HEAD:"
git fetch origin main --quiet
if git merge-base --is-ancestor "$TARGET_HEAD" origin/main; then
  say "  远端 origin/main 已包含 $TARGET_HEAD,可 fast-forward。"
else
  die "  远端 origin/main 还没到 $TARGET_HEAD,先在本地推完再部署。"
fi

# ---------- 1. 备份 ----------
say "step 1  备份当前 /PolaZhenjing/templates + uploader.py + tests/ + docs/"
TS=$(date +%Y%m%d%H%M%S)
BACKUP_DIR=$BACKUP_ROOT/polazj-editor-rtf-$TS
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/app-templates.tgz"   -C "$APP_DIR" app/templates app/uploader.py
tar -czf "$BACKUP_DIR/tests.tgz"          -C "$APP_DIR" tests
tar -czf "$BACKUP_DIR/docs-snapshot.tgz"  -C "$APP_DIR" docs/pola/project-knowledge
cp "$APP_DIR/.env" "$BACKUP_DIR/env-backup" 2>/dev/null || warn "  .env 不存在,跳过。"
say "  备份完成: $BACKUP_DIR"
echo "$BACKUP_DIR" > /tmp/polazj_editor_rtf_last_backup

# ---------- 2. 拉代码 ----------
say "step 2  git pull --ff-only 到 $TARGET_HEAD"
git pull --ff-only origin main
NEW_HEAD=$(git rev-parse --short HEAD)
[[ "$NEW_HEAD" == "$TARGET_HEAD" ]] || die "  pull 后 HEAD=$NEW_HEAD,不是预期的 $TARGET_HEAD,中止!"
say "  现在 HEAD: $NEW_HEAD"
git log --oneline -5

# ---------- 3. 语法/测试门禁 ----------
say "step 3  py_compile + pytest"
.venv/bin/python3 -m py_compile \
  app/uploader.py app/__init__.py app/auth.py app/jobs.py app/skillhub.py app/agent.py \
  || die "  py_compile 失败,不重启服务。"

PYTHONPATH=. .venv/bin/pytest tests -q 2>&1 | tail -5
TESTS_LINE=$(PYTHONPATH=. .venv/bin/pytest tests -q 2>&1 | tail -2 | head -1)
say "  pytest 摘要: $TESTS_LINE"

# ---------- 4. 重启服务 ----------
say "step 4  systemctl restart $SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
sleep 2
STATE=$(systemctl is-active "$SERVICE_NAME")
[[ "$STATE" == "active" ]] || die "  服务未进入 active,回滚!"
say "  服务状态: $STATE"

say "  启动日志(最近 30 行):"
journalctl -u "$SERVICE_NAME" -n 30 --no-pager | tail -30 || true

# ---------- 5. 线上 smoke ----------
say "step 5  线上 HTTP smoke"
BASE="https://aipd.me${APP_DIR}"

check_code() {
  local url=$1 want=$2 label=$3
  local code
  code=$(curl -sS -o /dev/null -w "%{http_code}" "$url" || echo "ERR")
  if [[ "$code" == "$want" ]]; then
    say "  [$label] $code ✓"
  else
    warn "  [$label] $code (期望 $want)"
  fi
}

check_code "$BASE/assets/vendor/tinymce/tinymce-manifest.json"     200  "tinymce manifest"
check_code "$BASE/assets/vendor/tinymce/tinymce.min.js"            200  "tinymce main"
check_code "$BASE/assets/vendor/tinymce/langs/zh-Hans.js"          200  "tinymce zh-Hans"
check_code "$BASE/admin/login"                                     200  "admin login (未登录 200 OK)"
check_code "$BASE/admin/upload"                                    302  "admin upload (未登录 302 → login)"

say "  Flask test client 验证 article_edit 不再含 easymde、已含本地 TinyMCE + 模式切换"
.venv/bin/python3 - <<'PY'
import os
os.environ['ALLOW_FAKE_LOGIN'] = '1'
from app import create_app
app = create_app()
app.config['TESTING'] = True
with app.test_client() as c:
    with c.session_transaction() as s:
        s['user_id'] = 1; s['role'] = 'admin'
    r = c.get('/admin/articles/2026-04-11-test-article.md/edit')
    body = r.get_data(as_text=True)
    print('  status', r.status_code)
    for kw in ['easymde',
               'tinymce.min.js?v=6.8.5-pzj-20260602',
               'cache_suffix: TINYMCE_CACHE_SUFFIX',
               'editor_mode', 'rich-content', 'content-format']:
        flag = '✓' if kw in body else '✗'
        print(f'    {flag} {kw}')
PY

# ---------- done ----------
echo
say "=========================================================="
say "  部署完成 ✅"
say "  HEAD:        $NEW_HEAD"
say "  备份目录:    $BACKUP_DIR"
say "  服务状态:    $STATE"
say "  pytest:      $TESTS_LINE"
say "=========================================================="
echo
say "  接下来: 把发布摘要回填到"
say "    docs/pola/project-knowledge/release/2026-06-08-article-edit-rich-editor-deploy.md"
echo
say "  ROLLBACK 段(需要时手动执行):"
cat <<ROLLBACK

  # 全量回滚到 $ROLLBACK_HEAD
  cd $APP_DIR
  git reset --hard $ROLLBACK_HEAD
  systemctl restart $SERVICE_NAME
  systemctl is-active $SERVICE_NAME

  # 仅回滚代码(保留新 docs),从备份恢复 templates + uploader + tests
  tar -xzf $BACKUP_DIR/app-templates.tgz -C $APP_DIR
  tar -xzf $BACKUP_DIR/tests.tgz         -C $APP_DIR
  systemctl restart $SERVICE_NAME
ROLLBACK
