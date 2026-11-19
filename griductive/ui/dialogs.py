"""Game notices that share the board's paper, outlines and pixel characters."""
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog,QFrame,QLabel,QPushButton,QToolButton,QHBoxLayout,QVBoxLayout,QGraphicsDropShadowEffect
from .icons import icon


class ModalScrim(QFrame):
    def __init__(self,parent):
        super().__init__(parent)
        self.setObjectName('noticeScrim')
        self.setStyleSheet('QFrame#noticeScrim {background:rgba(15,35,66,95);border:0;}')

    def mousePressEvent(self,event):event.accept()
    def mouseReleaseEvent(self,event):event.accept()


class GameNotice(QDialog):
    def __init__(self,parent,theme,title,message,*,tone='info',subject=None,action='Đã hiểu'):
        super().__init__(parent,Qt.WindowType.Dialog|Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle(title);self.setAccessibleName(title)
        self.setFixedWidth(480)
        outer=QVBoxLayout(self);outer.setContentsMargins(16,16,16,22)
        self.panel=QFrame();self.panel.setObjectName('gameNotice');outer.addWidget(self.panel)
        accent=theme.innocent if tone=='success' else '#D97706' if tone=='warning' else theme.primary
        self.setStyleSheet(f'''
QFrame#gameNotice {{background:#FAF8F2;border:3px solid #766A59;border-radius:2px;}}
QFrame#gameNotice QLabel {{background:transparent;border:0;color:{theme.text};}}
QLabel#noticeTitle {{font-family:"Segoe UI";font-size:22px;font-weight:800;}}
QLabel#noticeSubject {{font-family:"Segoe UI";font-size:23px;font-weight:700;}}
QFrame#gameNotice QLabel#noticeCell {{font-size:12px;font-weight:700;color:#FFFFFF;background:{theme.primary};border-radius:2px;padding:3px 8px;}}
QLabel#noticeMessage {{font-family:"Segoe UI";font-size:15px;color:#334155;}}
QToolButton#noticeClose {{background:transparent;border:1px solid transparent;border-radius:2px;padding:3px;}}
QToolButton#noticeClose:hover {{background:#F1F5F9;border-color:#CBD5E1;}}
QPushButton#noticeAction {{background:{theme.primary};color:#FFFFFF;border:2px solid #243D67;border-bottom-width:4px;border-radius:2px;padding:9px 20px;font-size:15px;font-weight:700;}}
QPushButton#noticeAction:hover {{background:#1E40AF;}}
''')
        shadow=QGraphicsDropShadowEffect(self.panel);shadow.setBlurRadius(24)
        shadow.setOffset(0,6);shadow.setColor(QColor(20,43,58,95));self.panel.setGraphicsEffect(shadow)
        layout=QVBoxLayout(self.panel);layout.setContentsMargins(23,20,23,20);layout.setSpacing(19)
        heading=QHBoxLayout();heading.setSpacing(13)
        symbol=QLabel();symbol.setObjectName('noticeSymbol');symbol.setFixedSize(42,42)
        symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        symbol.setPixmap(icon('check' if tone=='success' else 'warning' if tone=='warning' else 'hint',accent).pixmap(QSize(26,26)))
        heading.addWidget(symbol)
        self.title_label=QLabel(title);self.title_label.setObjectName('noticeTitle');heading.addWidget(self.title_label,1)
        self.close_button=QToolButton();self.close_button.setObjectName('noticeClose')
        self.close_button.setIcon(icon('cross',theme.muted));self.close_button.setIconSize(QSize(19,19));self.close_button.setFixedSize(30,30)
        self.close_button.setAccessibleName('Đóng thông báo');self.close_button.setToolTip('Đóng')
        self.close_button.clicked.connect(self.reject);heading.addWidget(self.close_button,0,Qt.AlignmentFlag.AlignTop)
        layout.addLayout(heading)
        body=QHBoxLayout();body.setSpacing(18)
        if subject:
            name,cell,portrait=subject
            figure=QLabel();figure.setFixedSize(104,116);figure.setAlignment(Qt.AlignmentFlag.AlignCenter)
            figure.setPixmap(portrait.scaled(104,116,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.FastTransformation))
            body.addWidget(figure,0,Qt.AlignmentFlag.AlignTop)
        words=QVBoxLayout();words.setSpacing(10)
        if subject:
            identity=QHBoxLayout();identity.setSpacing(10)
            name_label=QLabel(name);name_label.setObjectName('noticeSubject');identity.addWidget(name_label)
            cell_label=QLabel(cell);cell_label.setObjectName('noticeCell');identity.addWidget(cell_label,0,Qt.AlignmentFlag.AlignVCenter)
            identity.addStretch();words.addLayout(identity)
        self.message=QLabel(message);self.message.setObjectName('noticeMessage');self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.TextFormat.PlainText);words.addWidget(self.message);words.addStretch()
        body.addLayout(words,1);layout.addLayout(body)
        actions=QHBoxLayout();actions.addStretch()
        self.action_button=QPushButton(action);self.action_button.setObjectName('noticeAction')
        self.action_button.setDefault(True);self.action_button.clicked.connect(self.accept)
        actions.addWidget(self.action_button);layout.addLayout(actions)
        self.adjustSize()
