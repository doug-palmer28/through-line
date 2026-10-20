"""Enter many survey responses at once: download an Excel template, fill it in, upload it back.

One template per survey tool and wave (pre or post). Rows are participant codes (every active
participant, with any answers already entered pre-filled); columns are that wave's questions (and the
demographic questions at pre). Rated and choice questions get dropdowns. Uploading replaces each listed
participant's form for that wave, exactly like the on-screen "Enter responses" grid, and goes through the
same checks. Uploads are read in memory and never saved.
"""

import io

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

import surveys
from reports import excel_safe

ID_MARKER = "Through Line ids"
INK, INPUT = "23262B", "FFF8E6"
MULTI_HINT = "Choose all that apply: separate choices with ; (semicolon)"


def _columns(inst, wave: str) -> list[dict]:
    """[{id, header, choices (list|None), multi, scale}] for this wave's questions, then demographics at pre."""
    cols = []
    for q in surveys.questions_for(inst.questions, wave):
        scale = q["scale"]
        choices = q.get("options") if scale in surveys.CHOICE else surveys.SCALES[scale]["options"]
        cols.append({"id": q["id"], "header": q["text"], "choices": choices, "multi": scale == "multi_choice",
                     "scale": scale})
    if wave == "pre":
        for key in inst.demographics:
            spec = surveys.DEMOGRAPHICS.get(key)
            if spec:
                cols.append({"id": f"demo:{key}", "header": spec["label"], "choices": spec["options"],
                             "multi": spec["multi"], "scale": "demographic"})
    return cols


def _cell_value(col: dict, raw):
    """Stored answer -> what staff see in the sheet (rated answers as their label)."""
    if raw is None:
        return None
    if isinstance(raw, list):
        return "; ".join(str(x) for x in raw)
    scale = col["scale"]
    if scale in surveys.MAX_VALUE:  # rated: stored as a number, shown as its label
        base = surveys.MIN_VALUE[scale]
        opts = surveys.SCALES[scale]["options"]
        i = int(raw) - base
        return opts[i] if 0 <= i < len(opts) else raw
    return excel_safe(raw)


def template_xlsx(org_name: str, inst, wave: str, participants: list, responses: list) -> bytes:
    cols = _columns(inst, wave)
    have = {r.participant_id: r for r in responses if r.wave == wave}
    wb = Workbook()
    ws = wb.active
    ws.title = "Responses"
    lists = wb.create_sheet("Choices")
    lists.sheet_state = "hidden"

    ws.append([excel_safe(f"{org_name}: {inst.name}, {wave.upper()} responses")])
    ws["A1"].font = Font(bold=True, size=14, color=INK)
    ws.append(["One row per participant. Fill in the yellow cells (use the dropdowns), save, and upload this file "
               "under Enter responses. Leave a row blank to skip that person. Don't change rows 3–4 or the codes."])
    ws["A2"].font = Font(italic=True, color="6B6F76")
    ws.append([ID_MARKER] + [c["id"] for c in cols])  # row 3: question ids (hidden), how uploads find the questions
    ws.row_dimensions[3].hidden = True
    ws.append(["Participant code"] + [excel_safe(c["header"]) for c in cols])
    for cell in ws[4]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=INK)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[4].height = 60

    for p in sorted(participants, key=lambda p: p.code):
        r = have.get(p.id)
        row = [p.code]
        for c in cols:
            if c["id"].startswith("demo:"):
                row.append(_cell_value(c, (r.demographics if r else {}).get(c["id"][5:])))
            else:
                row.append(_cell_value(c, (r.answers if r else {}).get(c["id"])))
        ws.append(row)
    last = max(ws.max_row, 5)

    for i, c in enumerate(cols, start=2):
        letter = ws.cell(4, i).column_letter
        ws.column_dimensions[letter].width = 26
        for rr in range(5, last + 1):
            ws.cell(rr, i).fill = PatternFill("solid", fgColor=INPUT)
        if c["choices"] and not c["multi"]:
            for j, opt in enumerate(c["choices"], start=1):
                lists.cell(j, i, opt)
            dv = DataValidation(type="list", formula1=f"=Choices!${letter}$1:${letter}${len(c['choices'])}",
                                allow_blank=True, error="Please pick one of the choices.", errorTitle="Choose from the list")
            ws.add_data_validation(dv)
            dv.add(f"{letter}5:{letter}{last}")
        elif c["multi"]:
            ws.cell(4, i).comment = Comment(MULTI_HINT + ": " + "; ".join(c["choices"] or []), "Through Line")
        elif c["scale"] == "number":
            dv = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
                                error="Please enter a number.", errorTitle="Numbers only")
            ws.add_data_validation(dv)
            dv.add(f"{letter}5:{letter}{last}")
    ws.column_dimensions["A"].width = 18
    ws.freeze_panes = "B5"
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def parse_upload(data: bytes, inst, wave: str) -> tuple[list[dict], list[dict]]:
    """Return (rows, errors). Rows match the bulk-entry API: {line, participant_code, answers, demographics}.
    Labels are turned back into stored values here; the usual checks (surveys.clean_answers) run afterwards."""
    try:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:
        raise ValueError("That file couldn't be opened as an Excel workbook (.xlsx).") from exc
    ws = wb["Responses"] if "Responses" in wb.sheetnames else wb.worksheets[0]
    cols = {c["id"]: c for c in _columns(inst, wave)}
    ids: list[str] | None = None
    rows, errors = [], []
    for line, values in enumerate(ws.iter_rows(values_only=True), start=1):
        values = list(values)
        if ids is None:
            if str(values[0] or "").strip() == ID_MARKER:
                ids = [str(v or "") for v in values[1:]]
            continue
        code = str(values[0] or "").strip().upper()
        if not code or code == "PARTICIPANT CODE":
            continue
        answers, demo = {}, {}
        for qid, raw in zip(ids, values[1:]):
            if raw in (None, "") or qid not in cols:
                continue
            col = cols[qid]
            if qid.startswith("demo:"):
                demo[qid[5:]] = [x.strip() for x in str(raw).split(";")] if col["multi"] else str(raw).strip()
            elif col["scale"] in surveys.MAX_VALUE:  # a label (or the number itself) -> the stored number
                opts = surveys.SCALES[col["scale"]]["options"]
                text = str(raw).strip()
                match = next((k for k, o in enumerate(opts) if o.lower() == text.lower()), None)
                answers[qid] = match + surveys.MIN_VALUE[col["scale"]] if match is not None else text
            else:
                answers[qid] = raw if not isinstance(raw, str) else raw.strip()
        if answers or demo:
            rows.append({"line": line, "participant_code": code, "answers": answers, "demographics": demo})
    if ids is None:
        raise ValueError("This doesn't look like a Through Line responses template. Download a fresh one.")
    unknown = [i for i in ids if i and i not in cols]
    if unknown:
        errors.append({"line": 3, "error": "Some columns are for questions this survey doesn't ask at this wave "
                                           "anymore; they were skipped. Download a fresh template."})
    return rows, errors
