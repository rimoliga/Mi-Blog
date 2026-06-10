#!/usr/bin/env python3
"""
Converts vault/posts/ Obsidian notes to content/posts/ Hugo pages.
Only notes with publish: true in frontmatter are processed.
Copies attachments from vault/adjuntos/ to static/img/.
"""

import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime

VAULT_POSTS = "vault/posts"
VAULT_ATTACHMENTS = "vault/adjuntos"
CONTENT_POSTS = "content/posts"
STATIC_IMG = "static/img"


def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^\w-]", "", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def parse_frontmatter(content, filepath):
    """Return (dict, body_str). Raises ValueError on malformed frontmatter."""
    if not content.startswith("---"):
        return {}, content

    end = content.find("\n---", 3)
    if end == -1:
        raise ValueError(f"Frontmatter block never closed in {filepath}")

    fm_text = content[3:end].strip()
    body = content[end + 4:].lstrip("\n")

    fm = {}
    for lineno, line in enumerate(fm_text.splitlines(), 1):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(
                f"Malformed frontmatter line {lineno} in {filepath}: {line!r}"
            )
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.lower() == "true":
            fm[key] = True
        elif value.lower() == "false":
            fm[key] = False
        elif (value.startswith('"') and value.endswith('"')) or \
             (value.startswith("'") and value.endswith("'")):
            fm[key] = value[1:-1]
        else:
            fm[key] = value

    return fm, body


def collect_publishable(vault_dir):
    """
    Walk vault_dir and return:
      - publishable: {stem: {path, fm, body, slug}}
      - errors: [str]
    """
    publishable = {}
    errors = []

    for root, _dirs, files in os.walk(vault_dir):
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
            except OSError as exc:
                errors.append(f"Cannot read {fpath}: {exc}")
                continue

            try:
                fm, body = parse_frontmatter(content, fpath)
            except ValueError as exc:
                errors.append(str(exc))
                continue

            if fm.get("publish") is not True:
                continue

            stem = os.path.splitext(fname)[0]
            title = fm.get("title") or stem
            date_val = fm.get("date") or datetime.fromtimestamp(
                os.path.getmtime(fpath)
            ).strftime("%Y-%m-%d")

            publishable[stem] = {
                "path": fpath,
                "fm": {**fm, "title": title, "date": str(date_val), "draft": False},
                "body": body,
                "slug": slugify(title),
            }

    return publishable, errors


def convert_wikilinks(body, publishable_stems, stem_to_slug):
    def replace(m):
        inner = m.group(1)
        target, sep, text = inner.partition("|")
        target = target.strip()
        text = (text if sep else target).strip()
        if target in publishable_stems:
            return f"[{text}](/posts/{stem_to_slug[target]}/)"
        return text

    return re.sub(r"\[\[([^\]]+)\]\]", replace, body)


def convert_attachments(body, vault_attachments_dir, static_img_dir):
    def replace(m):
        inner = m.group(1)
        fname = os.path.basename(inner)
        candidates = [
            os.path.join(vault_attachments_dir, inner),
            os.path.join(vault_attachments_dir, fname),
        ]
        for src in candidates:
            if os.path.isfile(src):
                os.makedirs(static_img_dir, exist_ok=True)
                shutil.copy2(src, os.path.join(static_img_dir, fname))
                break
        return f"![](/img/{fname})"

    return re.sub(r"!\[\[([^\]]+)\]\]", replace, body)


def clean_obsidian_syntax(body):
    # Remove %%comments%%
    body = re.sub(r"%%.*?%%", "", body, flags=re.DOTALL)
    # Remove dataview blocks
    body = re.sub(r"```dataview\b.*?```", "", body, flags=re.DOTALL | re.IGNORECASE)
    # Convert callouts > [!type] to plain blockquotes
    body = re.sub(r"^(> )\[![^\]]+\] ?", r"\1", body, flags=re.MULTILINE)
    return body


def build_frontmatter(fm):
    def fmt(val):
        if isinstance(val, bool):
            return str(val).lower()
        s = str(val)
        if any(c in s for c in (':', '#', '[', ']', '{', '}')):
            return f'"{s}"'
        return s

    skip = {"publish"}
    priority = ["title", "date", "draft"]
    lines = ["---"]
    for key in priority:
        if key in fm:
            lines.append(f"{key}: {fmt(fm[key])}")
    for key, val in fm.items():
        if key not in skip and key not in priority:
            lines.append(f"{key}: {fmt(val)}")
    lines.append("---")
    return "\n".join(lines)


def main():
    publishable, errors = collect_publishable(VAULT_POSTS)

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    stem_to_slug = {stem: info["slug"] for stem, info in publishable.items()}

    if os.path.exists(CONTENT_POSTS):
        shutil.rmtree(CONTENT_POSTS)
    os.makedirs(CONTENT_POSTS, exist_ok=True)

    for stem, info in publishable.items():
        body = clean_obsidian_syntax(info["body"])
        # Attachments must run before wikilinks: ![[file]] vs [[note]]
        body = convert_attachments(body, VAULT_ATTACHMENTS, STATIC_IMG)
        body = convert_wikilinks(body, set(publishable), stem_to_slug)

        out_path = os.path.join(CONTENT_POSTS, info["slug"] + ".md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(build_frontmatter(info["fm"]) + "\n\n" + body.strip() + "\n")

        print(f"  {stem!r} → {info['slug']}.md")

    print(f"obsidian_to_hugo: {len(publishable)} nota(s) publicada(s).")


if __name__ == "__main__":
    main()
