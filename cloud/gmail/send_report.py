"""Send verified Amala outreach through Gmail from a headless runner."""

from __future__ import annotations

import imaplib
import json
import os
import re
import smtplib
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
SLOT = re.sub(r"[^a-zA-Z0-9_-]", "-", os.getenv("AMALA_SLOT", "manual"))
DAY = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
RUN_ID = f"{DAY}-{SLOT}"
RUN_DIR = ROOT / "runs" / RUN_ID
REPORT_PATH = RUN_DIR / "report.md"
DELIVERY_PATH = RUN_DIR / "delivery.json"
RUN_LOG_PATH = ROOT / "run-log.jsonl"

# Exact pairs manually verified from the businesses' public official pages on
# 2026-11-14. This is intentionally narrow: a changed URL or address blocks
# delivery until it is reviewed again.
VERIFIED_RECIPIENTS = {
    ("https://www.mobilemistri.com/", "info@mobilemistri.com"),
    ("https://vivalaundry.in/", "hello@vivalaundry.in"),
    ("https://easylaundry.in/", "support@easylaundry.in"),
    ("https://www.mykhana.in/", "sales@mykhana.in"),
    ("https://shuchilaundry.com/", "info@shuchilaundry.com"),
    ("https://gocaters.in/", "admin@gocaters.in"),
    ("https://doorstepfix.com/", "mansoor@doorstepfix.com"),
}


def report_field(report: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}:\s*(.+)$", report, re.MULTILINE)
    if not match:
        raise ValueError(f"Missing report field: {label}")
    return match.group(1).strip()


def draft_parts(report: str) -> tuple[str, str]:
    try:
        section = report.split("## Draft email", 1)[1].split("## Test output", 1)[0].strip()
    except IndexError as error:
        raise ValueError("The outreach draft could not be parsed") from error
    lines = section.splitlines()
    if not lines or not lines[0].startswith("Subject:"):
        raise ValueError("The outreach draft could not be parsed")
    subject = lines[0].removeprefix("Subject:").strip()
    body = "\n".join(lines[1:]).strip()
    if not subject or not body:
        raise ValueError("The outreach draft is incomplete")
    return subject, body


def select_all_mail(imap: imaplib.IMAP4_SSL) -> None:
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
        raise RuntimeError("Unable to open Gmail All Mail for verification")


def connect_imap(address: str, password: str) -> imaplib.IMAP4_SSL:
    imap = imaplib.IMAP4_SSL("imap.gmail.com", 993, ssl_context=ssl.create_default_context())
    imap.login(address, password)
    select_all_mail(imap)
    return imap


def gmail_query(imap: imaplib.IMAP4_SSL, query: str) -> list[bytes]:
    escaped = query.replace("\\", "\\\\").replace('"', '\\"')
    status, data = imap.uid("SEARCH", None, "X-GM-RAW", f'"{escaped}"')
    if status != "OK":
        raise RuntimeError(f"Gmail search failed: {status}")
    return (data[0] or b"").split()


def duplicate_exists(address: str, password: str, recipient: str, subject: str) -> bool:
    with connect_imap(address, password) as imap:
        return bool(gmail_query(
            imap,
            f'(in:sent OR in:drafts) to:{recipient} subject:"{subject}"',
        ))


def sent_exists(address: str, password: str, recipient: str, subject: str) -> bool:
    with connect_imap(address, password) as imap:
        return bool(gmail_query(imap, f'in:sent to:{recipient} subject:"{subject}"'))


def send(address: str, password: str, recipient: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = address
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP_SSL(
        "smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30
    ) as smtp:
        smtp.login(address, password)
        smtp.send_message(message)


def verify_sent(address: str, password: str, recipient: str, subject: str) -> None:
    for _ in range(6):
        if sent_exists(address, password, recipient, subject):
            return
        time.sleep(5)
    raise RuntimeError("Gmail accepted the message but it was not verified in Sent")


def save_result(result: dict) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    DELIVERY_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with RUN_LOG_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"runId": RUN_ID, "gmailDelivery": result["status"]}) + "\n")


def recipient_is_public(official_source: str, recipient: str, saved_evidence: str) -> bool:
    if (official_source, recipient) in VERIFIED_RECIPIENTS:
        return True
    if recipient in saved_evidence.lower():
        return True
    parsed = urllib.parse.urlparse(official_source)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Official source must be a valid HTTPS URL")
    request = urllib.request.Request(
        official_source,
        headers={"User-Agent": "AmalaBusinessResearch/2.0 (+recipient-verification)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read(2_000_000).decode("utf-8", errors="replace")
    return recipient in page.lower()


def main() -> None:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Report does not exist: {REPORT_PATH}")

    address = os.getenv("GMAIL_ADDRESS", "").strip().lower()
    password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if address != "amalaraj020@gmail.com" or not password:
        save_result({
            "status": "BLOCKED",
            "reason": "Cloud Gmail credentials are not configured for amalaraj020@gmail.com",
        })
        print("Gmail delivery BLOCKED: cloud credentials are not configured")
        return

    report = REPORT_PATH.read_text(encoding="utf-8")
    business = report_field(report, "Business")
    official_source = report_field(report, "Official source")
    recipient = report_field(report, "Public email").lower()
    model = report_field(report, "Model")
    tests = report_field(report, "Tests")
    cost = report_field(report, "Actual paid API cost")
    subject, body = draft_parts(report)

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", recipient):
        raise ValueError("The report does not contain a valid public recipient")
    evidence = (RUN_DIR / "official-site-evidence.txt").read_text(encoding="utf-8")
    if not recipient_is_public(official_source, recipient, evidence):
        raise ValueError("Recipient is not present on the official public source")

    duplicate = duplicate_exists(address, password, recipient, subject)
    if duplicate:
        outreach_status = "SKIPPED_DUPLICATE"
    else:
        send(address, password, recipient, subject, body)
        verify_sent(address, password, recipient, subject)
        outreach_status = "SENT_VERIFIED"

    summary_subject = f"Amala {SLOT} run — {DAY}"
    summary_body = (
        f"Amala office run {RUN_ID} completed.\n\n"
        f"Business: {business}\nOfficial source: {official_source}\n"
        f"Model: {model}\nTests: {tests}\nOutreach: {outreach_status}\n"
        f"Actual paid API cost: {cost}\n"
        f"Report: https://github.com/amalraj020-a11y/9am-office-work/blob/main/"
        f"runs/{RUN_ID}/report.md\n"
    )
    if not duplicate_exists(address, password, address, summary_subject):
        send(address, password, address, summary_subject, summary_body)
        verify_sent(address, password, address, summary_subject)

    save_result({
        "status": "PASS",
        "account": address,
        "recipient": recipient,
        "recipientEvidence": "official-site-evidence.txt",
        "duplicateCheck": "CLEAR" if not duplicate else "MATCHED",
        "outreach": outreach_status,
        "ownerReport": "SENT_VERIFIED",
        "costInr": 0,
    })
    print(f"Gmail delivery PASS: outreach={outreach_status}; ownerReport=SENT_VERIFIED")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        save_result({"status": "FAIL", "reason": str(error)})
        raise
