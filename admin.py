import json
from pathlib import Path
from dash import dcc, html, Input, Output, State, no_update, ALL

USERS_DB = Path("assets/users.db.json")
DEFAULT_ADMIN_CODE = "letmein"

def _load(): 
    if USERS_DB.exists():
        try: return json.loads(USERS_DB.read_text())
        except Exception: pass
    return {"users":[]}
def _save(d): USERS_DB.write_text(json.dumps(d, indent=2))

def page_admin():
    return html.Div([
        html.H2("🛡️ Admin Approval"),
        html.P("Enter admin code to view and approve users."),
        dcc.Input(id="admin-code", type="password", placeholder="Admin code", style={"width":"260px","marginRight":"10px"}),
        html.Button("Load Pending", id="btn-load-pending", n_clicks=0),
        html.Div(id="admin-msg", style={"marginTop":"10px","color":"#555"}),
        html.Div(id="pending-users", style={"marginTop":"16px"})
    ])

def register_callbacks(app):
    @app.callback(Output("pending-users","children"),
                  Output("admin-msg","children"),
                  Input("btn-load-pending","n_clicks"),
                  State("admin-code","value"),
                  prevent_initial_call=True)
    def admin_load_pending(n, code):
        if (code or "") != DEFAULT_ADMIN_CODE:
            return no_update, "Invalid admin code."
        db=_load()
        pend=[u for u in db["users"] if not u.get("approved",False)]
        if not pend: return html.Div("No pending users."), "Loaded."
        cards=[]
        for u in pend:
            cards.append(html.Div([
                html.Div([html.Strong(u.get("name") or "(no name)"), html.Span(f"  <{u['email']}>")]),
                html.Button(f"Approve {u['email']}", id={"type":"approve-user","email":u["email"]}, n_clicks=0)
            ], style={"border":"1px solid #ddd","padding":"8px","marginBottom":"6px","borderRadius":"6px"}))
        return html.Div(cards), "Loaded."

    @app.callback(Output("admin-msg","children", allow_duplicate=True),
                  Input({"type":"approve-user","email":ALL}, "n_clicks"),
                  State({"type":"approve-user","email":ALL}, "id"),
                  prevent_initial_call=True)
    def approve_selected(n_clicks_list, ids):
        if not n_clicks_list or not ids: return no_update
        db=_load(); changed=0
        for n, ident in zip(n_clicks_list, ids):
            if n:
                email=ident["email"]
                for u in db["users"]:
                    if u["email"].lower()==email.lower() and not u.get("approved",False):
                        u["approved"]=True; changed+=1
        if changed: _save(db); return f"Approved {changed} user(s). Reload."
        return "No changes."

