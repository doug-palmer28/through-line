"""Build the two files submitted on Canvas: deliverables/report.html and deliverables/slides.html.

    .venv/Scripts/python scripts/build_deliverables.py --access-code <the live site's sign-up code>
    .venv/Scripts/python scripts/build_deliverables.py --access-code <code> --demo "keystone.demo:<password>"

Sources live in the repo (docs/report/index.html, docs/slides/index.html, images in docs/report/img/).
The built files are self-contained: every image is embedded, so they open by double-clicking on any
computer. The access code is filled in only here, and deliverables/ is git-ignored, so the code is
never published in the public repo.
"""

import argparse
import base64
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "deliverables"


def inline_images(html: str, base: Path) -> str:
    def data_uri(match: re.Match) -> str:
        src = match.group(2)
        if src.startswith(("data:", "http:", "https:")):
            return match.group(0)
        path = (base / src).resolve()
        if not path.is_file():
            raise SystemExit(f"Missing image: {path}")
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        return f'{match.group(1)}"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"'

    return re.sub(r'(<img\b[^>]*?\bsrc=)"([^"]+)"', data_uri, html)


def new_tab_links(html: str) -> str:
    """Web links open in a new tab, so the report or deck stays open; in-page links (#r13) don't."""
    return re.sub(r'<a (?![^>]*\btarget=)([^>]*\bhref="https?://)', r'<a target="_blank" rel="noopener" \1', html)


def fill(html: str, code: str, demo: str | None, slide: bool) -> str:
    html = html.replace("{{ACCESS_CODE}}", code)
    if demo:
        user, _, password = demo.partition(":")
        size = "font-size:25px;" if slide else ""
        line = (f'<p class="small" style="{size}margin:6px 0 0"><b style="font-weight:700">Want to see a finished example right away?</b> Sign in as '
                f'<span class="code">{user}</span> with password <span class="code">{password}</span>: Keystone Family '
                "Housing Partners, with the logic model, surveys, dashboard, report, and grant draft already built.</p>")
        html = html.replace("<!--DEMO-->", line)
    else:
        html = html.replace("<!--DEMO-->", "")
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftover:
        raise SystemExit(f"Unfilled placeholders: {leftover}")
    return html


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--access-code", required=True, help="the live site's sign-up access code")
    ap.add_argument("--demo", default=None, help='optional ready-made login, as "username:password"')
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    report_src = (DOCS / "report" / "index.html").read_text(encoding="utf-8")
    report = new_tab_links(fill(inline_images(report_src, DOCS / "report"), args.access_code, args.demo, slide=False))
    (OUT / "report.html").write_text(report, encoding="utf-8")

    svg = re.search(r"<svg\b.*?</svg>", report_src, re.S)
    slides_src = (DOCS / "slides" / "index.html").read_text(encoding="utf-8")
    slides_src = slides_src.replace("<!--AGENT_SVG-->", svg.group(0) if svg else "")
    slides = new_tab_links(fill(inline_images(slides_src, DOCS / "slides"), args.access_code, args.demo, slide=True))
    (OUT / "slides.html").write_text(slides, encoding="utf-8")

    for name in ("report.html", "slides.html"):
        size = (OUT / name).stat().st_size / 1_048_576
        print(f"deliverables/{name}: {size:.1f} MB, self-contained")


if __name__ == "__main__":
    main()
