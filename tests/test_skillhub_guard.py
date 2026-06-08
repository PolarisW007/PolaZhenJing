import zipfile

import pytest

from app import skillhub


def test_safe_extract_rejects_too_many_files(tmp_path, monkeypatch):
    monkeypatch.setattr(skillhub, "SKILLHUB_MAX_ZIP_FILES", 1)
    zip_path = tmp_path / "skills.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("a/SKILL.md", "---\nname: a\n---\n")
        archive.writestr("b/SKILL.md", "---\nname: b\n---\n")

    with pytest.raises(ValueError, match="文件数量过多"):
        skillhub._safe_extract_zip(zip_path, tmp_path / "out")


def test_safe_extract_rejects_extracted_size(tmp_path, monkeypatch):
    monkeypatch.setattr(skillhub, "SKILLHUB_MAX_EXTRACTED_BYTES", 4)
    zip_path = tmp_path / "skills.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("a/SKILL.md", "12345")

    with pytest.raises(ValueError, match="解压后过大"):
        skillhub._safe_extract_zip(zip_path, tmp_path / "out")
