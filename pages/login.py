# pages/login.py
import os
import json
from pathlib import Path
from datetime import datetime

from dash import dcc, html, Input, Output, State, no_update
from itsdangerous import URLSafeSerializer

from utils.emailer import send_email_many  # uses SMTP_* env vars

# ---------------- Config & constants ----------------
USERS_DB = Path("assets/users.db.json")

EMAIL_VERIFY_SECRET = os.environ.get("EMAIL_VERIFY_SECRET", "change-me-please")
VERIFY_SALT = "email-verify"
serializer = URLSafeSerializer(EMAIL_VERIFY_SECRET, salt=VERIFY_SALT)

# public base URL for building the verify link
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8050")

# who to notify when a new user registers (env configurable)
ADMIN_EMAILS = [
    e.strip() for e in os.environ.get(
        "ADMIN_EMAILS",
        "afaroo04@uoguelph.ca,adeelsway@gmail.com"
    ).split(",") if e.strip()
]

# ---------------- Persistence helpers ----------------
def _load():
    if USERS_DB.exists():
        try:
            return json.loads(USERS_DB.read_text())
        except Exception:
            pass
    return {"users": []}

def _save(d):
    USERS_DB.parent.mkdir(parents=True, exist_ok=True)
    USERS_DB.write_text(json.dumps(d, indent=2))

def _find_user(db, email):
    for u in db.get("users", []):
        if u.get("email", "").lower() == str(email or "").lower():
            return u
    return None

# ---------------- UI ----------------
def page_login():
    return html.Div([
        html.H2("🔐 Sign In / Register"),

        html.Div([
            # Existing user (left)
            html.Div([
                html.H3("Existing User"),
                dcc.Input(id="login-email", type="email", placeholder="email@example.com",
                          style={"width": "100%", "marginBottom": "8px"}),
                dcc.Input(id="login-name", type="text", placeholder="Your name",
                          style={"width": "100%", "marginBottom": "8px"}),
                dcc.Input(id="login-password", type="password", placeholder="Password (not validated; demo)",
                          style={"width": "100%", "marginBottom": "8px"}),

                html.Div([
                    html.Button("Sign In", id="btn-login", n_clicks=0),
                    html.Button("Get Verify Link", id="btn-show-verify-login", n_clicks=0,
                                title="If your email isn’t arriving, click to get an instant verify link.",
                                style={"marginLeft": "10px", "background": "white",
                                       "border": "1px solid #cfd8ea", "borderRadius": "6px",
                                       "padding": "6px 10px", "cursor": "pointer"})
                ], style={"display": "flex", "alignItems": "center"}),

                html.Div(id="login-msg", style={"marginTop": "8px", "color": "#555"}),
                html.Div(id="inline-verify-login", style={"marginTop": "6px"})
            ], style={"flex": "1", "paddingRight": "20px", "borderRight": "1px dashed #ccc"}),

            # New user (right)
            html.Div([
                html.H3("New User"),
                dcc.Input(id="reg-email", type="email", placeholder="email@example.com",
                          style={"width": "100%", "marginBottom": "8px"}),
                dcc.Input(id="reg-name", type="text", placeholder="Your name",
                          style={"width": "100%", "marginBottom": "8px"}),
                dcc.Input(id="reg-password", type="password", placeholder="Set password (demo only)",
                          style={"width": "100%", "marginBottom": "8px"}),

                html.Div([
                    html.Button("Register", id="btn-register", n_clicks=0),
                    html.Button("Get Verify Link", id="btn-show-verify", n_clicks=0,
                                title="If email delivery is off, click to generate your verify link here.",
                                style={"marginLeft": "10px", "background": "white",
                                       "border": "1px solid #cfd8ea", "borderRadius": "6px",
                                       "padding": "6px 10px", "cursor": "pointer"})
                ], style={"display": "flex", "alignItems": "center"}),

                html.Div("We’ll email you a verification link. If email is unavailable, use the button to get the link here.",
                         style={"marginTop": "8px", "color": "#555"}),
                html.Div(id="inline-verify", style={"marginTop": "6px"}),
                html.Div(id="register-msg", style={"marginTop": "8px", "color": "#555"})
            ], style={"flex": "1", "paddingLeft": "20px"})
        ], style={"display": "flex", "gap": "20px"})
    ])

# ---------------- Callbacks ----------------
def register_callbacks(app):
    # --- Registration flow (unchanged email flow; improved fallback message kept) ---
    @app.callback(
        Output("register-msg", "children"),
        Input("btn-register", "n_clicks"),
        State("reg-email", "value"),
        State("reg-name", "value"),
        prevent_initial_call=True
    )
    def register_user(n, email, name):
        if not email:
            return "Please enter an email."

        db = _load()

        # already registered?
        u = _find_user(db, email)
        if u:
            if not u.get("approved", False):
                token = serializer.dumps(email)
                verify_link = f"{BASE_URL}/verify/{token}"
                subject = "Verify your DairyBioControl account (reminder)"
                body = f"""Hello {name or u.get('name','')},

You (or someone using your email) tried to register at DairyBioControl.

Please click the link below to verify your email and activate your account:
{verify_link}

If you didn't request this, you can ignore this email.

— DairyBioControl
"""
                status_resend = send_email_many([email], subject, body)
                if (status_resend.startswith("SMTP not configured")
                    or status_resend.startswith("SMTP disabled")
                    or status_resend.startswith("Email send failed")):
                    return html.Div([
                        html.Div("Email could not be sent. Use the button “Get Verify Link” to verify now.",
                                 style={"marginBottom":"6px", "color":"#a33"}),
                        html.A("Or click this link now", href=verify_link, target="_blank",
                               style={"fontWeight":"600"})
                    ])
                return "Already registered but not verified. We re-sent the verification email."
            return "Email already registered. Please sign in."

        # new user
        user = {"email": email, "name": name or "", "approved": False, "role": "user"}
        db["users"].append(user)
        _save(db)

        token = serializer.dumps(email)
        verify_link = f"{BASE_URL}/verify/{token}"

        subject_user = "Verify your DairyBioControl account"
        body_user = f"""Hello {name or ''},

Thanks for registering with DairyBioControl.
Please click the link below to verify your email and activate your account:

{verify_link}

If you didn't request this, you can ignore this email.

— DairyBioControl
"""
        status_user = send_email_many([email], subject_user, body_user)

        # notify admins (best-effort)
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        subject_admin = "New DairyBioControl Registration"
        body_admin = f"""A new user just registered:

Email: {email}
Name:  {name or '(none)'}
When:  {ts}

Status: verification email sent to user.
"""
        status_admin = send_email_many(ADMIN_EMAILS, subject_admin, body_admin)

        if (status_user.startswith("SMTP not configured")
            or status_user.startswith("SMTP disabled")
            or status_user.startswith("Email send failed")):
            return html.Div([
                html.Div("Email could not be sent. Click “Get Verify Link” to verify now.",
                         style={"marginBottom":"6px", "color":"#a33"}),
                html.A("Or click this link now", href=verify_link, target="_blank",
                       style={"fontWeight":"600"})
            ])

        msg = "Verification email sent. Please check your inbox and click the link."
        if status_admin.startswith("SMTP not configured") or status_admin.startswith("SMTP disabled"):
            msg += " (Admin notification not sent; SMTP is not configured.)"
        elif status_admin.startswith("Email send failed"):
            msg += f" (Admin notify error: {status_admin})"
        return msg

    # --- Manual verify link (Registration panel) ---
    @app.callback(
        Output("inline-verify", "children"),
        Input("btn-show-verify", "n_clicks"),
        State("reg-email", "value"),
        State("reg-name", "value"),
        prevent_initial_call=True
    )
    def show_verify_link(n, email, name):
        if not email:
            return html.Div("Enter an email above first.", style={"color":"#a33"})
        db = _load()
        u = _find_user(db, email)
        # if the user doesn't exist yet, create a pending record so verification works
        if not u:
            u = {"email": email, "name": name or "", "approved": False, "role": "user"}
            db["users"].append(u)
            _save(db)
        token = serializer.dumps(email)
        verify_link = f"{BASE_URL}/verify/{token}"
        return html.Div([
            html.Span("Instant verify link: ", style={"marginRight":"6px", "fontWeight":"600"}),
            html.A(verify_link, href=verify_link, target="_blank"),
            html.Div("Click the link to activate your account immediately.",
                     style={"fontSize":"13px","color":"#555","marginTop":"4px"})
        ])

    # --- Manual verify link (Existing user panel) ---
    @app.callback(
        Output("inline-verify-login", "children"),
        Input("btn-show-verify-login", "n_clicks"),
        State("login-email", "value"),
        State("login-name", "value"),
        prevent_initial_call=True
    )
    def show_verify_link_login(n, email, name):
        if not email:
            return html.Div("Enter your email above first.", style={"color":"#a33"})
        db = _load()
        u = _find_user(db, email)
        if not u:
            # create a pending record so user can still verify
            u = {"email": email, "name": name or "", "approved": False, "role": "user"}
            db["users"].append(u)
            _save(db)
        token = serializer.dumps(email)
        verify_link = f"{BASE_URL}/verify/{token}"
        return html.Div([
            html.Span("Instant verify link: ", style={"marginRight":"6px", "fontWeight":"600"}),
            html.A(verify_link, href=verify_link, target="_blank"),
            html.Div("Click to verify and then sign in.", style={"fontSize":"13px","color":"#555","marginTop":"4px"})
        ])

    # --- Sign-in (unchanged, but pairs nicely with the manual verify link) ---
    @app.callback(
        Output("login-msg", "children"),
        Output("store-auth", "data"),
        Input("btn-login", "n_clicks"),
        State("login-email", "value"),
        State("login-name", "value"),
        prevent_initial_call=True
    )
    def login_user(n, email, name):
        auth = {"logged_in": False, "approved": False, "email": "", "name": name or "", "role": "user"}
        if not email:
            return "Enter email.", auth

        db = _load()
        u = _find_user(db, email)
        if u:
            auth = {
                "logged_in": True,
                "approved": bool(u.get("approved", False)),
                "email": email,
                "name": name or u.get("name", ""),
                "role": u.get("role", "user"),
            }
            if auth["approved"]:
                return "Signed in. Approved ✅", auth
            else:
                return "Signed in. Please verify your email — use the “Get Verify Link” button.", auth

        return "Email not found. Please register.", auth

