# app4.py
from dotenv import load_dotenv
load_dotenv()

import os, json, smtplib
from pathlib import Path

import dash
from dash import dcc, html, Input, Output
from itsdangerous import URLSafeSerializer, BadSignature

from components.sidebar import sidebar, content_style
from utils.trait_db import load_trait_db

from pages.home import page_home
from pages.documentation import page_documentation
from pages.login import register_callbacks as login_callbacks, page_login
from pages.upload import register_callbacks as upload_callbacks, page_upload
from pages.module_safety import register_callbacks as safety_callbacks, page_module as page_safety
from pages.module_dairy import register_callbacks as dairy_callbacks, page_module as page_dairy
from pages.module_antibacterial import register_callbacks as abx_callbacks, page_module as page_abx
from pages.module_antifungal import register_callbacks as af_callbacks, page_module as page_af
from pages.results import register_callbacks as results_callbacks, page_results
from pages.about import page_about
from pages.contact import page_contact, register_callbacks as contact_callbacks
from pages.cite import page_cite

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "DairyBioControl"

# ---- Load DB once
TRAIT_DB = load_trait_db()
app.server.config["TRAIT_DB"] = TRAIT_DB

# ---- Email verification config
USERS_DB = Path("assets/users.db.json")
EMAIL_VERIFY_SECRET = os.environ.get("EMAIL_VERIFY_SECRET", "change-me-please")
VERIFY_SALT = "email-verify"
serializer = URLSafeSerializer(EMAIL_VERIFY_SECRET, salt=VERIFY_SALT)

def _load_users():
    if USERS_DB.exists():
        try:
            return json.loads(USERS_DB.read_text())
        except Exception:
            pass
    return {"users": []}

def _save_users(d):
    USERS_DB.parent.mkdir(parents=True, exist_ok=True)
    USERS_DB.write_text(json.dumps(d, indent=2))

@server.route("/verify/<token>")
def verify_user(token):
    try:
        email = serializer.loads(token)
    except BadSignature:
        return "<h2>Invalid or expired verification link.</h2>", 400

    db = _load_users()
    changed = False
    for u in db.get("users", []):
        if u.get("email", "").lower() == str(email).lower():
            if not u.get("approved", False):
                u["approved"] = True
                changed = True
            break

    if changed:
        _save_users(db)
        return """<div style="font-family:system-ui;padding:24px">
                    <h2>✅ Email verified</h2>
                    <p>Your account is now active. You can return to the app and sign in.</p>
                  </div>"""
    else:
        if any(u.get("email","").lower()==str(email).lower() for u in db.get("users", [])):
            return """<div style="font-family:system-ui;padding:24px">
                        <h2>ℹ️ Already verified</h2>
                        <p>Your account is already active. You can sign in.</p>
                      </div>"""
        return "<h2>User not found.</h2>", 404

@server.route("/smtp_selftest")
def smtp_selftest():
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "0") or 0)
    user = os.environ.get("SMTP_USER", "")
    pwd  = os.environ.get("SMTP_PASS", "")
    if not host or not port or not user or not pwd:
        return "FAIL: Missing SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS env vars", 500
    use_ssl = (str(port) == "465")
    try:
        S = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with S(host, port, timeout=20) as s:
            if not use_ssl:
                s.ehlo(); s.starttls(); s.ehlo()
            s.login(user, pwd)
        return f"OK: logged in to {host}:{port} as {user}"
    except Exception as e:
        return f"FAIL: {host}:{port} user={user} -> {e}", 500

# ---- Render health check (added) ----
@server.get("/health")
def health():
    return "ok", 200

# ------------------ GLOBAL stores (always present) ------------------
# These are referenced by module/result callbacks. Keeping them here
# avoids “nonexistent object” errors when navigating off the upload page.
_global_stores = html.Div([
    dcc.Store(id="store-features"),
    dcc.Store(id="store-filename"),
    dcc.Store(id="store-filekind"),
    dcc.Store(id="store-email"),
    dcc.Store(id="store-upload-status"),
    dcc.Store(id="store-upload-started"),
    dcc.Store(id="store-analysis-mode"),
    dcc.Store(id="store-progress", data=0),
    dcc.Interval(id="progress-interval", interval=350, n_intervals=0, disabled=True),
], style={"display":"none"})

# ------------------ Layout ------------------
app.layout = html.Div([
    sidebar(),
    _global_stores,                    # <— keep the stores global
    html.Div(id="page-content", style=content_style)
])

# ------------------ Router ------------------
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page_content(pathname):
    page = (pathname or "/").strip("/").lower()
    if page in ("", "home"): return page_home()
    if page == "documentation": return page_documentation()
    if page == "login": return page_login()
    if page == "upload": return page_upload()
    if page == "safetyscreening": return page_safety()
    if page == "dairyadaptation": return page_dairy()
    if page == "antibacterial": return page_abx()
    if page == "antifungal": return page_af()
    if page == "results": return page_results()
    if page == "aboutus": return page_about()
    if page == "contact": return page_contact()
    if page == "cite": return page_cite()
    return html.Div([html.H2("🔍 Page not found")], style={"padding": "30px"})

# ------------------ Register all callbacks ------------------
login_callbacks(app)
upload_callbacks(app)
safety_callbacks(app)
dairy_callbacks(app)
abx_callbacks(app)
af_callbacks(app)
results_callbacks(app)
contact_callbacks(app)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", "8050")), debug=False)

