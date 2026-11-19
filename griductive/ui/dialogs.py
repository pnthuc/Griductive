"""Game notices that share the board's paper, outlines and pixel characters."""
from PySide6.QtCore import Qt,QSize,QRectF
from PySide6.QtGui import QColor,QPainter
from PySide6.QtWidgets import QDialog,QFrame,QLabel,QToolButton,QHBoxLayout,QVBoxLayout,QGraphicsDropShadowEffect
from .icons import icon
from .widgets import pixel_frame, PixelHintButton


class ModalScrim(QFrame):
    def __init__(self,parent):
        super().__init__(parent)
        self.setObjectName('noticeScrim')
        self.setStyleSheet('QFrame#noticeScrim {background:rgba(15,35,66,95);border:0;}')

    def mousePressEvent(self,event):event.accept()
    def mouseReleaseEvent(self,event):event.accept()


class NoticePanel(QFrame):
    def paintEvent(self, event):
        painter = QPainter(self)
        box = QRectF(self.rect())
        painter.fillPath(pixel_frame(box, 6), QColor('#514344'))
        paper = box.adjusted(3, 3, -3, -6)
        painter.fillPath(pixel_frame(paper, 4), QColor('#FAF3E4'))
        painter.fillRect(8, 5, self.width()-16, 2, QColor('#FFFDF1'))


class GameNotice(QDialog):
    def __init__(self,parent,theme,title,message,*,tone='info',subject=None,action='Đã hiểu'):
        super().__init__(parent,Qt.WindowType.Dialog|Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle(title);self.setAccessibleName(title)
        self.setFixedWidth(540 if subject else 480)
        outer=QVBoxLayout(self);outer.setContentsMargins(16,16,16,22)
        self.panel=NoticePanel();self.panel.setObjectName('gameNotice');outer.addWidget(self.panel)
        accent=theme.innocent if tone=='success' else '#D97706' if tone=='warning' else theme.primary
        self.setStyleSheet(f'''
QFrame#gameNotice {{background:transparent;border:0;}}
QFrame#gameNotice QLabel {{background:transparent;border:0;color:{theme.text};}}
QFrame#gameNotice QLabel#noticeSymbol {{background:#F1D7A1;border:2px solid #9C7952;}}
QLabel#noticeTitle {{font-family:"Segoe UI";font-size:22px;font-weight:800;}}
QLabel#noticeSubject {{font-family:"Segoe UI";font-size:23px;font-weight:700;}}
QLabel#noticeMessage {{font-family:"Segoe UI";font-size:15px;color:#334155;}}
QToolButton#noticeClose {{background:transparent;border:1px solid transparent;border-radius:2px;padding:3px;}}
QToolButton#noticeClose:hover {{background:#F1F5F9;border-color:#CBD5E1;}}
QPushButton#noticeAction {{background:{theme.primary};color:#FFFFFF;border:2px solid #243D67;border-bottom-width:4px;border-radius:2px;padding:9px 20px;font-size:15px;font-weight:700;}}
QPushButton#noticeAction:hover {{background:#1E40AF;}}
''')
        shadow=QGraphicsDropShadowEffect(self.panel);shadow.setBlurRadius(0)
        shadow.setOffset(4,4);shadow.setColor(QColor(20,43,58,95));self.panel.setGraphicsEffect(shadow)
        layout=QVBoxLayout(self.panel);layout.setContentsMargins(23,20,23,20);layout.setSpacing(19)
        heading=QHBoxLayout();heading.setSpacing(13)
        symbol=QLabel();symbol.setObjectName('noticeSymbol' if tone in ('success','warning') else 'hintBulb');symbol.setFixedSize(42,42)
        symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        symbol.setPixmap(icon('check' if tone=='success' else 'warning' if tone=='warning' else 'hint',accent).pixmap(QSize(26,26)))
        heading.addWidget(symbol)
        self.title_label=QLabel(title);self.title_label.setObjectName('noticeTitle');heading.addWidget(self.title_label,1)
        self.close_button=QToolButton();self.close_button.setObjectName('noticeClose')
        self.close_button.setIcon(icon('cross','#695344'));self.close_button.setIconSize(QSize(19,19));self.close_button.setFixedSize(30,30)
        self.close_button.setAccessibleName('Đóng thông báo');self.close_button.setToolTip('Đóng')
        self.close_button.clicked.connect(self.reject);heading.addWidget(self.close_button,0,Qt.AlignmentFlag.AlignTop)
        layout.addLayout(heading)
        body=QHBoxLayout();body.setSpacing(18)
        if subject:
            name,portrait=subject
            figure=QLabel();figure.setObjectName('noticeFigure');figure.setFixedSize(210,210);figure.setAlignment(Qt.AlignmentFlag.AlignCenter)
            figure.setPixmap(portrait.scaled(figure.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.FastTransformation))
            body.addWidget(figure,0,Qt.AlignmentFlag.AlignTop)
        words=QVBoxLayout();words.setSpacing(10)
        if subject:
            name_label=QLabel(name);name_label.setObjectName('noticeSubject');words.addWidget(name_label)
        self.message=QLabel(message);self.message.setObjectName('noticeMessage');self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.TextFormat.PlainText);words.addWidget(self.message);words.addStretch()
        body.addLayout(words,1);layout.addLayout(body)
        actions=QHBoxLayout();actions.addStretch()
        self.action_button=PixelHintButton(action);self.action_button.setFixedSize(max(110,self.action_button.fontMetrics().horizontalAdvance(action)+52),38);self.action_button.setObjectName('noticeAction')
        self.action_button.setDefault(True);self.action_button.clicked.connect(self.accept)
        actions.addWidget(self.action_button);layout.addLayout(actions)
        self.adjustSize()
