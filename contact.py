# pages/contact.py
from dash import html, dcc, Input, Output, State, no_update
from utils.emailer import send_email_many
import os

# You can keep hard-coded recipients, or read from env:
DESTINATIONS = [
    e.strip() for e in os.environ.get(
        "ADMIN_EMAILS",
        "afaroo04@uoguelph.ca,adeelsway@gmail.com"
    ).split(",") if e.strip()
]

CARD_STYLE = {
    "maxWidth": "720px",
    "margin": "20px auto",
    "background": "white",
    "border": "14px solid #f3a7b6",
    "borderRadius": "24px",
    "padding": "28px 32px 36px",
    "boxShadow": "0 6px 24px rgba(0,0,0,0.06)"
}
TITLE_STYLE = {"textAlign": "center","fontSize": "34px","color": "#ff9800","fontWeight": "800","letterSpacing": "1px","margin": "8px 0 18px"}
LABEL_STYLE = {"display": "block", "color": "#7a7a7a", "marginTop": "16px", "marginBottom": "3px"}
LINE_INPUT_STYLE = {
    "width":"100%","border":"none","borderBottom":"3px solid #f5a5b7",
    "outline":"none","padding":"10px 6px","fontSize":"16px","background":"transparent"
}
TEXTAREA_STYLE = {**LINE_INPUT_STYLE, "height":"160px","resize":"vertical"}
BTN_STYLE = {
    "display":"block","margin":"26px auto 0","padding":"14px 28px","borderRadius":"20px",
    "background":"white","border":"3px solid #f5a5b7","color":"#f5a5b7",
    "fontWeight":"800","letterSpacing":"1px","cursor":"pointer"
}

def page_contact():
    return html.Div([
        html.Div(style=CARD_STYLE, children=[
            html.Div("CONTACT US", style=TITLE_STYLE),

            html.Label("Your Email", style=LABEL_STYLE),
            dcc.Input(id="contact-email", type="email", placeholder="you@example.com", style=LINE_INPUT_STYLE),

            html.Label("Message", style=LABEL_STYLE),
            dcc.Textarea(id="contact-message", placeholder="Type your message…", style=TEXTAREA_STYLE),

            html.Button("SUBMIT", id="contact-submit", n_clicks=0, style=BTN_STYLE),
            html.Div(id="contact-status", style={"textAlign":"center","marginTop":"12px","color":"#666"})
        ])
    ])

def register_callbacks(app):
    @app.callback(
        Output("contact-status","children"),
        Input("contact-submit","n_clicks"),
        State("contact-email","value"),
        State("contact-message","value"),
        prevent_initial_call=True
    )
    def submit_contact(n, email, message):
        # 1) Ensure callback is firing
        print("[CONTACT] Click:", n, "Email:", email)

        if not n:
            return no_update

        email = (email or "").strip()
        message = (message or "").strip()

        # 2) Basic validation
        if not message:
            return "Please enter a message."
        if email and "@" not in email:
            return "Please enter a valid email address (or leave it blank)."

        # 3) Compose and send
        subject = "Contact Form Submission — DairyBioControl"
        body = "\n".join([
            "New DairyBioControl contact form submission:",
            f"From: {email or '(no email provided)'}",
            "",
            message
        ])

        # show immediate feedback while sending
        status_info = "Sending…"
        try:
            # You can use reply_to=email so you can hit Reply in your inbox.
            status = send_email_many(DESTINATIONS, subject, body, reply_to=email)
            print("[CONTACT] Mailer status:", status)  # debug in server log

            if status.startswith("Message sent"):
                return "✅ Thanks! Your message has been sent."
            if status.startswith("SMTP not configured") or status.startswith("SMTP disabled"):
                return "✉️ SMTP is not configured on the server; message not sent."
            if status.startswith("Email send failed"):
                return f"⚠️ {status}"
            # Any other unexpected text — still show to user
            return status or "Submitted."
        except Exception as e:
            print("[CONTACT] Exception:", e)
            return f"⚠️ Error: {e}"

