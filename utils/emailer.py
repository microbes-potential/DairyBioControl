# utils/emailer.py
import os, smtplib

def _env(key, default=""):
    return (os.environ.get(key, default) or "").strip()

SMTP_HOST = _env("SMTP_HOST")            # e.g. mail.gmx.com
SMTP_PORT = int(_env("SMTP_PORT") or "587")
SMTP_USER = _env("SMTP_USER")            # dairybiocontrol@gmx.com
SMTP_PASS = _env("SMTP_PASS")            # your GMX password
SMTP_FROM = _env("SMTP_FROM") or SMTP_USER or "noreply@example.com"

# Optional: set to "1" to disable tries beyond your configured host/port
DISABLE_FALLBACK = _env("SMTP_DISABLE_FALLBACK") == "1"

# Known GMX endpoints we can try if primary fails (only if fallback enabled)
_GMX_ALTS = [
    ("mail.gmx.com", 587, False),  # STARTTLS
    ("mail.gmx.com", 465, True),   # SSL
    ("mail.gmx.net", 587, False),
    ("mail.gmx.net", 465, True),
    ("smtp.gmx.com", 465, True),
]

def _send(host, port, use_ssl, to_list, subject, body, reply_to=None):
    headers = [
        f"From: {SMTP_FROM}",
        f"To: {', '.join(to_list)}",
        f"Subject: {subject}",
    ]
    if reply_to:
        headers.append(f"Reply-To: {reply_to}")
    msg = "\r\n".join(headers) + "\r\n\r\n" + body

    # Choose SSL vs STARTTLS
    Smtp = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    try:
        with Smtp(host, port, timeout=30) as server:
            if not use_ssl:
                server.ehlo()
                server.starttls()
                server.ehlo()
            # IMPORTANT: full email as username
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, to_list, msg.encode("utf-8"))
        return True, f"Message sent via {host}:{port} ({'SSL' if use_ssl else 'STARTTLS'})."
    except Exception as e:
        return False, f"FAIL {host}:{port} -> {e}"

def _send_raw(to_list, subject, body, reply_to=None):
    if not to_list:
        return "No recipients provided."
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        return "SMTP not configured; skipping send (set SMTP_* env vars)."

    # 1) Try the configured host/port exactly as provided
    primary_use_ssl = (str(SMTP_PORT) == "465")
    ok, msg = _send(SMTP_HOST, SMTP_PORT, primary_use_ssl, to_list, subject, body, reply_to=reply_to)
    print(f"[EMAIL] primary {SMTP_HOST}:{SMTP_PORT} -> {msg}")  # debug
    if ok:
        return msg

    # 2) Optional GMX fallback tries
    if DISABLE_FALLBACK:
        return f"Email send failed: {msg}"

    tried = [f"{SMTP_HOST}:{SMTP_PORT}"]
    for host, port, use_ssl in _GMX_ALTS:
        key = f"{host}:{port}"
        if key in tried:
            continue
        ok2, msg2 = _send(host, port, use_ssl, to_list, subject, body, reply_to=reply_to)
        print(f"[EMAIL] alt {key} -> {msg2}")  # debug
        if ok2:
            return msg2
        tried.append(key)

    return f"Email send failed: {msg}"

def send_results_email(to_email, subject, body):
    return _send_raw([to_email] if to_email else [], subject, body)

def send_email_many(to_emails, subject, body, reply_to=None):
    return _send_raw([e for e in to_emails if e], subject, body, reply_to=reply_to)

