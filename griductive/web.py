"""Browser UI authored entirely in Python with Dash components/callbacks.

Matches the Desktop Alto's Odyssey x Reigns Lineless Paper-Cut Vector UI 1:1:
- Full-screen edge-to-edge card grid over the flat-vector sky/hills/poppies SVG
- Single ultra-minimal top HUD bar (Griductive · Case ⌄ | 3/9 | 💡 Gợi ý | ☰)
- 30% Left Portrait Arch (ice-blue silhouette when unopened, vibrant green/coral
  when solved) + 70% Right spacious multi-line clue area (no "Lời khai" label)
- Flush Reigns-style 50/50 bottom split verdict bar on the selected suspect
- Exact original highlight rules (bold colored words + segmented region borders)
"""
import base64
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from html import unescape

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from flask import Flask, Response, abort, send_file

from .engine import PuzzleError, SolverTimeout, clue_parts
from .presentation.references import reference_focus
from .presentation.wording_vi import clue_html, clue_text
from .vector_art import PORTRAIT_COUNT, portrait_svg, profession_svg
from .web_game import ROOT, new_session, puzzle_options, restore, transition

INK = '#0B192C'
MUTED = '#52637A'
SELECTED = '#1D4ED8'
OPERAND_A = '#0284C7'
OPERAND_B = '#7C3AED'
ANCHOR = '#D97706'
INNOCENT = '#2CC26B'
CRIMINAL = '#EE505E'

ROLE_COLORS = {'result': SELECTED, 'a': OPERAND_A, 'b': OPERAND_B, 'anchor': ANCHOR}
STATUS = {'CRIMINAL': 'Tội phạm', 'INNOCENT': 'Vô tội'}
IMAGE_FILES = {'backdrop.svg', 'sprites.png', 'sprites-silhouette.png', 'pixel-desk.png', 'pixel-profession-props.png'}


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


@lru_cache(maxsize=512)
def _svg_uri(svg: str) -> str:
    encoded = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    return f'data:image/svg+xml;base64,{encoded}'


CHARACTER_CATEGORIES = {
    '0': 'medical', '1': 'painting', '2': 'journalism', '3': 'law', '4': 'academic',
    '5': 'cooking', '6': 'library', '7': 'mechanics', '8': 'gardening', '9': 'photography',
    '10': 'architecture', '11': 'watchmaking', '12': 'musician', '13': 'firefighting', '14': 'floristry',
    '15': 'tailoring', '16': 'aviation', '17': 'baking', '18': 'detective', '19': 'engineering',
    '20': 'bookselling', '21': 'nursing', '22': 'sailing', '23': 'music_teaching', '24': 'botany',
}


def _character_categories():
    return CHARACTER_CATEGORIES


def _portrait_url(portrait, silhouette=False):
    kind = 'silhouette' if silhouette else 'portrait'
    return f'/images/{kind}-{portrait % PORTRAIT_COUNT}.svg?v=2'


def portrait_arch(portrait, status=None, is_selected=False, compact=False):
    silhouette = (status is None and not is_selected)
    if status == 'INNOCENT':
        panel_bg, arch_bg = '#DCF9E8', '#2CC26B'
    elif status == 'CRIMINAL':
        panel_bg, arch_bg = '#FFE4E8', '#EE505E'
    elif is_selected:
        panel_bg, arch_bg = '#DCEBFE', '#99C2F6'
    else:
        panel_bg, arch_bg = 'transparent', '#D6E9FA'

    return html.Div(
        html.Div(
            html.Img(
                src=_portrait_url(portrait, silhouette),
                alt=STATUS.get(status, 'Chưa xác định'),
                style={
                    'width': 'min(118cqw, 100cqh)', 'height': 'auto',
                    'display': 'block', 'flexShrink': 0,
                    'pointerEvents': 'none', 'userSelect': 'none',
                },
            ),
            style={
                'width': '100%', 'height': '100%', 'background': arch_bg,
                'borderRadius': '999px 999px 0 0',
                'display': 'flex', 'alignItems': 'flex-end', 'justifyContent': 'center',
                'overflow': 'hidden', 'containerType': 'size',
            },
        ),
        style={
            'width': '100%', 'height': '100%',
            'background': panel_bg,
            'padding': '9px 6px 0' if compact else '14px 10px 0',
            'boxSizing': 'border-box',
            'display': 'flex', 'alignItems': 'stretch', 'position': 'relative',
        },
    )


def inline_clue_nodes(spec, board, registry, names, cell, pinned_key):
    """Exact old-version pill-free bold colored links inside the active card."""
    rendered = clue_html(spec, board, registry, WEB_PAPER_THEME, names)
    nodes = []
    cursor = 0
    idx = 0
    for match in _LINK_RE.finditer(rendered):
        if match.start() > cursor:
            nodes.append(unescape(rendered[cursor:match.start()]))
        key, color, raw_label = match.group(1), match.group(2), unescape(match.group(3))
        is_pinned = key == pinned_key
        nodes.append(html.Button(
            raw_label,
            id={'kind': 'region', 'key': key, 'idx': f'{cell}-{idx}'},
            n_clicks=0,
            style={
                'display': 'inline', 'padding': '0 2px', 'margin': 0,
                'border': 0, 'borderRadius': '3px',
                'background': '#EFF6FF' if is_pinned else 'transparent',
                'color': color, 'fontWeight': 700, 'fontSize': 'inherit',
                'fontFamily': 'inherit', 'lineHeight': 'inherit', 'cursor': 'pointer',
            },
        ))
        cursor = match.end()
        idx += 1
    if cursor < len(rendered):
        nodes.append(unescape(rendered[cursor:]))
    return nodes


def render_board(public, registry, session):
    size = public.board.size
    selected = session.get('selected')
    active = selected if selected in public.clues else None
    parts = (
        {part.key: part for part in clue_parts(public.clues[active], public.board, registry)}
        if active else {}
    )
    pinned = session.get('focus') if session.get('focus') in parts else None
    focus = reference_focus(parts, active, pinned, pinned)
    names = {person.cell: person.name for person in public.characters}
    categories = _character_categories()
    compact = size == 5

    coord_pill = {
        'background': 'rgba(255, 255, 255, 0.30)', 'color': '#0D2744',
        'border': 'none', 'borderRadius': '9px',
        'fontSize': '15px', 'fontWeight': 800,
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
    }

    items = [html.Div()]  # empty top-left corner
    for col in range(size):
        items.append(html.Div(chr(65 + col), style=coord_pill | {'height': '28px'}))

    by_cell = {p.cell: p for p in public.characters}
    for row in range(size):
        items.append(html.Div(str(row + 1), style=coord_pill | {'width': '32px'}))
        for col in range(size):
            cell = f'{chr(65 + col)}{row + 1}'
            person = by_cell[cell]
            status = public.statuses.get(cell)
            is_sel = cell == selected
            roles = focus.roles(cell)
            is_anchor = cell in focus.anchors
            dimmed = bool(active and cell not in focus.focused)

            shadow_parts = ['0 4px 12px rgba(16, 74, 142, 0.18)']
            if is_sel:
                border_css = f'3.5px solid {SELECTED}'
            elif roles:
                border_css = f'4.5px solid {ROLE_COLORS[roles[0]]}'
                if len(roles) > 1:
                    shadow_parts.insert(0, f'inset 0 0 0 3.5px {ROLE_COLORS[roles[1]]}')
            elif is_anchor:
                border_css = f'3.5px solid {ANCHOR}'
            else:
                rim = '#A7E8C3' if status == 'INNOCENT' else '#FECDD3' if status == 'CRIMINAL' else '#D5E6F7'
                border_css = f'1.5px solid {rim}'

            chip_bg = (
                '#27A860' if status == 'INNOCENT'
                else '#E44555' if status == 'CRIMINAL'
                else SELECTED if is_sel
                else '#83A3C4'
            )
            name_color = ROLE_COLORS.get(focus.named.get(cell), INK)

            # Circular check/cross badge ONLY on solved cards (NO '?' on unopened!)
            status_mark = html.Span(
                '✓' if status == 'INNOCENT' else '✕',
                title=STATUS[status],
                style={
                    'marginLeft': 'auto', 'width': '22px', 'height': '22px',
                    'borderRadius': '50%', 'flexShrink': 0,
                    'background': INNOCENT if status == 'INNOCENT' else CRIMINAL,
                    'color': '#FFFFFF', 'fontSize': '12px', 'fontWeight': 800,
                    'display': 'inline-flex', 'alignItems': 'center', 'justifyContent': 'center',
                },
            ) if status else None

            if cell in public.clues:
                clue_len = len(clue_text(public.clues[cell], public.board, registry, names))
                clue_fs = (
                    'clamp(13px, 0.98vw, 16px)' if compact
                    else ('clamp(16px, 1.18vw, 20.5px)' if clue_len > 125 else 'clamp(17px, 1.32vw, 23px)')
                )
                right_body = html.Div(
                    inline_clue_nodes(public.clues[cell], public.board, registry, names, cell, pinned)
                    if cell == active
                    else clue_text(public.clues[cell], public.board, registry, names),
                    style={
                        'position': 'relative', 'zIndex': 2 if cell == active else 0,
                        'flex': '1 1 auto', 'marginTop': '8px',
                        'fontSize': clue_fs, 'fontWeight': 500,
                        'lineHeight': '1.42', 'color': '#1E293B',
                        'overflowY': 'auto',
                    },
                )
            else:
                cat = categories.get(str(person.portrait), 'detective')
                prop_img = None if is_sel else html.Img(
                    src=_svg_uri(profession_svg(cat, '#C4DCF5')),
                    alt='',
                    **{'aria-hidden': 'true'},
                    style={
                        'width': 'clamp(42px, 3.6vw, 66px)' if compact else 'clamp(64px, 5.6vw, 108px)',
                        'height': 'clamp(42px, 3.6vw, 66px)' if compact else 'clamp(64px, 5.6vw, 108px)',
                        'marginLeft': 'auto', 'marginTop': 'auto',
                        'marginRight': '10px', 'marginBottom': '10px',
                        'opacity': 0.92,
                        'pointerEvents': 'none',
                    },
                )
                verdict_bar = html.Div([
                    html.Button(
                        '✓ Vô tội',
                        id={'kind': 'card-verdict', 'cell': cell, 'verdict': 'INNOCENT'},
                        n_clicks=0,
                        style={
                            'flex': '1 1 50%', 'padding': '10px 6px' if compact else '15px 8px', 'border': 0,
                            'borderRadius': 0,
                            'background': '#45CF80', 'color': '#FFFFFF',
                            'fontWeight': 700, 'fontSize': 'clamp(13px, 1.05vw, 18.5px)', 'cursor': 'pointer',
                        },
                    ),
                    html.Button(
                        '✕ Tội phạm',
                        id={'kind': 'card-verdict', 'cell': cell, 'verdict': 'CRIMINAL'},
                        n_clicks=0,
                        style={
                            'flex': '1 1 50%', 'padding': '10px 6px' if compact else '15px 8px', 'border': 0,
                            'borderRadius': '0 0 9px 0',
                            'background': '#F9616E', 'color': '#FFFFFF',
                            'fontWeight': 700, 'fontSize': 'clamp(13px, 1.05vw, 18.5px)', 'cursor': 'pointer',
                        },
                    ),
                ], style={
                    'position': 'relative', 'zIndex': 3, 'display': 'flex',
                    'marginTop': 'auto', 'marginLeft': '-18px',
                }) if is_sel else None

                right_body = html.Div(
                    [el for el in (prop_img, verdict_bar) if el is not None],
                    style={'flex': '1 1 auto', 'display': 'flex', 'flexDirection': 'column'},
                )

            card = html.Div([
                html.Button(
                    '',
                    id={'kind': 'card', 'cell': cell},
                    n_clicks=0,
                    **{'aria-label': f'{person.name} ({cell}), {STATUS.get(status, "chưa xác định")}'},
                    style={
                        'position': 'absolute', 'inset': 0, 'width': '100%', 'height': '100%',
                        'background': 'transparent', 'border': 0, 'padding': 0,
                        'cursor': 'pointer', 'zIndex': 1, 'borderRadius': '12px',
                    },
                ),
                # Left 38.5%: Responsive Full-Height Tinted Panel + Semicircular Dome Arch
                html.Div([
                    portrait_arch(person.portrait, status, is_sel, compact),
                    html.Span(cell, style={
                        'position': 'absolute', 'top': '10px', 'left': '10px',
                        'background': chip_bg, 'color': '#FFFFFF',
                        'borderRadius': '7px', 'padding': '3px 9px',
                        'fontSize': 'clamp(12px, 0.95vw, 16px)', 'fontWeight': 700, 'lineHeight': '1.3',
                    }),
                ], style={
                    'position': 'relative', 'width': '38.5%', 'flexShrink': 0,
                    'display': 'flex', 'alignItems': 'stretch',
                }),
                # Right 61.5%: Scaled Bold Name, Profession, Divider & Adaptive Clue
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div(person.name, style={
                                'fontSize': 'clamp(16px, 1.28vw, 22px)' if compact else 'clamp(22px, 1.85vw, 33px)',
                                'fontWeight': 800, 'color': name_color, 'lineHeight': '1.15',
                            }),
                            html.Div(person.profession, style={
                                'fontSize': 'clamp(11.5px, 0.9vw, 15px)' if compact else 'clamp(14px, 1.12vw, 19.5px)',
                                'color': MUTED, 'fontWeight': 500, 'marginTop': '2px',
                            }),
                        ], style={'minWidth': 0}),
                        status_mark,
                    ], style={
                        'display': 'flex', 'alignItems': 'flex-start', 'gap': '6px',
                        'paddingRight': '12px', 'paddingTop': '12px', 'paddingBottom': '8px',
                        'borderBottom': '1.5px solid #EBF2FA',
                    }),
                    html.Div(right_body, style={
                        'flex': '1 1 auto', 'display': 'flex', 'flexDirection': 'column',
                        'paddingRight': '0' if (is_sel and cell not in public.clues) else '14px',
                        'paddingBottom': '0' if (is_sel and cell not in public.clues) else '12px',
                    }),
                ], style={
                    'flex': '1 1 auto', 'minWidth': 0, 'paddingLeft': '18px',
                    'display': 'flex', 'flexDirection': 'column',
                }),
            ], style={
                'position': 'relative', 'display': 'flex', 'gap': 0,
                'padding': 0, 'borderRadius': '12px', 'background': '#FFFFFF',
                'overflow': 'hidden',
                'border': border_css, 'boxShadow': ', '.join(shadow_parts),
                'opacity': 0.28 if dimmed else 1.0,
                'transform': 'scale(1.03)' if is_sel else 'none',
                'zIndex': 4 if is_sel else 1,
                'transition': 'transform 0.14s ease, opacity 0.14s ease',
                'boxSizing': 'border-box', 'minHeight': '122px' if compact else '186px',
            })
            items.append(card)

    return html.Div(items, style={
        'flex': '1 1 auto', 'display': 'grid',
        'gridTemplateColumns': f'32px repeat({size}, minmax({"165px" if compact else "220px"}, 1fr))',
        'gridTemplateRows': f'28px repeat({size}, 1fr)',
        'gap': '10px 11px' if compact else '13px 14px', 'alignItems': 'stretch',
    })


def render_journal(engine):
    public = engine.public_state()
    names = {person.cell: person.name for person in public.characters}
    if not engine.trace:
        return html.P(
            'Chưa có bước suy luận. Chọn Bước tiếp hoặc Chạy tự động để xem từng phán quyết.',
            style={'color': MUTED, 'fontSize': '13.5px', 'padding': '14px 8px', 'margin': 0},
        )
    entries = []
    for entry in engine.trace:
        is_crim = entry['verdict'] == 'CRIMINAL'
        v_color = CRIMINAL if is_crim else '#1E9E5A'
        person = next(p for p in public.characters if p.cell == entry['cell'])
        queries = []
        for query in entry['queries']:
            assumptions = []
            for literal in query['assumptions']:
                cell = public.board.cells[abs(literal) - 1]
                assumptions.append(f'{names[cell]} ({cell}) là {STATUS["CRIMINAL" if literal > 0 else "INNOCENT"]}')
            q_label = 'Giả sử ' + ', '.join(assumptions) if assumptions else 'Dữ kiện đã mở'
            q_res = 'Nhất quán (SAT)' if query['result'] == 'SAT' else 'Mâu thuẫn (UNSAT)'
            queries.append(html.Li(f'{q_label} → {q_res}', style={'marginBottom': '4px'}))
        entries.append(html.Details([
            html.Summary([
                html.Span(f"{entry['step']:02d}", style={
                    'color': SELECTED, 'fontWeight': 700, 'fontSize': '13px', 'width': '22px',
                }),
                html.Img(
                    src=_portrait_url(person.portrait),
                    alt='',
                    style={
                        'width': '38px', 'height': '38px', 'borderRadius': '50%', 'flexShrink': 0,
                        'backgroundColor': CRIMINAL if is_crim else INNOCENT,
                    },
                ),
                html.Div([
                    html.Div([
                        html.Strong(names[entry['cell']], style={'fontSize': '15px', 'color': INK}),
                        html.Span(entry['cell'], style={
                            'fontSize': '11px', 'background': '#83A3C4', 'color': '#FFFFFF',
                            'padding': '1px 5px', 'borderRadius': '4px', 'marginLeft': '6px',
                            'fontWeight': 700,
                        }),
                    ]),
                    html.Div(STATUS[entry['verdict']], style={'color': v_color, 'fontSize': '12.5px', 'fontWeight': 700}),
                ], style={'flex': '1 1 auto'}),
                html.Span('Chi tiết ▾', style={'fontSize': '11.5px', 'color': SELECTED, 'fontWeight': 600}),
            ], style={
                'display': 'flex', 'alignItems': 'center', 'gap': '9px',
                'cursor': 'pointer', 'listStyle': 'none',
            }),
            html.Div([
                html.Div(
                    clue_text(entry['new_clue_content'], public.board, engine.registry, names),
                    style={'fontSize': '13px', 'lineHeight': '1.45', 'marginBottom': '6px', 'color': INK},
                ),
                html.Div(
                    'Lời khai trước đó: ' + ', '.join(entry['active_clues']),
                    style={'fontSize': '11.5px', 'color': MUTED, 'marginBottom': '6px'},
                ),
                html.Ul(queries, style={
                    'paddingLeft': '18px', 'margin': '0 0 6px', 'fontSize': '12px', 'lineHeight': '1.45',
                }),
                html.Div(
                    f"KB: {entry['primary_variables']} biến chính, "
                    f"{entry['auxiliary_variables']} biến phụ, {entry['clauses']} mệnh đề.",
                    style={'fontSize': '11.5px', 'color': MUTED},
                ),
            ], style={'marginTop': '10px', 'paddingTop': '8px', 'borderTop': '1px solid #E2E8F0'}),
        ], style={
            'background': '#FFFFFF', 'border': '1px solid #E2E8F0',
            'borderRadius': '9px', 'padding': '10px 12px', 'marginBottom': '8px',
        }))
    return entries


def layout():
    session = dict(new_session(), journal_open=False, menu_open=False)
    return html.Main([
        dcc.Store(id='session', storage_type='session', data=session),
        dcc.Interval(id='clock', interval=2500, disabled=True),
        dcc.Download(id='download'),

        # Single Ultra-Minimal Top HUD Bar (NO bottom bar!)
        html.Header([
            html.Div([
                html.Span('Griductive', style={
                    'fontSize': '26px', 'fontWeight': 800, 'color': '#FFFFFF', 'letterSpacing': '-0.3px',
                }),
                html.Span('•', style={'color': 'rgba(255,255,255,0.75)', 'fontSize': '18px'}),
                html.Div(
                    dcc.Dropdown(
                        id='puzzle', options=puzzle_options(), value=session['puzzle'],
                        clearable=False, searchable=False,
                        style={'minWidth': '250px', 'color': INK, 'fontSize': '14px', 'fontWeight': 600},
                    ),
                ),
                html.Span(id='puzzle-title', style={'display': 'none'}),
                html.Span(id='detail', style={'display': 'none'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'flexWrap': 'wrap'}),

            # Subtle inline toast notice in top bar only when needed
            dcc.Loading(
                html.Div(id='notice', role='status', style={
                    'color': '#FFFFFF', 'fontSize': '13px', 'fontWeight': 600,
                    'background': 'rgba(15, 23, 42, 0.28)', 'padding': '4px 12px',
                    'borderRadius': '14px',
                }),
                delay_show=250,
            ),

            html.Div([
                html.Div(id='progress', style={
                    'background': 'rgba(255, 255, 255, 0.24)', 'color': '#FFFFFF',
                    'border': '1.5px solid rgba(255, 255, 255, 0.50)', 'borderRadius': '16px',
                    'padding': '5px 14px', 'fontSize': '14px', 'fontWeight': 700,
                }),
                html.Button('💡 Gợi ý', id='hint', n_clicks=0, style={
                    'background': '#FFFFFF', 'color': '#0F2942', 'border': 0,
                    'borderRadius': '17px', 'padding': '6px 16px',
                    'fontSize': '14px', 'fontWeight': 700, 'cursor': 'pointer',
                    'boxShadow': '0 2px 8px rgba(15, 41, 66, 0.15)',
                }),
                html.Div([
                    html.Button('☰', id='menu-toggle', n_clicks=0, title='Công cụ', style={
                        'width': '36px', 'height': '36px', 'borderRadius': '10px',
                        'background': 'rgba(255, 255, 255, 0.22)', 'color': '#FFFFFF',
                        'border': '1.5px solid rgba(255, 255, 255, 0.45)',
                        'fontSize': '18px', 'fontWeight': 700, 'cursor': 'pointer',
                    }),
                    html.Div([
                        html.Button('Nhật ký & Tự động giải', id='journal-toggle', n_clicks=0, style={
                            'width': '100%', 'textAlign': 'left', 'padding': '8px 12px',
                            'border': 0, 'borderRadius': '6px', 'background': 'transparent',
                            'color': INK, 'fontSize': '13.5px', 'fontWeight': 600, 'cursor': 'pointer',
                        }),
                        html.Button('Làm lại màn này', id='restart', n_clicks=0, style={
                            'width': '100%', 'textAlign': 'left', 'padding': '8px 12px',
                            'border': 0, 'borderRadius': '6px', 'background': 'transparent',
                            'color': INK, 'fontSize': '13.5px', 'fontWeight': 600, 'cursor': 'pointer',
                        }),
                        dcc.Upload(
                            id='upload',
                            children=html.Div('Mở tệp JSON…', style={
                                'padding': '8px 12px', 'borderRadius': '6px',
                                'color': INK, 'fontSize': '13.5px', 'fontWeight': 600, 'cursor': 'pointer',
                            }),
                            accept='.json,application/json',
                            multiple=False,
                        ),
                    ], id='menu-popup', style={
                        'display': 'none', 'position': 'absolute', 'right': 0, 'top': '44px',
                        'width': '210px', 'background': '#FFFFFF', 'border': '1px solid #CBD5E1',
                        'borderRadius': '10px', 'padding': '6px', 'zIndex': 30,
                        'boxShadow': '0 10px 25px rgba(15, 23, 42, 0.18)',
                    }),
                ], style={'position': 'relative'}),
                # Hidden compatibility triggers
                html.Button(id='innocent', n_clicks=0, style={'display': 'none'}),
                html.Button(id='criminal', n_clicks=0, style={'display': 'none'}),
                html.Button(id='clear', n_clicks=0, style={'display': 'none'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
        ], style={
            'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
            'gap': '12px', 'flexWrap': 'wrap', 'marginBottom': '8px',
        }),

        # Full-Screen Edge-to-Edge Board + Collapsible Right Solver Journal
        html.Fieldset([
            html.Div([
                html.Section(
                    html.Div(id='board', style={'height': '100%', 'display': 'flex', 'flexDirection': 'column'}),
                    style={'flex': '1 1 640px', 'minWidth': 0, 'display': 'flex', 'flexDirection': 'column'},
                ),
                html.Aside([
                    html.Div([
                        html.H2('Nhật ký suy luận', style={'fontSize': '19px', 'fontWeight': 800, 'margin': 0}),
                        html.Button('✕', id='journal-close', n_clicks=0, title='Đóng', style={
                            'background': 'transparent', 'border': 0, 'color': MUTED,
                            'fontSize': '16px', 'cursor': 'pointer', 'padding': '2px 6px',
                        }),
                    ], style={
                        'padding': '12px 16px', 'borderBottom': '1px solid #E2E8F0',
                        'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                    }),
                    html.Div([
                        html.Div([
                            html.Button('Chạy tự động', id='auto', n_clicks=0, style={
                                'flex': '1 1 0', 'padding': '8px 10px', 'borderRadius': '8px',
                                'border': 0, 'background': SELECTED, 'color': '#FFFFFF',
                                'fontWeight': 700, 'fontSize': '13px', 'cursor': 'pointer',
                            }),
                            html.Button('Bước tiếp', id='step', n_clicks=0, style={
                                'flex': '1 1 0', 'padding': '8px 10px', 'borderRadius': '8px',
                                'border': '1.5px solid #CBD5E1', 'background': '#FFFFFF',
                                'color': INK, 'fontWeight': 700, 'fontSize': '13px', 'cursor': 'pointer',
                            }),
                        ], style={'display': 'flex', 'gap': '8px', 'marginBottom': '10px'}),
                        html.Div(id='journal', style={
                            'background': '#F1F5F9', 'borderRadius': '9px', 'padding': '8px',
                            'maxHeight': 'calc(100vh - 220px)', 'overflowY': 'auto',
                        }),
                        html.Div([
                            html.Button('Xuất JSON', id='export', n_clicks=0, style={
                                'marginLeft': 'auto', 'padding': '5px 10px', 'fontSize': '12px',
                                'fontWeight': 600, 'borderRadius': '6px', 'border': '1px solid #CBD5E1',
                                'background': '#FFFFFF', 'color': SELECTED, 'cursor': 'pointer',
                            }),
                        ], style={'display': 'flex', 'marginTop': '10px'}),
                    ], style={'padding': '14px'}),
                ], id='journal-panel', style={'display': 'none'}),
            ], style={'flex': '1 1 auto', 'display': 'flex', 'gap': '14px', 'alignItems': 'stretch'}),
        ], id='controls', style={
            'flex': '1 1 auto', 'display': 'flex', 'flexDirection': 'column',
            'border': 0, 'padding': 0, 'margin': 0,
        }),
    ], style={
        'minHeight': '100vh', 'boxSizing': 'border-box', 'padding': '10px 32px 28px',
        'display': 'flex', 'flexDirection': 'column',
        'fontFamily': '"Segoe UI", Inter, Arial, sans-serif', 'color': INK,
        'backgroundImage': 'url("/images/backdrop.svg")', 'backgroundSize': 'cover',
        'backgroundPosition': 'center bottom',
        'backgroundRepeat': 'no-repeat', 'backgroundColor': '#2A84E5',
    })


def create_app():
    server = Flask(__name__, static_folder=None)
    server.config['MAX_CONTENT_LENGTH'] = 2_000_000

    @server.get('/health')
    def health():
        return {'status': 'ok'}

    @server.get('/images/<name>')
    def image(name):
        m = re.fullmatch(r'(portrait|silhouette)-([0-9]{1,2})\.svg', name)
        if m:
            idx = int(m.group(2))
            if idx < PORTRAIT_COUNT:
                return Response(
                    portrait_svg(idx, silhouette=m.group(1) == 'silhouette'),
                    mimetype='image/svg+xml',
                    headers={'Cache-Control': 'public, max-age=86400'},
                )
        if name not in IMAGE_FILES:
            abort(404)
        path = ROOT / 'public/images' / name
        if not path.is_file():
            abort(404)
        return send_file(path, conditional=True, max_age=86400)

    dashboard = Dash(
        __name__, server=server, title='Griductive',
        assets_folder=str(ROOT / 'public'), include_assets_files=False,
        meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
        suppress_callback_exceptions=True, update_title='Đang suy luận…',
    )
    dashboard.layout = layout

    @dashboard.callback(
        Output('session', 'data'), Output('board', 'children'), Output('detail', 'children'),
        Output('journal', 'children'), Output('progress', 'children'), Output('notice', 'children'),
        Output('auto', 'children'), Output('clock', 'disabled'),
        Output('innocent', 'disabled'), Output('criminal', 'disabled'), Output('download', 'data'),
        Output('puzzle-title', 'children'), Output('puzzle', 'options'), Output('puzzle', 'value'),
        Output('journal-panel', 'style'), Output('menu-popup', 'style'),
        Input('puzzle', 'value'), Input('upload', 'contents'), Input('restart', 'n_clicks'),
        Input('hint', 'n_clicks'), Input('step', 'n_clicks'), Input('auto', 'n_clicks'),
        Input('innocent', 'n_clicks'), Input('criminal', 'n_clicks'),
        Input('clear', 'n_clicks'), Input('export', 'n_clicks'), Input('clock', 'n_intervals'),
        Input('menu-toggle', 'n_clicks'), Input('journal-toggle', 'n_clicks'), Input('journal-close', 'n_clicks'),
        Input({'kind': 'card', 'cell': ALL}, 'n_clicks'),
        Input({'kind': 'card-verdict', 'cell': ALL, 'verdict': ALL}, 'n_clicks'),
        Input({'kind': 'region', 'key': ALL, 'idx': ALL}, 'n_clicks'),
        State('session', 'data'),
        running=[(Output('controls', 'disabled'), True, False)],
    )
    def update(puzzle, upload, restart, hint, step, auto, innocent, criminal,
               clear, export, ticks, menu_toggle, journal_toggle, journal_close,
               cards, card_verdicts, regions, session):
        trigger = ctx.triggered_id
        session = session if isinstance(session, dict) else new_session()
        journal_open = bool(session.get('journal_open', False))
        menu_open = bool(session.get('menu_open', False))
        action, payload = None, None

        if isinstance(trigger, dict):
            menu_open = False
            kind = trigger.get('kind')
            if kind == 'card':
                if not any(cards):
                    raise PreventUpdate
                action, payload = 'select', trigger['cell']
            elif kind == 'card-verdict':
                if not any(card_verdicts):
                    raise PreventUpdate
                session = dict(session, selected=trigger['cell'])
                action, payload = 'verdict', trigger['verdict']
            else:
                if not any(regions):
                    raise PreventUpdate
                action, payload = 'focus', trigger['key']
        elif trigger == 'menu-toggle':
            menu_open = not menu_open
        elif trigger == 'journal-toggle':
            journal_open = not journal_open
            menu_open = False
        elif trigger == 'journal-close':
            journal_open = False
            menu_open = False
            action = 'pause_if_running'
        elif trigger == 'puzzle':
            if puzzle != session.get('puzzle'):
                action, payload = 'load', puzzle
                journal_open = False
                menu_open = False
        elif trigger == 'upload' and upload:
            action, payload = 'upload', upload
            journal_open = False
            menu_open = False
        elif trigger == 'restart':
            action = 'restart'
            journal_open = False
            menu_open = False
        elif trigger in ('innocent', 'criminal'):
            action, payload = 'verdict', trigger.upper()
            menu_open = False
        elif trigger == 'clock':
            if not session.get('running'):
                raise PreventUpdate
            action = 'tick'
        elif trigger:
            action = trigger
            menu_open = False
            if trigger in ('step', 'auto'):
                journal_open = True

        download = no_update
        try:
            if action == 'pause_if_running':
                engine = restore(session)
                updated = dict(session, running=False)
            else:
                updated, engine = transition(session, action, payload)
                if action == 'export':
                    download = dcc.send_string(
                        json.dumps(engine.trace, ensure_ascii=False, indent=2),
                        'griductive-trace.json',
                    )
        except (PuzzleError, SolverTimeout, ValueError, TypeError) as exc:
            try:
                engine = restore(session)
                updated = dict(session, running=False, notice=str(exc))
            except (PuzzleError, SolverTimeout, ValueError, TypeError):
                updated = new_session()
                engine = restore(updated)
                updated['notice'] = str(exc)

        updated['journal_open'] = journal_open
        updated['menu_open'] = menu_open
        public = engine.public_state()
        selected = updated.get('selected')
        disabled = selected not in public.board.cells or selected in public.statuses
        options = puzzle_options()
        if updated.get('custom'):
            options.append({'label': public.title + ' (JSON)', 'value': 'custom'})

        panel_style = {
            'display': 'block' if journal_open else 'none',
            'flex': '0 0 365px', 'width': '365px', 'maxWidth': '100%',
            'background': '#FFFFFF', 'border': '1.5px solid #CBD5E1',
            'borderRadius': '12px', 'boxSizing': 'border-box',
            'boxShadow': '0 8px 24px rgba(15, 41, 66, 0.18)',
        }
        popup_style = {
            'display': 'block' if menu_open else 'none',
            'position': 'absolute', 'right': 0, 'top': '44px',
            'width': '210px', 'background': '#FFFFFF', 'border': '1px solid #CBD5E1',
            'borderRadius': '10px', 'padding': '6px', 'zIndex': 30,
            'boxShadow': '0 10px 25px rgba(15, 23, 42, 0.18)',
        }
        return (
            updated, render_board(public, engine.registry, updated),
            '', render_journal(engine),
            f'{len(public.statuses)}/{len(public.board.cells)}', updated['notice'],
            'Tạm dừng' if updated.get('running') else 'Chạy tự động', not updated.get('running'),
            disabled, disabled, download, public.title, options, updated['puzzle'],
            panel_style, popup_style,
        )

    server.extensions['griductive_dash'] = dashboard
    return server
