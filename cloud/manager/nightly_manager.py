#!/usr/bin/env python3
"""PC-independent 1 AM IST control report for Amala's eight daily slots."""

from __future__ import annotations

import imaplib
import json
import os
import smtplib
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

from openpyxl import Workbook, load_workbook


IST = ZoneInfo("Asia/Kolkata")
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "management"
WORKBOOK = OUTPUT / "amala-openclaw-control.xlsx"
REPOS = {
    "09:00 AM": ("9am-office-work", "Business AI office run"),
    "09:00 PM": ("9am-office-work", "Business AI evening run"),
    "10:00 AM": ("10am-office-work", "Local-business website run"),
    "10:00 PM": ("10am-office-work", "Local-business website evening run"),
    "11:00 AM": ("11am-office-work", "Website streak run"),
    "11:00 PM": ("11am-office-work", "Application streak run"),
    "12:00 AM": ("12am-office-work", "Cyber Guardian midnight run"),
    "12:00 PM": ("12am-office-work", "Cyber Guardian noon run"),
}


def api(path: str):
    request = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "AmalaOpenClawManager/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def near_slot(value: str, day, hour: int, tolerance_minutes: int = 100) -> bool:
    actual = parse_utc(value).astimezone(IST)
    expected = datetime(day.year, day.month, day.day, hour, tzinfo=IST)
    return abs((actual - expected).total_seconds()) <= tolerance_minutes * 60


def action_evidence(repo: str, day, hour: int):
    data = api(f"/repos/amalraj020-a11y/{repo}/actions/runs?per_page=30")
    matches = [
        run for run in data.get("workflow_runs", [])
        if near_slot(run["created_at"], day, hour)
    ]
    if not matches:
        return "MISSED", "", "", "No workflow run found near the assigned slot"
    run = min(
        matches,
        key=lambda item: abs(
            (
                parse_utc(item["created_at"]).astimezone(IST)
                - datetime(day.year, day.month, day.day, hour, tzinfo=IST)
            ).total_seconds()
        ),
    )
    status = "COMPLETED" if run.get("conclusion") == "success" else (
        "IN PROGRESS" if run.get("status") != "completed" else "FAILED"
    )
    started = parse_utc(run["created_at"]).astimezone(IST).isoformat(timespec="seconds")
    finished = parse_utc(run["updated_at"]).astimezone(IST).isoformat(timespec="seconds")
    return status, started, finished, run["html_url"]


def commit_evidence(repo: str, day, hour: int):
    commits = api(f"/repos/amalraj020-a11y/{repo}/commits?per_page=50")
    matches = []
    expected = datetime(day.year, day.month, day.day, hour, tzinfo=IST)
    for commit in commits:
        value = commit.get("commit", {}).get("committer", {}).get("date")
        if not value:
            continue
        actual = parse_utc(value).astimezone(IST)
        if abs((actual - expected).total_seconds()) <= 120 * 60:
            matches.append((actual, commit))
    if not matches:
        return "MISSED", "", "", "No repository commit found near the assigned slot"
    actual, commit = min(matches, key=lambda item: abs((item[0] - expected).total_seconds()))
    stamp = actual.isoformat(timespec="seconds")
    return "COMPLETED", stamp, stamp, commit["html_url"]


def cyber_evidence(day, session: str):
    path = f"reports/cyber-guardian/{day.isoformat()}-{session}.md"
    url = f"https://github.com/amalraj020-a11y/12am-office-work/blob/main/{path}"
    try:
        data = api(f"/repos/amalraj020-a11y/12am-office-work/contents/{path}")
        if data.get("sha"):
            return "COMPLETED", "", "", url
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    return "MISSED", "", "", f"Missing expected report: {url}"


def collect(day):
    rows = []
    for slot, (repo, workflow) in REPOS.items():
        hour = datetime.strptime(slot, "%I:%M %p").hour
        if repo in ("9am-office-work", "11am-office-work"):
            status, started, finished, evidence = action_evidence(repo, day, hour)
        elif repo == "10am-office-work":
            status, started, finished, evidence = commit_evidence(repo, day, hour)
        elif slot == "12:00 AM":
            status, started, finished, evidence = cyber_evidence(day, "12AM")
        else:
            status, started, finished, evidence = cyber_evidence(day, "12PM")
        rows.append({
            "slot": slot,
            "workflow": workflow,
            "status": status,
            "started": started,
            "finished": finished,
            "evidence": evidence,
            "credential_access": "Do not access",
            "money_impact": "₹0",
        })
    return rows


def workbook(day, rows):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if WORKBOOK.exists():
        book = load_workbook(WORKBOOK)
    else:
        book = Workbook()
        daily = book.active
        daily.title = "Daily Reports"
        daily.append([
            "Report Date", "Completed", "Failed/Missed", "In Progress",
            "Executive Summary", "Email Status", "Sent At",
        ])
        log = book.create_sheet("Work Log")
        log.append([
            "Report Date", "Schedule Time", "Workflow", "Run Status",
            "Started At", "Finished At", "Evidence / Link",
            "Credential Access", "Money Impact",
        ])
    daily = book["Daily Reports"]
    log = book["Work Log"]
    completed = sum(row["status"] == "COMPLETED" for row in rows)
    missed = sum(row["status"] in ("FAILED", "MISSED") for row in rows)
    progress = sum(row["status"] == "IN PROGRESS" for row in rows)
    summary = f"{completed}/8 completed; {missed} failed or missed; {progress} in progress."
    daily.append([day.isoformat(), completed, missed, progress, summary, "PENDING", ""])
    for row in rows:
        log.append([
            day.isoformat(), row["slot"], row["workflow"], row["status"],
            row["started"], row["finished"], row["evidence"],
            row["credential_access"], row["money_impact"],
        ])
    for sheet in book.worksheets:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = cell.font.copy(bold=True)
    book.save(WORKBOOK)
    return len(daily["A"])


def render(day, rows) -> tuple[str, str]:
    completed = sum(row["status"] == "COMPLETED" for row in rows)
    lines = [
        f"# Amala OpenClaw Control Report — {day.isoformat()}",
        "",
        f"Result: {completed}/8 assigned runs completed with evidence.",
        "",
        "| Time | Workflow | Status | Evidence |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['slot']} | {row['workflow']} | {row['status']} | {row['evidence']} |"
        )
    lines += [
        "",
        "Restrictions enforced: no credential-value access, no purchases, no billing changes, and ₹0 additional spend.",
    ]
    body = "\n".join(lines) + "\n"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / f"{day.isoformat()}.md").write_text(body, encoding="utf-8")
    return f"Amala OpenClaw Control Report — {day.isoformat()}", body


def select_all_mail(imap):
    status, folders = imap.list()
    if status != "OK":
        raise RuntimeError("Unable to list Gmail folders")
    all_mail = None
    for raw in folders or []:
        decoded = raw.decode("utf-8", errors="replace")
        if "\\All" in decoded:
            all_mail = decoded.rsplit(' "', 1)[-1].strip('"')
            break
    status, _ = imap.select(f'"{all_mail or "[Gmail]/All Mail"}"', readonly=True)
    if status != "OK":
        raise RuntimeError("Unable to open Gmail All Mail")


def sent_exists(address: str, password: str, subject: str) -> bool:
    with imaplib.IMAP4_SSL("imap.gmail.com", 993, ssl_context=ssl.create_default_context()) as imap:
        imap.login(address, password)
        select_all_mail(imap)
        query = f'in:sent to:{address} subject:"{subject}"'.replace('"', '\\"')
        status, data = imap.uid("SEARCH", None, "X-GM-RAW", f'"{query}"')
        return status == "OK" and bool((data[0] or b"").split())


def send_report(subject: str, body: str):
    address = os.getenv("GMAIL_ADDRESS", "").strip().lower()
    password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if address != "amalaraj020@gmail.com" or not password:
        raise RuntimeError("Configured Gmail account is missing or is not amalaraj020@gmail.com")
    if sent_exists(address, password, subject):
        return "SKIPPED_DUPLICATE"
    message = EmailMessage()
    message["From"] = address
    message["To"] = address
    message["Subject"] = subject
    message.set_content(body)
    message.add_attachment(
        WORKBOOK.read_bytes(),
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=WORKBOOK.name,
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30) as smtp:
        smtp.login(address, password)
        smtp.send_message(message)
    for _ in range(6):
        if sent_exists(address, password, subject):
            return "SENT_VERIFIED"
        time.sleep(5)
    raise RuntimeError("Gmail accepted the report but it was not verified in Sent")


def finish_workbook(row_number: int, email_status: str):
    book = load_workbook(WORKBOOK)
    sheet = book["Daily Reports"]
    sheet.cell(row=row_number, column=6, value=email_status)
    sheet.cell(row=row_number, column=7, value=datetime.now(IST).isoformat(timespec="seconds"))
    book.save(WORKBOOK)


def main():
    now = datetime.now(IST)
    report_day = (now - timedelta(days=1)).date()
    rows = collect(report_day)
    daily_row = workbook(report_day, rows)
    subject, body = render(report_day, rows)
    email_status = send_report(subject, body)
    finish_workbook(daily_row, email_status)
    print(json.dumps({
        "report_date": report_day.isoformat(),
        "completed": sum(row["status"] == "COMPLETED" for row in rows),
        "email_status": email_status,
        "workbook": str(WORKBOOK.relative_to(ROOT)),
    }))


if __name__ == "__main__":
    main()
