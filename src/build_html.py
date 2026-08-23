#!/usr/bin/env python3
"""Inline the design system, effects, app code and question bank into one
self-contained HTML file. No network fetches at runtime beyond the optional
Google Fonts import, which falls back to system serif/sans stacks offline.

    python3 src/build_html.py
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SKILL = pathlib.Path("/Users/user/.claude/skills/interface/assets")

PARTS = {
    "/*__DESIGN_SYSTEM__*/": SKILL / "design-system.css",
    "/*__APP_CSS__*/":       HERE / "app.css",
    "/*__EFFECTS__*/":       SKILL / "effects.js",
    "/*__APP_JS__*/":        HERE / "app.js",
    "/*__BANK__*/":          HERE / "bank.json",
}

# index.html, not mcpa-trainer.html: every static host (Vercel, Netlify, GitHub
# Pages, S3, `python3 -m http.server`) serves index.html for a bare "/" and 404s
# when it is absent. Naming the deliverable anything else means the deployed root
# is broken even though the file is sitting right there.
OUT = ROOT / "index.html"

def main():
    html = (HERE / "index.template.html").read_text()
    for token, path in PARTS.items():
        if not path.exists():
            sys.exit(f"FATAL: missing {path}")
        if token not in html:
            sys.exit(f"FATAL: template has no {token} placeholder")
        html = html.replace(token, path.read_text().strip())

    OUT.write_text(html)
    print(f"  wrote {OUT.name} — {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
