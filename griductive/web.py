"""Browser UI and callbacks for Griductive."""

import json
import re
from uuid import uuid4
from dataclasses import dataclass
from html import unescape

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from flask import Flask, abort, send_file

from .engine import PuzzleError, SolverTimeout, clue_parts
from .presentation.references import reference_focus
from .presentation.wording_vi import clue_html, clue_text
from .web_game import ROOT, new_session, puzzle_options, restore, transition

INK = "#0B192C"
MUTED = "#52637A"
SELECTED = "#1D4ED8"
OPERAND_A = "#0284C7"
OPERAND_B = "#7C3AED"
ANCHOR = "#D97706"
INNOCENT = "#2CC26B"
CRIMINAL = "#EE505E"

ROLE_COLORS = {"result": SELECTED, "a": OPERAND_A, "b": OPERAND_B, "anchor": ANCHOR}
STATUS = {"CRIMINAL": "Tội phạm", "INNOCENT": "Vô tội"}
IMAGE_FILES = {
    "backdrop.svg",
    "sprites.png",
    "sprites-silhouette.png",
    "pixel-desk.png",
    "pixel-profession-props.png",
}


@dataclass(frozen=True)
class _WebPaperTheme:
    gold: str = SELECTED
    operand_a: str = OPERAND_A
    operand_b: str = OPERAND_B
    anchor: str = ANCHOR
    criminal: str = INK
    innocent: str = INK


WEB_PAPER_THEME = _WebPaperTheme()
_LINK_RE = re.compile(r'<a href="([^"]+)" style="color:([^;]+);[^"]*">(.*?)</a>')


CHARACTER_CATEGORIES = {
    "0": "medical",
    "1": "painting",
    "2": "journalism",
    "3": "law",
    "4": "academic",
    "5": "cooking",
    "6": "library",
    "7": "mechanics",
    "8": "gardening",
    "9": "photography",
    "10": "architecture",
    "11": "watchmaking",
    "12": "musician",
    "13": "firefighting",
    "14": "floristry",
    "15": "tailoring",
    "16": "aviation",
    "17": "baking",
    "18": "detective",
    "19": "engineering",
    "20": "bookselling",
    "21": "nursing",
    "22": "sailing",
    "23": "music_teaching",
    "24": "botany",
}


PORTRAIT_COUNT = len(CHARACTER_CATEGORIES)
IMAGE_FILES.update(
    f"profession-{category}.svg" for category in CHARACTER_CATEGORIES.values()
)


def sprite(person, frame=0, muted=False):
    columns = 2 if muted else 7
    sheet = "sprites-muted" if muted else "sprites"
    return html.Span(
        className="sprite",
        style={
            "backgroundImage": f'url("/pixel/{sheet}.png")',
            "backgroundSize": f"{columns * 100}% 2500%",
            "backgroundPositionY": f"{person.portrait / 24 * 100}%",
            "--pose": f"{frame / (columns - 1) * 100}%",
            "--blink": f"{(3 if frame == 4 else 1) / (columns - 1) * 100}%",
            "--reaction": f"{(2 if frame == 0 and not muted else 5 if frame == 6 else 3 if frame == 4 else 0) / (columns - 1) * 100}%",
            "--delay": f"{-person.portrait * 0.731}s",
        },
    )


def glyph(name):
    names = (
        "check",
        "cross",
        "hint",
        "warning",
        "step",
        "export",
        "pause",
        "play",
        "restart",
        "chevron",
    )
    return html.Span(
        className="glyph",
        style={"--glyph": f"{names.index(name) / 9 * 100}%"},
        **{"aria-hidden": "true"},
    )


def inline_clue_nodes(spec, board, registry, names, cell, pinned_key):
    """Exact old-version pill-free bold colored links inside the active card."""
    rendered = clue_html(spec, board, registry, WEB_PAPER_THEME, names)
    nodes = []
    cursor = 0
    idx = 0
    for match in _LINK_RE.finditer(rendered):
        if match.start() > cursor:
            nodes.append(unescape(rendered[cursor : match.start()]))
        key, color, raw_label = match.group(1), match.group(2), unescape(match.group(3))
        is_pinned = key == pinned_key
        nodes.append(
            html.Button(
                raw_label,
                id={"kind": "region", "key": key, "idx": f"{cell}-{idx}"},
                n_clicks=0,
                style={
                    "display": "inline",
                    "padding": "0 2px",
                    "margin": 0,
                    "border": 0,
                    "borderRadius": "3px",
                    "background": "#EFF6FF" if is_pinned else "transparent",
                    "color": color,
                    "fontWeight": 700,
                    "fontSize": "inherit",
                    "fontFamily": "inherit",
                    "lineHeight": "inherit",
                    "cursor": "pointer",
                },
            )
        )
        cursor = match.end()
        idx += 1
    if cursor < len(rendered):
        nodes.append(unescape(rendered[cursor:]))
    return nodes


def render_board(public, registry, session):
    size = public.board.size
    selected = session.get("selected")
    active = selected if selected in public.clues else None
    parts = (
        {
            part.key: part
            for part in clue_parts(public.clues[active], public.board, registry)
        }
        if active
        else {}
    )
    pinned = session.get("focus") if session.get("focus") in parts else None
    focus = reference_focus(parts, active, pinned, pinned)
    names = {person.cell: person.name for person in public.characters}
    items = [html.Div()]
    items.extend(html.Div(chr(65 + c), className="coordinate") for c in range(size))
    by_cell = {p.cell: p for p in public.characters}
    for row in range(1, size + 1):
        items.append(html.Div(str(row), className="coordinate"))
        for col in range(size):
            cell = f"{chr(65 + col)}{row}"
            person = by_cell[cell]
            status = public.statuses.get(cell)
            chosen = cell == selected
            roles = focus.roles(cell)
            css = {}
            if roles and not chosen:
                css["--rim"] = ROLE_COLORS[roles[0]]
                css["--edge"] = "6px"
                if len(roles) > 1:
                    css["--rim-fill"] = (
                        f"conic-gradient({ROLE_COLORS[roles[0]]} 50%, {ROLE_COLORS[roles[1]]} 0)"
                    )
            elif cell in focus.anchors and not chosen:
                css["--rim"] = ANCHOR
            if active and cell not in focus.focused:
                css["opacity"] = 0.28
            state = (status or "unknown").lower()
            frame = {"CRIMINAL": 6, "INNOCENT": 4}.get(status, 0)
            if cell in public.clues:
                nodes = (
                    inline_clue_nodes(
                        public.clues[cell], public.board, registry, names, cell, pinned
                    )
                    if cell == active
                    else clue_text(public.clues[cell], public.board, registry, names)
                )
                body = html.Div(nodes, className="statement")
            elif chosen:
                body = html.Div(
                    [
                        html.Button(
                            [glyph(mark), STATUS[key]],
                            id={"kind": "card-verdict", "cell": cell, "verdict": key},
                            n_clicks=0,
                            className="key verdict " + key.lower(),
                        )
                        for key, mark in [("INNOCENT", "check"), ("CRIMINAL", "cross")]
                    ],
                    className="verdicts",
                )
            else:
                index = person.portrait
                body = html.Div(
                    className="prop",
                    style={
                        "backgroundPosition": f"{(index % 5) * 25}% {(index // 5) * 25}%"
                    },
                )
            panel = html.Div(
                [
                    sprite(person, frame, not status and not chosen),
                    html.Div([html.I() for _ in range(4)], className="bars")
                    if status == "CRIMINAL"
                    else None,
                    html.Span(cell, className="chip"),
                ],
                className="portrait",
            )
            info = html.Div(
                [
                    html.Strong(
                        person.name,
                        style={"color": ROLE_COLORS.get(focus.named.get(cell), INK)},
                    ),
                    html.Small(person.profession),
                    body,
                ],
                className="info",
            )
            mark = (
                html.Span(
                    glyph("check" if status == "INNOCENT" else "cross"),
                    className="mark",
                    title=STATUS[status],
                )
                if status
                else None
            )
            items.append(
                html.Div(
                    html.Article(
                        [
                            panel,
                            info,
                            mark,
                            html.Button(
                                id={"kind": "card", "cell": cell},
                                n_clicks=0,
                                className="card-hit",
                                **{
                                    "aria-label": f"{person.name} ({cell}), {STATUS.get(status, 'chưa xác định')}"
                                },
                            ),
                        ],
                        className="card " + state + (" chosen" if chosen else ""),
                        style=css,
                        **{"data-cell": cell},
                    ),
                    className="slot",
                )
            )
    return html.Div(items, className="grid", style={"--n": size})


def render_journal(engine):
    public = engine.public_state()
    names = {person.cell: person.name for person in public.characters}
    if not engine.trace:
        return html.Div(
            [
                "Chưa có bước suy luận.",
                html.P("Chạy tự động hoặc chọn Bước tiếp để xem từng phán quyết."),
            ],
            className="empty-entry",
        )
    entries = []
    sources = {
        spec["id"]: f"{names[cell]} ({cell})" for cell, spec in public.clues.items()
    }
    people = {p.cell: p for p in public.characters}
    for entry in engine.trace:
        cell = entry["cell"]
        person = people[cell]
        verdict = entry["verdict"]
        queries = []
        for query in entry["queries"]:
            assumptions = []
            for literal in query["assumptions"]:
                target = public.board.cells[abs(literal) - 1]
                assumptions.append(
                    f"{names[target]} ({target}) là {STATUS['CRIMINAL' if literal > 0 else 'INNOCENT']}"
                )
            condition = (
                "Giả sử " + ", ".join(assumptions) if assumptions else "Dữ kiện đã mở"
            )
            result = (
                "Nhất quán (SAT)" if query["result"] == "SAT" else "Mâu thuẫn (UNSAT)"
            )
            queries.append(html.Div([condition, html.Br(), result]))
        entries.append(
            html.Article(
                [
                    html.Header(
                        [
                            html.B(f"{entry['step']:02d}"),
                            html.Div(sprite(person), className="journal-portrait"),
                            html.Div(
                                [
                                    html.Strong(person.name),
                                    html.Small(cell),
                                    html.Div(
                                        [
                                            glyph(
                                                "cross"
                                                if verdict == "CRIMINAL"
                                                else "check"
                                            ),
                                            STATUS[verdict],
                                        ],
                                        className=verdict.lower(),
                                    ),
                                ]
                            ),
                        ]
                    ),
                    html.Details(
                        [
                            html.Summary(
                                [
                                    f"Đã mở lời khai của {person.name}",
                                    html.B("Chi tiết"),
                                ]
                            ),
                            html.H4(f"Lời khai của {person.name} ({cell})"),
                            clue_text(
                                entry["new_clue_content"],
                                public.board,
                                engine.registry,
                                names,
                            ),
                            html.H4("Lời khai có trước bước này"),
                            html.Div(
                                [
                                    html.Div(sources.get(i, i))
                                    for i in entry["active_clues"]
                                ]
                            ),
                            html.H4("Kiểm chứng"),
                            *queries,
                            html.P(
                                f"KB trước bước này: {entry['primary_variables']} biến chính, {entry['auxiliary_variables']} biến phụ, {entry['clauses']} mệnh đề."
                            ),
                        ]
                    ),
                ],
                className="entry",
            )
        )
    return entries


def layout():
    session = new_session()
    options = puzzle_options()
    return html.Main(
        [
            dcc.Store(id="session", storage_type="session", data=session),
            dcc.Interval(id="clock", interval=650, disabled=True),
            dcc.Download(id="download"),
            html.Div(
                [
                    dcc.Dropdown(id="puzzle", options=options, value=session["puzzle"]),
                    dcc.Upload(id="upload"),
                    html.Div(id="detail"),
                    html.Div(id="progress"),
                    *[html.Button(id=i) for i in ("innocent", "criminal", "clear")],
                ],
                hidden=True,
            ),
            html.Div(
                [
                    html.Header(
                        [
                            html.B("Griductive", className="brand"),
                            html.Span("•"),
                            html.Details(
                                [
                                    html.Summary(
                                        [html.Span(id="puzzle-title"), glyph("chevron")]
                                    ),
                                    html.Div(
                                        [
                                            html.Button(
                                                o["label"],
                                                **{"data-puzzle": o["value"]},
                                            )
                                            for o in options
                                        ],
                                        className="case-list menu",
                                    ),
                                ],
                                id="cases",
                            ),
                            html.Div(className="spacer"),
                            html.Button(
                                [glyph("hint"), "Gợi ý"], id="hint", className="key hud"
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        html.Img(src="/pixel/gear.png", alt=""),
                                        id="menu-toggle",
                                        className="key hud",
                                        title="Menu chính",
                                        **{"aria-label": "Menu chính"},
                                    ),
                                    html.Div(
                                        [
                                            html.Button(
                                                [glyph("play"), "Tự động giải"],
                                                id="journal-toggle",
                                            ),
                                            html.Button(
                                                [glyph("restart"), "Làm lại màn này"],
                                                id="restart",
                                            ),
                                        ],
                                        id="menu-popup",
                                        className="menu",
                                        style={"display": "none"},
                                    ),
                                ],
                                className="tools",
                            ),
                        ]
                    ),
                    html.Fieldset(html.Div(id="board"), id="controls"),
                ],
                className="desk",
            ),
            html.Aside(
                [
                    html.Div(className="dock-grip", title="Kéo để đổi chiều rộng"),
                    html.Header(
                        [
                            html.B("Tự động giải"),
                            html.Button("×", id="journal-close", title="Đóng"),
                        ]
                    ),
                    html.Small(id="journal-case"),
                    html.Div(
                        [
                            html.Button(id="auto", className="key"),
                            html.Button(
                                [glyph("step"), "Bước tiếp"], id="step", className="key"
                            ),
                        ],
                        className="solver-controls",
                    ),
                    html.Div(id="solver-status"),
                    html.Div(id="journal"),
                    html.Button("Đến bước mới nhất ↓", id="latest", hidden=True),
                    html.Footer(
                        [
                            html.Details(
                                [html.Summary("Thông số KB"), html.Div(id="kb-stats")]
                            ),
                            html.Button([glyph("export"), "Xuất JSON"], id="export"),
                        ]
                    ),
                ],
                id="journal-panel",
                style={"display": "none"},
            ),
            html.Div(id="notice"),
        ],
        className="workspace",
    )


def notice_view(title, message, person=None):
    return html.Dialog(
        [
            html.Div(
                [
                    glyph("hint" if title == "Gợi ý" else "warning"),
                    html.B(title),
                    html.Button("×", className="dismiss", title="Đóng"),
                ],
                className="notice-heading",
            ),
            html.Div(
                [
                    html.Div(sprite(person), className="notice-portrait")
                    if person
                    else None,
                    html.Div(
                        [html.Strong(person.name) if person else None, html.P(message)]
                    ),
                ],
                className="notice-body",
            ),
            html.Button(
                "Xem nhân vật" if person else "Đã hiểu", className="key dismiss"
            ),
        ],
        className="notice-box",
        key=f"{title}-{message}-{uuid4().hex}",
    )


def create_app():
    server = Flask(__name__, static_folder=None)
    server.config["MAX_CONTENT_LENGTH"] = 2_000_000

    @server.get("/pixel/<name>")
    def pixel_asset(name):
        if name not in {
            "gear.png",
            "glyphs.png",
            "sprites.png",
            "sprites-muted.png",
            "harbor.png",
        }:
            abort(404)
        return send_file(ROOT / "public/pixel" / name, conditional=True, max_age=86400)

    @server.get("/board.css")
    def board_styles():
        return send_file(ROOT / "public/board.css", conditional=True)

    @server.get("/board.js")
    def board_events():
        return send_file(ROOT / "public/board.js", conditional=True)

    @server.get("/health")
    def health():
        return {"status": "ok"}

    @server.get("/images/<name>")
    def image(name):
        m = re.fullmatch(r"(portrait|silhouette)-([0-9]{1,2})\.svg", name)
        if m and int(m.group(2)) < PORTRAIT_COUNT:
            name = f"{m.group(1)}-{int(m.group(2))}.svg"
        elif name not in IMAGE_FILES:
            abort(404)
        path = ROOT / "public/images" / name
        if not path.is_file():
            abort(404)
        return send_file(path, conditional=True, max_age=86400)

    dashboard = Dash(
        __name__,
        server=server,
        title="Griductive",
        assets_folder=str(ROOT / "public"),
        include_assets_files=False,
        external_stylesheets=["/board.css"],
        external_scripts=["/board.js"],
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ],
        suppress_callback_exceptions=True,
        update_title="Đang suy luận…",
    )
    dashboard.layout = layout

    @dashboard.callback(
        Output("session", "data"),
        Output("board", "children"),
        Output("detail", "children"),
        Output("journal", "children"),
        Output("progress", "children"),
        Output("notice", "children"),
        Output("auto", "children"),
        Output("clock", "disabled"),
        Output("innocent", "disabled"),
        Output("criminal", "disabled"),
        Output("download", "data"),
        Output("puzzle-title", "children"),
        Output("puzzle", "options"),
        Output("puzzle", "value"),
        Output("journal-panel", "style"),
        Output("menu-popup", "style"),
        Output("journal-case", "children"),
        Output("solver-status", "children"),
        Output("kb-stats", "children"),
        Output("step", "disabled"),
        Output("auto", "disabled"),
        Output("export", "disabled"),
        Input("puzzle", "value"),
        Input("upload", "contents"),
        Input("restart", "n_clicks"),
        Input("hint", "n_clicks"),
        Input("step", "n_clicks"),
        Input("auto", "n_clicks"),
        Input("innocent", "n_clicks"),
        Input("criminal", "n_clicks"),
        Input("clear", "n_clicks"),
        Input("export", "n_clicks"),
        Input("clock", "n_intervals"),
        Input("menu-toggle", "n_clicks"),
        Input("journal-toggle", "n_clicks"),
        Input("journal-close", "n_clicks"),
        Input({"kind": "card", "cell": ALL}, "n_clicks"),
        Input({"kind": "card-verdict", "cell": ALL, "verdict": ALL}, "n_clicks"),
        Input({"kind": "region", "key": ALL, "idx": ALL}, "n_clicks"),
        State("session", "data"),
        running=[(Output("controls", "disabled"), True, False)],
    )
    def update(
        puzzle,
        upload,
        restart,
        hint,
        step,
        auto,
        innocent,
        criminal,
        clear,
        export,
        ticks,
        menu_toggle,
        journal_toggle,
        journal_close,
        cards,
        card_verdicts,
        regions,
        session,
    ):
        trigger = ctx.triggered_id
        session = session if isinstance(session, dict) else new_session()
        journal_open = bool(session.get("journal_open", False))
        menu_open = bool(session.get("menu_open", False))
        action, payload = None, None

        if isinstance(trigger, dict):
            menu_open = False
            kind = trigger.get("kind")
            if kind == "card":
                if not any(cards):
                    raise PreventUpdate
                action, payload = "select", trigger["cell"]
            elif kind == "card-verdict":
                if not any(card_verdicts):
                    raise PreventUpdate
                session = dict(session, selected=trigger["cell"])
                action, payload = "verdict", trigger["verdict"]
            else:
                if not any(regions):
                    raise PreventUpdate
                action, payload = "focus", trigger["key"]
        elif trigger == "menu-toggle":
            menu_open = not menu_open
        elif trigger == "journal-toggle":
            journal_open = not journal_open
            menu_open = False
        elif trigger == "journal-close":
            journal_open = False
            menu_open = False
            action = "pause_if_running"
        elif trigger == "puzzle":
            if puzzle != session.get("puzzle"):
                action, payload = "load", puzzle
                journal_open = False
                menu_open = False
        elif trigger == "upload" and upload:
            action, payload = "upload", upload
            journal_open = False
            menu_open = False
        elif trigger == "restart":
            action = "restart"
            journal_open = False
            menu_open = False
        elif trigger in ("innocent", "criminal"):
            action, payload = "verdict", trigger.upper()
            menu_open = False
        elif trigger == "clock":
            if not session.get("running"):
                raise PreventUpdate
            action = "tick"
        elif trigger:
            action = trigger
            menu_open = False
            if trigger in ("step", "auto"):
                journal_open = True

        download = no_update
        try:
            if action == "pause_if_running":
                engine = restore(session)
                updated = dict(session, running=False)
            else:
                updated, engine = transition(session, action, payload)
                if action == "export":
                    download = dcc.send_string(
                        json.dumps(engine.trace, ensure_ascii=False, indent=2),
                        "griductive-trace.json",
                    )
        except (PuzzleError, SolverTimeout, ValueError, TypeError) as exc:
            action = "error"
            try:
                engine = restore(session)
                updated = dict(session, running=False, notice=str(exc))
            except (PuzzleError, SolverTimeout, ValueError, TypeError):
                updated = new_session()
                engine = restore(updated)
                updated["notice"] = str(exc)

        updated["journal_open"] = journal_open
        updated["menu_open"] = menu_open
        public = engine.public_state()
        selected = updated.get("selected")
        disabled = selected not in public.board.cells or selected in public.statuses
        options = puzzle_options()
        if updated.get("custom"):
            options.append({"label": public.title + " (JSON)", "value": "custom"})

        panel_style = {"display": "flex" if journal_open else "none"}
        popup_style = {"display": "block" if menu_open else "none"}
        notice = None
        if action == "error":
            notice = notice_view("Suy luận", updated["notice"])
        elif action == "hint":
            person = (
                next((p for p in public.characters if p.cell == selected), None)
                if updated["notice"].startswith("Có thể chứng minh")
                else None
            )
            notice = notice_view(
                "Gợi ý",
                "Các lời khai đã mở đủ để xác định trạng thái của nhân vật này."
                if person
                else updated["notice"],
                person,
            )
        elif action in ("step", "tick", "verdict") and engine.solved:
            notice = notice_view(
                "Hoàn thành", "Đã chứng minh được trạng thái của tất cả nhân vật."
            )
        elif action == "verdict" and not updated["notice"].startswith("Đã chứng minh"):
            notice = notice_view("Phán quyết", updated["notice"])
        run_label = (
            "Tạm dừng"
            if updated.get("running")
            else "Chạy tiếp"
            if engine.trace
            else "Chạy tự động"
        )
        last = engine.trace[-1] if engine.trace else {}
        stats = (
            f"{last['primary_variables']} biến chính, {last['auxiliary_variables']} biến phụ, {last['clauses']} mệnh đề."
            if last
            else ""
        )
        return (
            updated,
            render_board(public, engine.registry, updated),
            "",
            render_journal(engine),
            f"{len(public.statuses)}/{len(public.board.cells)}",
            notice,
            [glyph("pause" if updated.get("running") else "play"), run_label],
            not updated.get("running"),
            disabled,
            disabled,
            download,
            public.title,
            options,
            updated["puzzle"],
            panel_style,
            popup_style,
            public.title,
            [
                html.B(
                    "Hoàn thành"
                    if engine.solved
                    else "Đang chạy"
                    if updated.get("running")
                    else "Đang xem từng bước"
                    if engine.trace
                    else "Sẵn sàng"
                ),
                html.Span(f"{len(engine.trace)} bước"),
            ],
            stats,
            bool(updated.get("running") or engine.solved),
            engine.solved,
            not bool(engine.trace),
        )

    server.extensions["griductive_dash"] = dashboard
    return server
