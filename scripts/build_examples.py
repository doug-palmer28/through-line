"""Export everything Through Line made for Keystone into examples/keystone/, so anyone can open it on GitHub.

    .venv/Scripts/python scripts/build_examples.py

Keystone Family Housing Partners is fictional (synthetic data). The script loads its package
(scripts/demo/keystone_family_housing.json) into a throwaway database, signs in, and saves every
download the app offers. No AI is called: every file is rendered from the stored drafts and data.
"""

import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "scripts" / "demo" / "keystone_family_housing.json"
OUT = ROOT / "examples" / "keystone"

tmp = Path(tempfile.mkdtemp(prefix="through_line_examples_"))
os.environ.update({
    "PORTKEY_API_KEY": "",  # empty, not missing, so .env can't supply a key: offline only
    "THROUGH_LINE_DB": str(tmp / "examples.db"),
    "THROUGH_LINE_SECRET": secrets.token_hex(32),
    "THROUGH_LINE_SESSIONS": str(tmp / "sessions"),
    "THROUGH_LINE_BRAND_DIR": str(tmp / "brand"),
    "THROUGH_LINE_AUDIT": str(tmp / "audit_log.json"),
})
os.environ.pop("THROUGH_LINE_SIGNUP_CODE", None)
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from db import engine  # noqa: E402
from operator_tools import import_org  # noqa: E402


def save(client: TestClient, url: str, name: str) -> None:
    r = client.get(url)
    if r.status_code != 200:
        raise SystemExit(f"{url}: {r.status_code} {r.text[:200]}")
    (OUT / name).write_bytes(r.content)
    print(f"  {name}")


def survey_markdown(inst: dict, scales: dict, demographics: dict) -> str:
    """The survey as a participant would see it, with its answer choices."""
    when = (inst.get("when") or "").strip()
    lines = [f"# {inst['name']}", "", "A survey tool Through Line built for Keystone from its approved measurement plan.", ""]
    if when:
        lines += [f"**When and how to give it:** {when}", ""]
    lines += ["## Questions", ""]
    for n, q in enumerate(inst.get("questions") or [], 1):
        lines.append(f"{n}. **{q.get('text') or q.get('prompt') or ''}**")
        scale = scales.get(q.get("scale") or q.get("type") or "")
        if scale and scale.get("options"):
            lines.append("   " + " · ".join(str(o) for o in scale["options"]))
        elif (q.get("scale") or q.get("type")) == "open_text":
            lines.append("   *(open answer)*")
    demo = [demographics.get(d, {}).get("label", d) for d in inst.get("demographics") or []]
    if demo:
        lines += ["", "## About you (optional)", ""] + [f"- {d}" for d in demo]
        lines += ["", "Every one of these is optional, and groups smaller than 5 people are hidden in every chart."]
    return "\n".join(lines) + "\n"


def to_pdf() -> None:
    """PDF copies of the PowerPoint and Word files, so they open right in the browser on GitHub (needs Microsoft Office)."""
    ps = r"""
$ErrorActionPreference = 'Stop'
$dir = $args[0]
$ppt = New-Object -ComObject PowerPoint.Application
Get-ChildItem $dir -Filter *.pptx | ForEach-Object {
  $p = $ppt.Presentations.Open($_.FullName, $true, $false, $false)
  $p.SaveAs([IO.Path]::ChangeExtension($_.FullName, '.pdf'), 32); $p.Close() }
$ppt.Quit()
$word = New-Object -ComObject Word.Application
Get-ChildItem $dir -Filter *.docx | ForEach-Object {
  $d = $word.Documents.Open($_.FullName, $false, $true)
  $d.SaveAs([ref][IO.Path]::ChangeExtension($_.FullName, '.pdf'), [ref]17); $d.Close() }
$word.Quit()
"""
    script = Path(tmp) / "to_pdf.ps1"
    script.write_text(ps, encoding="utf-8")
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), str(OUT)],
                       check=True, capture_output=True, timeout=300)
        print("  PDF copies of the PowerPoint and Word files")
    except (OSError, subprocess.SubprocessError) as e:
        print(f"  (skipped PDF copies: {e})")


def main_() -> None:
    engine()  # creates the throwaway database
    password = secrets.token_urlsafe(16) + "A1"
    print(import_org(BUNDLE, username="examples.export", password=password, display_name="Example export"))
    c = TestClient(main.app)
    assert c.post("/api/auth/login", json={"username": "examples.export", "password": password}).status_code == 200

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.iterdir():  # empty the folder but keep it (OneDrive can lock the folder itself)
        if old.is_file() and old.name != "README.md":
            old.unlink()

    sid = json.loads(BUNDLE.read_text(encoding="utf-8"))["studio_session"]["session_id"]
    save(c, f"/api/logic-model/sessions/{sid}/export.pptx", "1_logic_model_and_metrics.pptx")

    overview = c.get("/api/tools").json()
    for i, t in enumerate(overview["instruments"], 1):
        inst = c.get(f"/api/tools/instruments/{t['id']}").json()
        name = f"2_survey_{i}.md"
        (OUT / name).write_text(survey_markdown(inst, overview["scales"], overview["demographics"]), encoding="utf-8")
        print(f"  {name}")
    save(c, "/api/tools/indicators/template.xlsx", "2_program_numbers_template.xlsx")

    save(c, "/api/dashboard/data.xlsx", "3_dashboard_all_data.xlsx")
    save(c, "/api/dashboard/report.pptx", "3_dashboard_quick_report.pptx")

    runs = c.get("/api/reports").json()["runs"]
    if runs:
        save(c, f"/api/reports/{runs[0]['id']}/deck.pptx", "4_funder_deck.pptx")
        save(c, f"/api/reports/{runs[0]['id']}/one-pager.pdf", "4_one_page_flyer.pdf")

    apps = c.get("/api/grants").json()["applications"]
    if apps:
        save(c, f"/api/grants/{apps[0]['id']}/application.docx", "5_grant_application_draft.docx")
    if sys.platform == "win32":
        to_pdf()


if __name__ == "__main__":
    try:
        main_()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
