"""Deterministic personal-information scanner (no AI).

Used on participant quotes BEFORE any agent sees them, on every line of finished reports and grant
drafts AFTER the Privacy Reviewer (and again whenever they're rendered), and on agent outputs before
they're written to the audit log.

It catches the patterns code can catch reliably: participant codes, emails, phone numbers,
SSN-like numbers, street addresses, and dates of birth. Personal names need judgement, so the
Privacy Reviewer agent handles those (see prompts/privacy_reviewer.md).
"""

import re

PATTERNS: dict[str, re.Pattern] = {
    "participant code": re.compile(r"\b[A-Z]{2,4}-\d{4}[A-Z]\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "phone number": re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)"),
    "SSN-like number": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "street address": re.compile(r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s){1,3}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|"
                                 r"Drive|Dr|Court|Ct|Place|Pl|Way|Terrace)\b\.?"),
    # An actual date after "born"/"DOB" (not "foreign-born residents make up 40%" or "born in 2025").
    "date of birth": re.compile(
        r"\b(?:born|DOB|D\.O\.B\.|date of birth)\b\s*:?\s*(?:on\s+)?"
        r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?"
        r"|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{4}-\d{2}-\d{2})", re.I),
}


def scan(text: str) -> list[dict]:
    """Every match: {kind, text}."""
    found = []
    for kind, pattern in PATTERNS.items():
        for m in pattern.finditer(text or ""):
            found.append({"kind": kind, "text": m.group(0)})
    return found


def redact(text: str) -> tuple[str, list[dict]]:
    """Replace every match with [removed]; return the clean text and what was removed (kinds only are logged)."""
    found = scan(text)
    for f in found:
        text = text.replace(f["text"], "[removed]")
    return text, found


def scan_tree(obj, path: str = "") -> list[dict]:
    """Scan every string inside a nested dict/list (e.g. a whole deck plan). Returns {where, kind, text}."""
    hits = []
    if isinstance(obj, str):
        hits += [{"where": path or "text", **f} for f in scan(obj)]
    elif isinstance(obj, dict):
        for k, v in obj.items():
            hits += scan_tree(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += scan_tree(v, f"{path}[{i}]")
    return hits


def redact_tree(obj):
    """Return a copy with every match in every string replaced by [removed]."""
    if isinstance(obj, str):
        return redact(obj)[0]
    if isinstance(obj, dict):
        return {k: redact_tree(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_tree(v) for v in obj]
    return obj


def replace_tree(obj, old: str, new: str):
    """Replace an exact phrase everywhere in a nested structure (used to apply the agent's privacy fixes)."""
    if isinstance(obj, str):
        return obj.replace(old, new)
    if isinstance(obj, dict):
        return {k: replace_tree(v, old, new) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_tree(v, old, new) for v in obj]
    return obj
