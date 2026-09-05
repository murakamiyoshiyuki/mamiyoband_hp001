from pathlib import Path
import re
import shutil
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pages_cms_exposes_guarded_updates_only():
    config = yaml.safe_load(read(".pages.yml"))
    assert config["media"][0]["input"] == "素材/CMS"
    assert config["media"][0]["extensions"] == ["jpg", "jpeg", "png", "webp"]
    assert (ROOT / "素材" / "CMS").is_dir()
    updates = next(item for item in config["content"] if item["name"] == "updates")
    assert updates["path"] == "_updates"
    assert (ROOT / "_updates").is_dir()
    assert updates["operations"] == {"create": True, "rename": False, "delete": False}
    fields = {field["name"]: field for field in updates["fields"]}
    for required in (
        "title",
        "published_date",
        "category",
        "show_in_news",
        "show_in_live",
        "event_date",
        "summary",
        "image",
        "image_alt",
        "body",
    ):
        assert required in fields
    assert fields["title"]["required"] is True
    assert fields["published_date"]["required"] is True
    assert fields["body"]["required"] is True
    assert fields["body"]["options"]["extensions"] == ["jpg", "jpeg", "png", "webp"]


def test_jekyll_outputs_managed_updates_at_stable_root_urls():
    config = yaml.safe_load(read("_config.yml"))
    assert config["collections"]["updates"]["output"] is True
    assert config["collections"]["updates"]["permalink"] == "/:name.html"
    defaults = config["defaults"]
    assert any(
        item.get("scope", {}).get("type") == "updates"
        and item.get("values", {}).get("layout") == "update"
        for item in defaults
    )


def test_homepage_renders_managed_news_and_live_before_legacy_items():
    index = read("index.html")
    assert index.startswith("---\n---\n")
    assert "site.updates | where: \"show_in_news\", true" in index
    assert "site.updates | where: \"show_in_live\", true" in index
    assert 'item.published_date | date: "%Y.%m.%d"' in index
    assert 'item.event_date | date: "%Y.%m.%d"' in index
    assert index.index("cms-news-start") < index.index("news-tour-2026-2027.html")
    assert index.index("cms-live-start") < index.index("live-20261018.html")


def test_managed_layout_has_metadata_backlink_and_safe_plain_text_fields():
    layout = read("_layouts/update.html")
    assert "<meta property=\"og:title\"" in layout
    assert "index.html#news" in layout
    assert "index.html#live-info" in layout
    assert "assign has_event_info = false" in layout
    assert 'page.event_date | date: "%Y.%m.%d"' in layout
    assert 'page.published_date | date: "%Y.%m.%d"' in layout
    for field in ("event_date", "venue", "performers", "open_start", "price"):
        assert f"page.{field} and page.{field} != \"\"" in layout
    for field in ("page.title", "page.summary", "page.image_alt", "page.venue"):
        assert re.search(r"{{\s*" + re.escape(field) + r"\s*\|\s*escape\s*}}", layout)
    assert "{{ content }}" in layout


def test_staff_handoff_defines_same_write_path_and_verification_gate():
    agents = read("docs/Hermes編集ルール.md")
    guide = read("docs/スタッフ更新ガイド.md")
    validator = ROOT / "scripts" / "validate_site.py"
    assert "git pull --ff-only" in agents
    assert "python3 scripts/validate_site.py" in agents
    assert "GitHub Pages" in agents
    assert "WRITE権限" in guide
    assert "authenticated-browser-workflow" in guide
    assert "パスワードや認証コードはHermesへ送らない" in guide
    assert "https://github.com/murakamiyoshiyuki/mamiyoband_hp001" in guide
    assert "画像管理画面では画像の名前変更・削除ができます" in guide
    assert "Pages CMSの管理画面からメール招待も停止" in guide
    assert validator.is_file()


def test_github_runs_the_same_validation_automatically():
    workflow = read(".github/workflows/validate-staff-updates.yml")
    requirements = read("requirements-dev.txt")
    assert "python -m pytest -q" in workflow
    assert "python scripts/validate_site.py" in workflow
    assert "jekyll build" in workflow
    assert "requirements-dev.txt" in workflow
    assert "cache-dependency-path: requirements-dev.txt" in workflow
    assert "actions/checkout@v7" in workflow
    assert "actions/setup-python@v7" in workflow
    assert "PyYAML==" in requirements
    assert "pytest==" in requirements


def test_validator_accepts_the_existing_site_and_ignores_runtime_templates():
    result = subprocess.run(
        [sys.executable, "scripts/validate_site.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


def test_validator_rejects_invalid_or_unsafe_cms_content(tmp_path):
    shutil.copy(ROOT / ".pages.yml", tmp_path / ".pages.yml")
    shutil.copy(ROOT / "_config.yml", tmp_path / "_config.yml")
    (tmp_path / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "validate_site.py", tmp_path / "scripts" / "validate_site.py")
    (tmp_path / "_updates").mkdir()
    (tmp_path / "素材" / "CMS").mkdir(parents=True)
    (tmp_path / "_updates" / "unsafe.md").write_text(
        """---
title: 危険な投稿
published_date: "2026-02-30"
category: OTHER
show_in_news: "true"
show_in_live: true
event_date: "2026-02-30"
live_type: OTHER
summary: 検品
image: /素材/CMS/../secret.jpg
image_alt: 画像
ticket_url: "https://example.com/ bad"
---
<script>alert(1)</script>
{% include secret.html %}
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "scripts/validate_site.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    for problem in (
        "published_dateは実在する日付",
        "categoryはINFO/LIVE/RELEASE/MEDIAのいずれか",
        "show_in_newsはtrue/false",
        "event_dateは実在する日付",
        "live_typeはBAND/ACOUSTICのいずれか",
        "ticket_urlが不正",
        "imageは/素材/CMS/配下",
        "本文に使用できない記述",
    ):
        assert problem in result.stdout


def test_validator_rejects_html_entity_obfuscated_javascript_link(tmp_path):
    shutil.copy(ROOT / ".pages.yml", tmp_path / ".pages.yml")
    shutil.copy(ROOT / "_config.yml", tmp_path / "_config.yml")
    (tmp_path / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "validate_site.py", tmp_path / "scripts" / "validate_site.py")
    (tmp_path / "_updates").mkdir()
    (tmp_path / "素材" / "CMS").mkdir(parents=True)
    (tmp_path / "_updates" / "obfuscated-link.md").write_text(
        """---
title: 検証用のお知らせ
published_date: "2026-09-01"
category: INFO
show_in_news: true
show_in_live: false
event_date: ""
live_type: BAND
summary: 検証用の投稿です
image: ""
image_alt: 画像なし
ticket_url: ""
---
<a href="java&#x73;cript:alert(document.domain)">検証リンク</a>
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "scripts/validate_site.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "本文に使用できない記述" in result.stdout


def test_validator_rejects_control_character_obfuscated_markdown_link(tmp_path):
    shutil.copy(ROOT / ".pages.yml", tmp_path / ".pages.yml")
    shutil.copy(ROOT / "_config.yml", tmp_path / "_config.yml")
    (tmp_path / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "validate_site.py", tmp_path / "scripts" / "validate_site.py")
    (tmp_path / "_updates").mkdir()
    (tmp_path / "素材" / "CMS").mkdir(parents=True)
    (tmp_path / "_updates" / "obfuscated-markdown.md").write_text(
        """---
title: 検証用のお知らせ
published_date: "2026-09-01"
category: INFO
show_in_news: true
show_in_live: false
event_date: ""
live_type: BAND
summary: 検証用の投稿です
image: ""
image_alt: 画像なし
ticket_url: ""
---
[検証リンク](java&#x09;&#x73;cript:alert(document.domain))
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "scripts/validate_site.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "本文に使用できない記述" in result.stdout
