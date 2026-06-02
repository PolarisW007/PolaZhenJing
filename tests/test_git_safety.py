import subprocess

from git_safety import GitSafetyError, guarded_commit_and_push, split_stage_candidates


def run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return result


def init_repo(tmp_path):
    run(["git", "init"], tmp_path)
    run(["git", "config", "user.email", "test@example.com"], tmp_path)
    run(["git", "config", "user.name", "Test User"], tmp_path)
    return tmp_path


def test_split_stage_candidates_allows_articles_and_denies_env(tmp_path):
    repo = init_repo(tmp_path)
    posts = repo / "_posts"
    posts.mkdir()
    (posts / "2026-06-02-safe.md").write_text("# safe\n", encoding="utf-8")
    (repo / ".env").write_text("SECRET_TOKEN=should-not-stage\n", encoding="utf-8")

    allowed, denied = split_stage_candidates(repo)

    assert allowed == ["_posts/2026-06-02-safe.md"]
    assert ".env" in denied


def test_guarded_commit_blocks_when_denied_paths_exist(tmp_path):
    repo = init_repo(tmp_path)
    (repo / "_posts").mkdir()
    (repo / "_posts" / "2026-06-02-safe.md").write_text("# safe\n", encoding="utf-8")
    (repo / "debug-backup.txt").write_text("temporary\n", encoding="utf-8")

    try:
        guarded_commit_and_push(repo, "test", push=False)
    except GitSafetyError as exc:
        assert "debug-backup.txt" in str(exc)
    else:
        raise AssertionError("expected GitSafetyError")


def test_guarded_commit_stages_only_allowed_files(tmp_path):
    repo = init_repo(tmp_path)
    (repo / "_posts").mkdir()
    (repo / "_posts" / "2026-06-02-safe.md").write_text("# safe\n", encoding="utf-8")

    result = guarded_commit_and_push(repo, "test article", push=False)

    assert result.committed is True
    assert result.allowed == ["_posts/2026-06-02-safe.md"]
    log = run(["git", "log", "--oneline"], repo).stdout
    assert "test article" in log
