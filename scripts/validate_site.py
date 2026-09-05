#!/usr/bin/env python3
"""Validate CMS content and local references before publishing."""

from __future__ import annotations

import html
import re
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
ATTR = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
UNSAFE_BODY = re.compile(
    r"(?:\{\{|\{%|<\s*/?\s*[a-z][^>]*>|<\s*!|"
    r"javascript\s*:|data\s*:\s*text/html|on[a-z]+\s*=)",
    re.IGNORECASE,
)
REQUIRED = ("title", "published_date", "category", "summary", "image_alt")
CATEGORIES = {"INFO", "LIVE", "RELEASE", "MEDIA"}
LIVE_TYPES = {"BAND", "ACOUSTIC"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
TEXT_LIMITS = {"title": 120, "summary": 180, "image_alt": 180}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def valid_date(value) -> bool:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return 2000 <= value.year <= 2099
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return 2000 <= parsed.year <= 2099


def valid_https_url(value) -> bool:
    if value in (None, ""):
        return True
    if not isinstance(value, str) or any(char.isspace() for char in value):
        return False
    parts = urlsplit(value)
    return (
        parts.scheme == "https"
        and bool(parts.hostname)
        and parts.username is None
        and parts.password is None
    )


def canonical_body(body: str) -> str:
    """Decode browser-relevant encodings before unsafe-content checks."""
    value = body
    for _ in range(3):
        decoded = html.unescape(unquote(value))
        if decoded == value:
            break
        value = decoded
    return re.sub(r"[\x00-\x20\x7f]+", "", value)


def validate_config(errors: list[str]) -> None:
    for name in (".pages.yml", "_config.yml"):
        path = ROOT / name
        if not path.exists():
            errors.append(f"{name}: ファイルがありません")
            continue
        try:
            data = load_yaml(path)
            if not isinstance(data, dict):
                errors.append(f"{name}: YAMLの最上位は項目形式にしてください")
        except (yaml.YAMLError, ValueError) as exc:
            errors.append(f"{name}: YAMLまたは日付エラー: {exc}")


def validate_image(path: Path, image, errors: list[str]) -> None:
    if image in (None, ""):
        return
    if not isinstance(image, str) or not image.startswith("/素材/CMS/"):
        errors.append(f"{path.relative_to(ROOT)}: imageは/素材/CMS/配下にしてください")
        return
    media_root = (ROOT / "素材" / "CMS").resolve()
    candidate = (ROOT / unquote(image.lstrip("/"))).resolve()
    try:
        candidate.relative_to(media_root)
    except ValueError:
        errors.append(f"{path.relative_to(ROOT)}: imageは/素材/CMS/配下から出せません")
        return
    if candidate.suffix.lower() not in IMAGE_EXTENSIONS:
        errors.append(f"{path.relative_to(ROOT)}: imageの形式はjpg/jpeg/png/webpです")
    elif not candidate.is_file():
        errors.append(f"{path.relative_to(ROOT)}: 画像がありません: {image}")


def validate_updates(errors: list[str]) -> int:
    count = 0
    updates = ROOT / "_updates"
    if not updates.exists():
        return count
    for path in sorted(updates.glob("*.md")):
        count += 1
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER.match(text)
        if not match:
            errors.append(f"{path.relative_to(ROOT)}: YAML front matterがありません")
            continue
        try:
            data = yaml.safe_load(match.group(1)) or {}
        except (yaml.YAMLError, ValueError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: YAMLまたは日付エラー: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path.relative_to(ROOT)}: YAML front matterは項目形式にしてください")
            continue
        for field in REQUIRED:
            if data.get(field) in (None, ""):
                errors.append(f"{path.relative_to(ROOT)}: {field}は必須です")
        for field, limit in TEXT_LIMITS.items():
            value = data.get(field)
            if value not in (None, "") and (not isinstance(value, str) or len(value) > limit):
                errors.append(f"{path.relative_to(ROOT)}: {field}は文字列かつ{limit}文字以内です")
        if not valid_date(data.get("published_date")):
            errors.append(f"{path.relative_to(ROOT)}: published_dateは実在する日付（YYYY-MM-DD）です")
        if data.get("category") not in CATEGORIES:
            errors.append(f"{path.relative_to(ROOT)}: categoryはINFO/LIVE/RELEASE/MEDIAのいずれかです")
        for field in ("show_in_news", "show_in_live"):
            if not isinstance(data.get(field), bool):
                errors.append(f"{path.relative_to(ROOT)}: {field}はtrue/falseです")
        if not data.get("show_in_news") and not data.get("show_in_live"):
            errors.append(f"{path.relative_to(ROOT)}: NEWSかLIVE INFOを1つ以上ONにしてください")
        if data.get("show_in_live"):
            if not valid_date(data.get("event_date")):
                errors.append(f"{path.relative_to(ROOT)}: event_dateは実在する日付（YYYY-MM-DD）です")
            if data.get("live_type") not in LIVE_TYPES:
                errors.append(f"{path.relative_to(ROOT)}: live_typeはBAND/ACOUSTICのいずれかです")
        if not valid_https_url(data.get("ticket_url")):
            errors.append(f"{path.relative_to(ROOT)}: ticket_urlが不正です（https URLのみ）")
        validate_image(path, data.get("image"), errors)
        body = text[match.end():].strip()
        if not body:
            errors.append(f"{path.relative_to(ROOT)}: 本文は必須です")
        elif UNSAFE_BODY.search(canonical_body(body)):
            errors.append(f"{path.relative_to(ROOT)}: 本文に使用できない記述があります")
    return count


def validate_local_links(errors: list[str]) -> int:
    checked = 0
    for path in sorted(ROOT.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        for raw in ATTR.findall(text):
            if "{{" in raw or "{%" in raw or "${" in raw:
                continue
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc or raw.startswith(("#", "mailto:", "tel:")):
                continue
            target = unquote(parts.path)
            if not target:
                continue
            checked += 1
            candidate = ROOT / target.lstrip("/")
            if not candidate.exists():
                errors.append(f"{path.name}: リンク先がありません: {raw}")
    return checked


def main() -> int:
    errors: list[str] = []
    validate_config(errors)
    updates = validate_updates(errors)
    links = validate_local_links(errors)
    if errors:
        print("FAIL: 公開前検査で問題が見つかりました")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: CMS投稿 {updates}件 / ローカル参照 {links}件を確認")
    return 0


if __name__ == "__main__":
    sys.exit(main())
