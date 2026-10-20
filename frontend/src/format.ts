/** A server timestamp (UTC, with or without an offset) in the viewer's local time, e.g. "Oct 20, 2026, 11:25 AM". */
export function when(iso: string): string {
  const utc = /[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`;
  const d = new Date(utc);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}
