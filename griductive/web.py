"""Browser UI authored entirely in Python with Dash components/callbacks.

No handwritten HTML templates, JavaScript callbacks or CSS files. Dash owns
browser rendering; every game decision still runs in the existing Python engine.
"""
import json
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from flask import Flask, abort, send_file

from .engine import PuzzleError, SolverTimeout, clue_parts
from .presentation.references import reference_focus
from .presentation.wording_vi import clue_text
from .web_game import ROOT, new_session, puzzle_options, restore, transition

INK = '#28576F'
PAPER = '#FFF7E8'
MUTED = '#736F68'
BLUE = '#287DB6'
PURPLE = '#9C45BE'
GREEN = '#3F7F59'
RED = '#AF5145'
ROLE_COLORS = {'result': BLUE, 'a': BLUE, 'b': PURPLE, 'anchor': '#BC810C'}
STATUS = {'CRIMINAL': 'Tội phạm', 'INNOCENT': 'Vô tội'}
BUTTON = {'padding': '10px 15px', 'border': f'2px solid {INK}',
          'borderRadius': '9px', 'background': PAPER, 'color': INK,
          'fontSize': '14px', 'fontWeight': 600, 'cursor': 'pointer'}
PANEL = {'padding': '18px', 'border': '3px solid #817D75', 'borderRadius': '12px',
         'background': PAPER, 'boxSizing': 'border-box'}
IMAGE_FILES = {'sprites.png', 'pixel-desk.png', 'pixel-profession-props.png'}


def button(label, identifier, **style):
    return html.Button(label, id=identifier, n_clicks=0, style=BUTTON | style)


def sprite(portrait, status=None, size=80):
    frame = {None: 0, 'INNOCENT': 4, 'CRIMINAL': 6}[status]
    return html.Div(role='img', **{'aria-label': STATUS.get(status, 'Chưa xác định')},
        style={'width': f'{size}px', 'height': f'{size}px', 'flexShrink': 0,
               'backgroundImage': 'url(/images/sprites.png)',
               'backgroundSize': '700% 2500%',
               'backgroundPosition': f'{frame * 100 / 6}% {portrait * 100 / 24}%',
               'imageRendering': 'pixelated'})


def render_board(public, registry, session):
    selected = session.get('selected')
    active = selected if selected in public.clues else None
    parts = {part.key: part for part in clue_parts(public.clues[active], public.board, registry)} if active else {}
    pinned = session.get('focus') if session.get('focus') in parts else None
    focus = reference_focus(parts, active, pinned, pinned)
    names = {person.cell: person.name for person in public.characters}
    cards = []
    for person in public.characters:
        cell = person.cell
        status = public.statuses.get(cell)
        color = GREEN if status == 'INNOCENT' else RED if status else '#817D75'
        roles = focus.roles(cell)
        border = ROLE_COLORS[roles[0]] if roles else color
        if cell == selected:
            border = BLUE
        name_color = ROLE_COLORS.get(focus.named.get(cell), '#302D29')
        clue = clue_text(public.clues[cell], public.board, registry, names) if cell in public.clues else 'Lời khai chưa mở'
        card_style = {
            'display': 'flex', 'flexDirection': 'column', 'gap': '8px',
            'width': '100%', 'height': '100%', 'minHeight': '182px',
            'padding': '10px', 'border': f'{4 if roles or cell == selected else 3}px solid {border}',
            'borderRadius': '11px', 'textAlign': 'left', 'fontFamily': 'inherit',
            'background': '#F2F4ED' if status == 'INNOCENT' else '#F8EFEA' if status else '#FAF8F2',
            'cursor': 'pointer', 'boxSizing': 'border-box',
            'opacity': .40 if active and cell not in focus.focused else 1,
            'boxShadow': f'4px 4px 0 {PURPLE}' if len(roles) > 1 else 'none',
        }
        cards.append(html.Button([
            html.Div([
                html.Span(cell, style={'border': '1px solid #817D75', 'borderRadius': '5px',
                                      'padding': '2px 6px', 'fontSize': '12px'}),
                html.Strong(person.name, style={'fontSize': '18px', 'color': name_color}),
                html.Span('✓' if status == 'INNOCENT' else '▥' if status else '?',
                          title=STATUS.get(status, 'Chưa xác định'),
                          style={'color': color, 'fontSize': '20px', 'marginLeft': 'auto'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '7px'}),
            html.Div([
                sprite(person.portrait, status, 64 if public.board.size == 5 else 80),
                html.Div([
                    html.Div(person.profession, style={'fontSize': '12px', 'color': MUTED, 'marginBottom': '6px'}),
                    html.Div(clue, style={'fontSize': '13px', 'lineHeight': '1.45',
                                          'maxHeight': '110px', 'overflowY': 'auto',
                                          'color': '#302D29' if status else MUTED}),
                ], style={'minWidth': 0}),
            ], style={'display': 'flex', 'gap': '7px', 'alignItems': 'center'}),
        ], id={'kind': 'card', 'cell': cell}, n_clicks=0, style=card_style,
            **{'aria-label': f'{person.name} ({cell}), {STATUS.get(status, "chưa xác định")}'}))
    return html.Div(cards, style={
        'display': 'grid', 'gridTemplateColumns': f'repeat({public.board.size}, minmax(150px, 1fr))',
        'gap': '10px', 'padding': '4px 6px 8px 0',
    })


def render_detail(public, registry, session):
    selected = session.get('selected')
    person = next((person for person in public.characters if person.cell == selected), None)
    if person is None:
        return [html.H2('Theo dấu lời khai', style={'fontFamily': 'Georgia, serif', 'marginTop': 0}),
                html.P('Chọn một thẻ trên bàn để xem nhân vật và lời khai.', style={'lineHeight': '1.6'}),
                html.P('Mọi lời khai đều đúng. Chỉ mở thẻ khi có thể chứng minh trạng thái.',
                       style={'fontSize': '13px', 'color': MUTED, 'lineHeight': '1.6'})]
    names = {person.cell: person.name for person in public.characters}
    status = public.statuses.get(selected)
    content = [
        html.Div([sprite(person.portrait, status, 104), html.Div([
            html.H2(f'{person.name} ({selected})', style={'margin': '0 0 5px', 'fontFamily': 'Georgia, serif'}),
            html.Div(person.profession, style={'color': MUTED}),
            html.P(STATUS.get(status, 'Chưa xác định'),
                   style={'color': GREEN if status == 'INNOCENT' else RED if status else INK, 'fontWeight': 600}),
        ])], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
    ]
    if selected in public.clues:
        spec = public.clues[selected]
        content.extend([
            html.P(clue_text(spec, public.board, registry, names), style={'lineHeight': '1.65'}),
            html.P('Chọn vùng để đối chiếu trên bàn:', style={'fontSize': '12px', 'color': MUTED}),
        ])
        parts = [part for part in clue_parts(spec, public.board, registry)
                 if part.is_region or part.named_cells]
        content.append(html.Div([
            button(part.title, {'kind': 'region', 'key': part.key},
                   color=ROLE_COLORS.get(part.role, INK), fontSize='12px', padding='6px 9px',
                   background='#F6D39C' if part.key == session.get('focus') else PAPER)
            for part in parts
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '6px'}))
    else:
        content.append(html.P('Lời khai được giữ kín đến khi phán quyết được chứng minh.',
                              style={'lineHeight': '1.6', 'color': MUTED}))
    return content


def render_journal(engine):
    public = engine.public_state()
    names = {person.cell: person.name for person in public.characters}
    if not engine.trace:
        return html.P('Các bước đã chứng minh sẽ xuất hiện ở đây.', style={'color': MUTED, 'fontSize': '13px'})
    entries = []
    for entry in reversed(engine.trace):
        queries = []
        for query in entry['queries']:
            assumptions = []
            for literal in query['assumptions']:
                cell = public.board.cells[abs(literal) - 1]
                assumptions.append(f'{names[cell]} ({cell}) là {STATUS["CRIMINAL" if literal > 0 else "INNOCENT"]}')
            label = 'Giả sử ' + ', '.join(assumptions) if assumptions else 'Kiểm tra dữ kiện đã mở'
            queries.append(html.Li(f'{label}: {query["result"]}', style={'marginBottom': '6px'}))
        entries.append(html.Details([
            html.Summary(f'{entry["step"]}. {names[entry["cell"]]} ({entry["cell"]}): {STATUS[entry["verdict"]]}',
                         style={'cursor': 'pointer', 'fontWeight': 600}),
            html.P(clue_text(entry['new_clue_content'], public.board, engine.registry, names),
                   style={'fontSize': '13px', 'lineHeight': '1.5'}),
            html.Div('Clue đang có: ' + ', '.join(entry['active_clues']), style={'fontSize': '12px', 'color': MUTED}),
            html.Ul(queries, style={'paddingLeft': '18px', 'fontSize': '12px', 'lineHeight': '1.5'}),
        ], style={'padding': '12px 0', 'borderBottom': '1px solid #D7CDBD'}))
    return entries


def layout():
    session = new_session()
    return html.Main([
        dcc.Store(id='session', storage_type='session', data=session),
        dcc.Interval(id='clock', interval=2500, disabled=True),
        dcc.Download(id='download'),
        html.Div([
            html.Header([
                html.Div([
                    html.H1('Griductive', style={'fontFamily': 'Georgia, serif', 'fontSize': '36px', 'margin': 0}),
                    html.Div(id='puzzle-title', style={'fontSize': '15px', 'marginTop': '5px', 'color': MUTED}),
                ]),
                html.Div(id='progress', style={'background': '#F6C789', 'padding': '12px 18px',
                                              'border': f'2px solid {INK}', 'borderRadius': '16px',
                                              'fontWeight': 600}),
            ], style=PANEL | {'display': 'flex', 'justifyContent': 'space-between', 'gap': '15px',
                              'alignItems': 'center', 'flexWrap': 'wrap', 'marginBottom': '15px'}),
            html.Fieldset([
                html.Div([
                    dcc.Dropdown(id='puzzle', options=puzzle_options(), value=session['puzzle'],
                                 clearable=False, searchable=False,
                                 style={'minWidth': '260px', 'flex': '1 1 280px', 'color': '#302D29'}),
                    dcc.Upload(id='upload', children=button('Mở JSON', 'upload-button'),
                               accept='.json,application/json', multiple=False),
                    button('Làm lại', 'restart'), button('Gợi ý', 'hint'),
                    button('Một bước', 'step'), button('Tự động giải', 'auto', background=INK, color=PAPER),
                ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '9px', 'alignItems': 'center'}),
                html.Div([
                    button('✓ Vô tội', 'innocent', color=GREEN),
                    button('▥ Tội phạm', 'criminal', color=RED),
                    button('Bỏ chọn', 'clear', color=MUTED, fontSize='12px'),
                ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '8px', 'marginTop': '10px'}),
            ], id='controls', style={'border': 0, 'padding': 0, 'margin': '0 0 12px'}),
            dcc.Loading(html.Div(id='notice', role='status', style={
                'minHeight': '24px', 'padding': '9px 12px', 'marginBottom': '12px',
                'background': '#FFF7E8E8', 'borderRadius': '8px', 'lineHeight': '1.5',
            }), delay_show=250),
            html.Div([
                html.Section(html.Div(id='board'), style={'flex': '1 1 500px', 'minWidth': 0,
                                                         'overflowX': 'auto'}),
                html.Aside([
                    html.Div(id='detail'),
                    html.H3('Nhật ký suy luận', style={'fontFamily': 'Georgia, serif', 'marginTop': '24px'}),
                    button('Tải nhật ký JSON', 'export', fontSize='12px', padding='7px 10px'),
                    html.Div(id='journal', style={'maxHeight': '440px', 'overflowY': 'auto', 'marginTop': '10px'}),
                ], style=PANEL | {'flex': '1 1 260px', 'maxWidth': '360px'}),
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '16px', 'alignItems': 'flex-start'}),
        ], style={'maxWidth': '1540px', 'margin': '0 auto'}),
    ], style={'minHeight': '100vh', 'boxSizing': 'border-box', 'padding': '20px',
              'fontFamily': 'Segoe UI, Arial, sans-serif', 'color': INK,
              'backgroundColor': '#DCEFF6', 'backgroundImage': 'url(/images/pixel-desk.png)',
              'backgroundSize': 'cover', 'backgroundPosition': 'center', 'backgroundAttachment': 'fixed'})


def create_app():
    server = Flask(__name__, static_folder=None)
    server.config['MAX_CONTENT_LENGTH'] = 2_000_000

    @server.get('/health')
    def health():
        return {'status': 'ok'}

    @server.get('/images/<name>')
    def image(name):
        if name not in IMAGE_FILES:
            abort(404)
        path = ROOT / 'public/images' / name
        if not path.is_file():
            abort(404)
        return send_file(path, conditional=True, max_age=86400)

    dashboard = Dash(__name__, server=server, title='Griductive — Phố biển',
                     assets_folder=str(ROOT / 'public'), include_assets_files=False,
                     meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
                     suppress_callback_exceptions=True, update_title='Đang suy luận…')
    dashboard.layout = layout

    @dashboard.callback(
        Output('session', 'data'), Output('board', 'children'), Output('detail', 'children'),
        Output('journal', 'children'), Output('progress', 'children'), Output('notice', 'children'),
        Output('auto', 'children'), Output('clock', 'disabled'),
        Output('innocent', 'disabled'), Output('criminal', 'disabled'), Output('download', 'data'),
        Output('puzzle-title', 'children'), Output('puzzle', 'options'), Output('puzzle', 'value'),
        Input('puzzle', 'value'), Input('upload', 'contents'), Input('restart', 'n_clicks'),
        Input('hint', 'n_clicks'), Input('step', 'n_clicks'), Input('auto', 'n_clicks'),
        Input('innocent', 'n_clicks'), Input('criminal', 'n_clicks'),
        Input('clear', 'n_clicks'), Input('export', 'n_clicks'), Input('clock', 'n_intervals'),
        Input({'kind': 'card', 'cell': ALL}, 'n_clicks'),
        Input({'kind': 'region', 'key': ALL}, 'n_clicks'), State('session', 'data'),
        running=[(Output('controls', 'disabled'), True, False)],
    )
    def update(puzzle, upload, restart, hint, step, auto, innocent, criminal,
               clear, export, ticks, cards, regions, session):
        trigger = ctx.triggered_id
        session = session if isinstance(session, dict) else new_session()
        action, payload = None, None
        if isinstance(trigger, dict):
            if trigger.get('kind') == 'card':
                if not any(cards):
                    raise PreventUpdate
                action, payload = 'select', trigger['cell']
            else:
                if not any(regions):
                    raise PreventUpdate
                action, payload = 'focus', trigger['key']
        elif trigger == 'puzzle':
            if puzzle != session.get('puzzle'):
                action, payload = 'load', puzzle
        elif trigger == 'upload' and upload:
            action, payload = 'upload', upload
        elif trigger in ('innocent', 'criminal'):
            action, payload = 'verdict', trigger.upper()
        elif trigger == 'clock':
            if not session.get('running'):
                raise PreventUpdate
            action = 'tick'
        elif trigger:
            action = trigger
        download = no_update
        try:
            updated, engine = transition(session, action, payload)
            if action == 'export':
                download = dcc.send_string(json.dumps(engine.trace, ensure_ascii=False, indent=2),
                                           'griductive-trace.json')
        except (PuzzleError, SolverTimeout, ValueError, TypeError) as exc:
            try:
                engine = restore(session)
                updated = dict(session, running=False, notice=str(exc))
            except (PuzzleError, SolverTimeout, ValueError, TypeError):
                updated = new_session()
                engine = restore(updated)
                updated['notice'] = str(exc)
        public = engine.public_state()
        selected = updated.get('selected')
        disabled = selected not in public.board.cells or selected in public.statuses
        options = puzzle_options()
        if updated.get('custom'):
            options.append({'label': public.title + ' (JSON)', 'value': 'custom'})
        return (
            updated, render_board(public, engine.registry, updated),
            render_detail(public, engine.registry, updated), render_journal(engine),
            f'Tiến độ: {len(public.statuses)}/{len(public.board.cells)}', updated['notice'],
            'Tạm dừng' if updated.get('running') else 'Tự động giải', not updated.get('running'),
            disabled, disabled, download, public.title, options, updated['puzzle'],
        )

    server.extensions['griductive_dash'] = dashboard
    return server
