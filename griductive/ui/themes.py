"""Cozy Harbor x Coastal Detective palette and Qt stylesheet."""
from dataclasses import dataclass
from ..presentation.references import ANCHOR, OPERAND_A, OPERAND_B, SELECTED


@dataclass(frozen=True)
class Theme:
    name: str
    background: str
    surface: str
    text: str
    muted: str
    border: str
    gold: str
    selected: str
    anchor: str
    operand_a: str
    operand_b: str
    innocent: str
    criminal: str
    badge: str
    primary: str
    card_unknown: str
    card_innocent: str
    card_criminal: str


THEMES = {
    'pixel': Theme(
        'Bến cảng hoàng hôn',
        '#385064',  # harbor dusk slate
        '#FFFDF9',  # warm seashell ivory surface
        '#142536',  # deep harbor navy ink
        '#5B6E82',  # soft coastal slate subtitle
        '#D8CDBB',  # warm driftwood sand rim
        '#16324F',  # deep nautical accent
        SELECTED,
        ANCHOR,
        OPERAND_A,
        OPERAND_B,
        '#2BA368',  # cozy meadow-sea green
        '#DE5260',  # warm coral-berry red
        '#F3ECE0',  # warm sand badge tint
        '#1E5B88',  # harbor cerulean-navy primary
        '#FCF9F2',  # card_unknown: cozy warm ivory
        '#F2FAF5',  # card_innocent: soft mint-ivory
        '#FDF4F3',  # card_criminal: soft rose-ivory
    ),
}


def stylesheet(t):
    return f'''
QMainWindow, QWidget#workspace {{background:{t.background};}}
QWidget {{font-family:"Segoe UI";font-size:14px;color:{t.text};}}
QFrame#header {{background:transparent;border:none;}}
QLabel#brand {{
    font-family:"Segoe UI";
    font-size:21px;
    font-weight:800;
    color:#FFF9EE;
    letter-spacing:0.4px;
}}
QLabel#title {{color:#FFF9EE;font-size:15px;font-weight:600;}}
QLabel#muted {{color:{t.muted};font-size:13px;}}
QLabel#section {{font-size:19px;font-weight:700;}}
QWidget#boardCanvas {{background:transparent;}}
QMainWindow::separator {{
    width:0px;
    height:0px;
    background:transparent;
    border:none;
}}
QToolButton#menuButton::menu-indicator,
QToolButton#caseSelector::menu-indicator {{image:none;width:0px;}}
QMenu {{
    background:transparent;
    color:#1B2E40;
    border:none;
    padding:8px;
}}
QMenu::indicator {{
    width:0px;
    height:0px;
}}
QMenu::icon:checked {{
    background:transparent;
    border:none;
}}
QMenu::item {{
    padding:8px 18px 8px 12px;
    border:1.5px solid transparent;
    border-radius:6px;
    font-size:13.5px;
    font-weight:600;
    color:#1B2E40;
}}
QMenu::item:selected {{
    background:#FFE8B6;
    color:#142230;
    border:1.5px solid #D79C46;
}}
QMenu::item:disabled {{
    color:#7E8D9B;
    font-size:11.5px;
    font-weight:800;
    padding:5px 12px 3px 12px;
}}
QMenu::separator {{
    height:1px;
    background:#E4D7C1;
    margin:5px 8px;
}}
QPushButton, QToolButton, QComboBox {{
    background:#FFFDF8;
    border:1.5px solid #C8BBA6;
    border-radius:6px;
    padding:6px 13px;
    font-size:13.5px;
    font-weight:600;
    color:{t.text};
}}
QPushButton:hover, QToolButton:hover {{
    background:#FFF4DC;
    border-color:#B69A72;
}}
QPushButton:focus, QToolButton:focus, QComboBox:focus {{
    border:2px solid {t.selected};
}}
QPushButton#primary {{
    background:{t.primary};
    color:#FFFFFF;
    border:none;
    border-radius:6px;
    padding:8px 18px;
    font-size:14px;
    font-weight:700;
}}
QScrollArea {{border:none;background:transparent;}}
QScrollBar:vertical {{background:transparent;width:6px;}}
QScrollBar::handle:vertical {{background:#C9BCA8;border-radius:3px;min-height:24px;}}
QToolTip {{
    background:#192B3D;
    color:#FFF9EE;
    border:1.5px solid #45627D;
    border-radius:6px;
    padding:6px 10px;
    font-size:12.5px;
    font-weight:600;
}}
QStatusBar {{background:transparent;color:#FFF9EE;font-size:12px;}}
QDockWidget {{color:{t.text};}}
'''
