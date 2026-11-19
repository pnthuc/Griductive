"""Alto's Odyssey x Reigns luminous sky & crisp white flat-vector palette."""
from dataclasses import dataclass


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
        'Thảo nguyên xanh',
        '#455B60',  # matte slate board
        '#FFFFFF',  # surface: pure crisp white vector card
        '#0F172A',  # text: deep slate ink
        '#64748B',  # muted: cool slate subtitle
        '#D5E6F7',  # border: airy sky-white card rim
        '#0F2942',  # gold: deep navy ink accent
        '#1D4ED8',  # selected: royal cobalt
        '#D97706',  # anchor: warm amber
        '#0284C7',  # operand_a: ocean blue
        '#7C3AED',  # operand_b: vivid purple
        '#34C774',  # innocent: meadow green
        '#F85A6A',  # criminal: poppy coral
        '#EFF6FF',  # badge: soft sky tint
        '#1D4ED8',  # primary: royal cobalt
        '#FAF8F2',  # card_unknown
        '#F2F4ED',  # card_innocent
        '#F8EFEA',  # card_criminal
    ),
}


def stylesheet(t):
    return f'''
QMainWindow, QWidget#workspace {{background:{t.background};}}
QWidget {{font-family:"Segoe UI";font-size:14px;color:{t.text};}}
QFrame#header {{background:transparent;border:none;}}
QLabel#brand {{
    font-family:"Segoe UI";
    font-size:27px;
    font-weight:800;
    color:#FFFFFF;
}}
QLabel#headerDot {{
    color:rgba(255,255,255,195);
    font-size:19px;
    font-weight:700;
}}
QToolButton#caseSelector {{
    background:transparent;
    color:rgba(255,255,255,245);
    border:1px solid transparent;
    border-radius:2px;
    padding:4px 8px;
    font-family:"Segoe UI";
    font-size:18px;
    font-weight:600;
}}
QToolButton#caseSelector:hover {{
    background:rgba(255,255,255,36);
    border-color:rgba(255,255,255,90);
    color:#FFFFFF;
}}
QLabel#title {{color:#FFFFFF;font-size:16px;font-weight:600;}}
QLabel#muted {{color:{t.muted};font-size:13px;}}
QLabel#section {{font-size:20px;font-weight:700;}}
QWidget#boardCanvas {{background:transparent;}}
QLabel#coordHeader {{
    background:rgba(255,255,255,74);
    color:#0D2744;
    border:none;
    border-radius:2px;
    font-family:"Segoe UI";
    font-size:15px;
    font-weight:800;
    padding:2px 6px;
}}
QToolButton#menuButton {{
    background:#F5DEAD;border:2px solid #493A37;border-bottom-width:4px;
    padding:0;border-radius:0;
}}
QToolButton#menuButton:hover {{background:#FFEDBF;}}
QToolButton#menuButton:pressed {{background:#E4C593;border-bottom-width:2px;padding-top:2px;}}
QToolButton#menuButton::menu-indicator {{image:none;width:0px;}}
QToolButton#caseSelector::menu-indicator {{image:none;width:0px;}}
QMenu {{
    background:#FBF3E3;color:#463A38;border:3px solid #514344;
    border-bottom:5px solid #45383B;padding:5px;
}}
QMenu::item {{padding:8px 16px 8px 10px;border:2px solid transparent;font-weight:600;}}
QMenu::item:selected {{background:#F1D7A1;color:#382F32;border:2px solid #A98153;}}
QMenu::separator {{height:2px;background:#CDB690;margin:4px 6px;}}
QPushButton, QToolButton, QComboBox {{
    background:#FFFFFF;
    border:1.5px solid #CBD5E1;
    border-radius:2px;
    padding:7px 14px;
    font-size:14px;
    font-weight:600;
}}
QPushButton:hover, QToolButton:hover {{background:#F1F5F9;border-color:#94A3B8;}}
QPushButton:focus, QToolButton:focus, QComboBox:focus {{border:2px solid {t.selected};}}
QPushButton#primary {{
    background:{t.primary};
    color:#FFFFFF;
    border:none;
    border-radius:2px;
    padding:9px 20px;
    font-size:15px;
    font-weight:700;
}}
QPushButton#innocent {{
    font-family:"Segoe UI";
    font-size:13px;
    font-weight:700;
    color:#FFFFFF;
    background:#43CE80;
    border:none;
    border-bottom:3px solid #2BA862;
    border-top-left-radius:6px;
    border-bottom-left-radius:0px;
    border-top-right-radius:0px;
    border-bottom-right-radius:0px;
    padding:2px 6px;
}}
QPushButton#innocent:hover {{background:#36BE72;}}
QPushButton#criminal {{
    font-family:"Segoe UI";
    font-size:13px;
    font-weight:700;
    color:#FFFFFF;
    background:#FA6473;
    border:none;
    border-bottom:3px solid #DE4454;
    border-top-left-radius:0px;
    border-bottom-left-radius:0px;
    border-top-right-radius:6px;
    border-bottom-right-radius:9px;
    padding:2px 6px;
}}
QPushButton#criminal:hover {{background:#F05060;}}
QScrollArea {{border:none;background:transparent;}}
QScrollBar:vertical {{background:transparent;width:6px;}}
QScrollBar::handle:vertical {{background:#CBD5E1;border-radius:3px;min-height:24px;}}
QToolTip {{
    background:#0F172A;
    color:#FFFFFF;
    border:none;
    border-radius:2px;
    padding:6px 10px;
}}
QStatusBar {{background:transparent;color:#FFFFFF;font-size:12px;}}
QDockWidget {{color:{t.text};}}
'''
