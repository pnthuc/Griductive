"""Bright coastal palette shared by the desktop widgets and card painter."""
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
    'pixel': Theme('Phố biển', '#DCEFF6', '#FFF7E8', '#302D29', '#80786F',
        '#817D75', '#28576F', '#287DB6', '#BC810C', '#287DB6', '#9C45BE',
        '#3F7F59', '#AF5145', '#F4EAD5', '#245D7A',
        '#FAF8F2', '#F2F4ED', '#F8EFEA'),
}


def stylesheet(t):
    css = f'''
QMainWindow, QWidget#workspace {{background:{t.background};}}
QWidget {{font-family:"Segoe UI";font-size:14px;color:{t.text};}}
QLabel#brand {{font-family:Cambria;font-size:34px;font-weight:bold;color:{t.gold};}}
QLabel#title {{font-family:Cambria;font-size:23px;font-weight:bold;}}
QLabel#muted {{color:{t.muted};font-size:13px;}}
QLabel#section {{font-family:Cambria;font-size:23px;font-weight:bold;}}
QFrame#header, QFrame#footer {{background:{t.surface};border:4px solid {t.border};border-radius:10px;}}
QWidget#boardCanvas {{background:transparent;}}
QLabel#progress {{font-family:"Segoe UI";font-size:17px;font-weight:600;color:{t.text};background:#F6C789;border:3px solid {t.gold};border-radius:19px;padding:8px 17px;}}
QLabel#coordinate {{font-family:Cambria;font-size:23px;font-weight:bold;color:{t.text};background:{t.surface};border:3px solid {t.border};border-radius:7px;padding:3px 14px;}}
QMenu {{background:{t.surface};color:{t.text};border:4px solid {t.gold};padding:6px;}}
QMenu::item {{padding:10px 18px;}}
QMenu::item:selected {{background:{t.primary};color:#FFFFFF;}}
QPushButton, QToolButton, QComboBox {{background:{t.surface};border:3px solid {t.border};border-radius:9px;padding:10px 18px;font-size:15px;}}
QPushButton:hover, QToolButton:hover {{background:{t.badge};border-color:{t.gold};}}
QPushButton:focus, QToolButton:focus, QComboBox:focus {{border:3px solid {t.selected};}}
QPushButton:checked {{background:{t.badge};border-color:{t.gold};}}
QPushButton#primary {{background:{t.primary};color:#F4EDDB;border:2px solid {t.gold};border-radius:22px;padding:12px 25px;font-family:Cambria;font-size:19px;font-weight:bold;}}
QPushButton:disabled {{color:{t.muted};border-color:{t.border};}}
QPushButton#primary:disabled {{background:transparent;color:{t.muted};}}
QToolButton#verdict {{background:{t.surface};border-radius:12px;padding:5px 7px;font-size:12px;}}
QToolButton#verdict:disabled {{color:{t.muted};}}
QPushButton#innocent, QPushButton#criminal {{font-family:"Segoe UI";font-size:14px;font-weight:600;border:2px solid transparent;border-radius:7px;background:transparent;padding:4px 6px;}}
QPushButton#innocent {{color:#34724B;}}
QPushButton#criminal {{color:#A24A3F;}}
QPushButton#innocent:hover {{background:#E3EFDF;}}
QPushButton#criminal:hover {{background:#F6E4DC;}}
QPushButton#innocent:pressed {{background:#CFE2C8;}}
QPushButton#criminal:pressed {{background:#EECFC2;}}
QPushButton#innocent:focus {{border-color:{t.innocent};}}
QPushButton#criminal:focus {{border-color:{t.criminal};}}
QToolButton#chrome {{background:{t.surface};border:3px solid {t.border};border-radius:9px;padding:8px 10px;font-size:14px;}}
QToolButton#chrome:hover {{background:{t.surface};color:{t.text};}}
QToolButton#chrome:focus {{border:3px solid {t.gold};}}
QPushButton#motion {{border:2px solid transparent;border-radius:17px;padding:9px 12px;font-size:13px;color:{t.muted};}}
QPushButton#motion:checked {{background:{t.surface};color:{t.text};}}
QPushButton#hint {{background:#F6C789;color:{t.text};border:3px solid {t.text};border-radius:11px;padding:9px 20px;font-family:"Segoe UI";font-size:18px;font-weight:600;}}
QComboBox QAbstractItemView {{background:{t.surface};color:{t.text};selection-background-color:{t.primary};selection-color:#FFFFFF;}}
QCheckBox {{color:{t.muted};spacing:6px;font-size:12px;}}
QScrollArea {{border:none;background:transparent;}}
QScrollBar:vertical {{background:{t.background};width:10px;}}
QScrollBar::handle:vertical {{background:{t.border};border-radius:4px;min-height:30px;}}
QToolTip {{background:{t.surface};color:{t.text};border:2px solid {t.border};padding:6px;}}
QStatusBar {{background:{t.background};color:{t.muted};font-size:12px;}}
'''

    css += """
QPushButton#hint:hover {background:#FFD79F;}
QDockWidget {color:#193B53;}
"""
    return css
