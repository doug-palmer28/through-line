"""Read what the client already has: uploaded files and their website.

Privacy rule: uploads are read from memory and NEVER written to disk. The
extracted text lives only in the in-memory session and is dropped as soon as
the team has finished reading it (see sessions.py). The audit log records only
the kind and size of each source, never its name or content.

Safety rule: agents read only what a person can see. visible.py drops white,
tiny, off-page, transparent, covered, and hidden-formatted text, invisible
characters, and hidden web content, and counts what it skipped (never the text).

Token rule: every source is capped, and so is the total, so one huge annual
report can't blow up the cost of a session.
"""

import ipaddress
import re
import socket
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx
from starlette.concurrency import run_in_threadpool

import visible
from audit import audit_append
from security import check_zip

MAX_FILES = 5
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_CHARS_PER_SOURCE = 20_000
MAX_TOTAL_CHARS = 50_000
MAX_WEBSITE_BYTES = 2 * 1024 * 1024
WEBSITE_DEADLINE = 20  # seconds for the whole fetch, however slowly a site drips bytes
SUPPORTED = {".pdf", ".docx", ".pptx", ".txt", ".md"}


class IntakeError(ValueError):
    """A problem the client can fix (wrong file type, bad URL, ...)."""


@dataclass
class Source:
    label: str  # e.g. "Document 1 (PDF)". Deliberately not the file name.
    kind: str
    text: str
    truncated: bool
    hidden: list[dict] = field(default_factory=list)  # [{reason, chars}] skipped because a person can't see it

    def manifest(self) -> dict:
        """What may be logged: kind, size, and how much hidden text was skipped (never the text)."""
        return {"label": self.label, "kind": self.kind, "chars": len(self.text), "truncated": self.truncated,
                "hidden": self.hidden}


def _clean(text: str) -> str:
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def _cap(text: str) -> tuple[str, bool]:
    text = _clean(text)
    if len(text) <= MAX_CHARS_PER_SOURCE:
        return text, False
    return text[:MAX_CHARS_PER_SOURCE], True


# ============================================================ files


def _file_text(suffix: str, data: bytes) -> tuple[str, visible.Hidden]:
    """The visible text of a file, plus what was skipped."""
    if suffix == ".pdf":
        return visible.pdf_text(data)
    if suffix == ".docx":
        return visible.docx_text(data)
    if suffix == ".pptx":
        return visible.pptx_text(data)
    text = data.decode("utf-8", errors="replace")
    return visible.markdown_text(text) if suffix == ".md" else visible.plain_text(text)


def read_upload(index: int, filename: str, data: bytes) -> Source:
    suffix = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if suffix not in SUPPORTED:
        raise IntakeError(f"'{filename}' isn't a supported type. Use PDF, Word, PowerPoint, or text files.")
    if len(data) > MAX_FILE_BYTES:
        raise IntakeError(f"'{filename}' is larger than 10 MB.")
    try:
        if suffix in (".docx", ".pptx"):
            check_zip(data)
        raw, hidden = _file_text(suffix, data)
    except ValueError as exc:
        raise IntakeError(f"Couldn't read '{filename}': {exc}") from exc
    except Exception as exc:  # corrupt or password-protected files
        raise IntakeError(f"Couldn't read '{filename}'. Is it a valid, unlocked file?") from exc
    text, truncated = _cap(raw)
    return _noted(Source(label=f"Document {index} ({suffix[1:].upper()})", kind=suffix[1:], text=text,
                         truncated=truncated, hidden=hidden.summary()))


def _noted(source: Source) -> Source:
    """Log (counts only) when a source had text a person couldn't see."""
    if source.hidden:
        audit_append(event="hidden_text_skipped", agent="intake", team="safety",
                     output={"source": source.label, "kind": source.kind, "hidden": source.hidden})
    return source


# ============================================================ website


def _check_public(url: str) -> None:
    """Only fetch public http(s) sites, never this machine or a private network."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise IntakeError("The website address should start with http:// or https://")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise IntakeError(f"Couldn't find the website '{parsed.hostname}'.") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise IntakeError("That website address points to a private network, so it can't be read.")


def _peer_is_public(resp: httpx.Response) -> bool:
    """The address we actually connected to (guards against DNS that changes between the check and the fetch)."""
    stream = resp.extensions.get("network_stream")
    addr = stream.get_extra_info("server_addr") if stream is not None else None
    if not addr:
        return True  # not exposed by this transport; the pre-flight check still applied
    return ipaddress.ip_address(addr[0]).is_global


def read_website(url: str, label: str = "Website home page") -> Source:
    """Fetch one public page: ≤ 3 redirects, each hop checked, ≤ 2 MB, ≤ 20 seconds in total.

    Blocking by design; async routes call it through run_in_threadpool so a slow site never stalls the server.
    """
    url = url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    deadline = time.monotonic() + WEBSITE_DEADLINE
    body = b""
    with httpx.Client(timeout=8, follow_redirects=False, headers={"User-Agent": "ThroughLine/0.1 (class project)"}) as client:
        for _ in range(4):  # follow up to 3 redirects, checking each hop
            _check_public(url)
            try:
                with client.stream("GET", url) as resp:
                    if not _peer_is_public(resp):
                        raise IntakeError("That website address points to a private network, so it can't be read.")
                    if resp.is_redirect and "location" in resp.headers:
                        url = urljoin(url, resp.headers["location"])
                        continue
                    if resp.status_code >= 400:
                        raise IntakeError(f"The website returned an error ({resp.status_code}).")
                    chunks, size = [], 0
                    for chunk in resp.iter_bytes():
                        size += len(chunk)
                        if size > MAX_WEBSITE_BYTES:
                            raise IntakeError("That web page is too large to read.")
                        if time.monotonic() > deadline:
                            raise IntakeError("That website took too long to respond.")
                        chunks.append(chunk)
                    body, encoding = b"".join(chunks), resp.encoding or "utf-8"
                    break
            except httpx.HTTPError as exc:
                raise IntakeError("Couldn't reach that website.") from exc
        else:
            raise IntakeError("That website redirected too many times.")
    raw, hidden = visible.html_text(body.decode(encoding, errors="replace"))
    text, truncated = _cap(raw)
    return _noted(Source(label=label, kind="website", text=text, truncated=truncated, hidden=hidden.summary()))


async def read_upload_files(files, start: int = 1) -> list[Source]:
    """Read UploadFiles with a hard size cap, parsing off the event loop. Memory only."""
    sources = []
    for i, f in enumerate(files, start=start):
        name = f.filename or f"file{i}"
        if f.size is not None and f.size > MAX_FILE_BYTES:
            raise IntakeError(f"'{name}' is larger than 10 MB.")
        data = await f.read(MAX_FILE_BYTES + 1)
        await f.close()
        sources.append(await run_in_threadpool(read_upload, i, name, data))  # read_upload rejects > 10 MB
        del data
    return sources


async def fetch_website(url: str, label: str = "Website home page") -> Source:
    return await run_in_threadpool(read_website, url, label)


def combine(sources: list[Source]) -> str:
    """One block of reference text for the boss, capped in total and clearly fenced as data."""
    blocks, used = [], 0
    for s in sources:
        room = MAX_TOTAL_CHARS - used
        if room <= 0:
            break
        body = s.text[:room]
        used += len(body)
        blocks.append(f'<source label="{s.label}">\n{body}\n</source>')
    return "\n\n".join(blocks)
