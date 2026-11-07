"""Desktop cards."""
import math
from PySide6.QtCore import Qt, QRectF, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QTextDocument, QLinearGradient
from PySide6.QtWidgets import QWidget, QPushButton, QBoxLayout, QFrame, QScrollArea
from ..presentation.wording_vi import STATUS_TEXT
from .icons import icon
from .character_animation import CharacterAnimation
from .card_feedback import CardFeedback
from html import escape
from .widgets import InlineClue, painter_font, CardFadeEffect

class PortraitCard(QWidget):
    selected=Signal(str)
    verdict_requested=Signal(str, str)

    def __init__(self,character,status,clue,portrait,theme,parent=None):
        super().__init__(parent)
        self.character=character;self.status=status;self.clue=clue;self.portrait=portrait;self.theme=theme
        self.is_selected=False;self.counted=False;self.anchor=False;self.source=False
        self.dimmed=False;self.preview_role=None;self.region_roles=()
        self.name_role=None
        self.motion=True;self.pixel_style=True
        self.feedback=CardFeedback()
        self.fade_effect=CardFadeEffect(self);self.fade_effect.setOpacity(1.)
        self.setGraphicsEffect(self.fade_effect)
        self.expression_frames=();self.expression=CharacterAnimation(status)
        self._frame_bank=None;self._pose=None;self._old_pose=None;self._pose_started=0.
        self.expression.elapsed=.5+(character.portrait*.731)%3.5
        self.setMinimumSize(160,98);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(f'{character.cell} {character.name}')
        self.actions=QWidget(self);self.actions.setObjectName('verdictActions')
        self.actions.setStyleSheet('QWidget#verdictActions {background:#FFFCF5;border:2px solid #C8C2B7;border-radius:11px;}')
        self.verdict_layout=QBoxLayout(QBoxLayout.Direction.LeftToRight,self.actions)
        self.verdict_layout.setContentsMargins(4,4,4,4);self.verdict_layout.setSpacing(4)
        self.verdict_buttons={}
        for title in ('Innocent','Criminal'):
            w=QPushButton(STATUS_TEXT[title.upper()]);w.setObjectName(title.lower());w.setFixedHeight(40)
            w.setIconSize(QSize(18,18));self.verdict_buttons[title]=w
            w.clicked.connect(lambda checked=False,v=title.upper():self.verdict_requested.emit(self.character.cell,v))
            w.setToolTip('Chỉ chấp nhận khi suy ra được từ lời khai đã mở.');self.verdict_layout.addWidget(w)
        self.actions.hide()
        self.clue_text=InlineClue(self);self.clue_text.chosen.connect(lambda:self.selected.emit(self.character.cell))
        self.note_scroll=QScrollArea(self);self.note_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.note_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.note_scroll.setWidget(self.clue_text);self.note_scroll.setWidgetResizable(False)
        self.note_scroll.setStyleSheet('QScrollArea, QScrollArea > QWidget > QWidget {background:transparent;border:0;} QScrollBar:vertical {width:5px;background:transparent;} QScrollBar::handle:vertical {background:#9A743C;border-radius:2px;}')
        self.note_scroll.viewport().setAutoFillBackground(False)
        self.active_html=None
        self.props=None

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            if self.motion:self.expression.react()
            self.setFocus();self.selected.emit(self.character.cell);self.update()
            event.accept()
        else:super().mousePressEvent(event)

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter,Qt.Key.Key_Space):
            if self.motion:self.expression.react()
            self.selected.emit(self.character.cell);self.update()
        else:super().keyPressEvent(event)

    def resizeEvent(self,event):self.place_actions();super().resizeEvent(event)

    def content_geometry(self):
        s=min(1.,self.height()/210.)
        rect=QRectF(5,5,self.width()-10,self.height()-10)
        portrait_top=max(36,32*s)
        portrait=QRectF(rect.x()+6,rect.y()+portrait_top,rect.width()*.40,rect.height()-portrait_top-max(18,25*s))
        text_left=portrait.right()+14*s
        return rect,portrait,QRectF(text_left,rect.top(),rect.right()-text_left-20,rect.height())

    def place_actions(self):
        _,_,content=self.content_geometry();x=math.ceil(content.x());width=max(40,math.floor(content.width()))
        s=min(1.,self.height()/210.)
        show_actions=self.is_selected and not self.status
        compact=width<180
        self.verdict_layout.setDirection(QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight)
        padding=max(3,round(4*s))
        self.verdict_layout.setContentsMargins(padding,padding,padding,padding)
        button_height=max(22,round(32*s));self.verdict_layout.setSpacing(max(2,round(4*s)))
        action_height=(2*button_height+self.verdict_layout.spacing() if compact else button_height)+2*padding
        self.actions.setGeometry(x,max(round(65*s),self.height()-action_height-round(15*s)),width,action_height)
        self.actions.setVisible(show_actions)
        for name,w in self.verdict_buttons.items():
            w.setFixedHeight(button_height);w.setIconSize(QSize(max(16,round(20*s)),max(16,round(20*s))))
            w.setStyleSheet(f'font-size:{max(11,round(14*s))}px;padding:0;')
            color=self.theme.innocent if name=='Innocent' else self.theme.criminal
            w.setIcon(icon('check' if name=='Innocent' else 'mask',color))
        if self.clue:
            html=self.active_html if self.source and self.active_html else escape(self.clue)
            self.clue_text.active=self.source
            if self.clue_text.text()!=html:self.clue_text.setText(html)
            font_size=max(13,round(18*s))
            self.clue_text.setStyleSheet(f'font-family:"Segoe UI";font-size:{font_size}px;background:transparent;color:{self.theme.text};')
            paper=self.paper_geometry(content,s)
            safe=paper.adjusted(8,6,-8,-6)
            x0,y0=math.ceil(safe.left()),math.ceil(safe.top())
            self.note_scroll.setGeometry(x0,y0,math.floor(safe.right())-x0,
                                         math.floor(safe.bottom())-y0)
            self.note_scroll.show()
            text_width=max(20,self.note_scroll.width()-7)
            doc=QTextDocument();doc.setDocumentMargin(0)
            f=QFont('Segoe UI');f.setPixelSize(font_size);doc.setDefaultFont(f);doc.setHtml(html);doc.setTextWidth(text_width)
            needed=math.ceil(doc.size().height())+5
            # Overflow stays inside the paper; content never changes card geometry.
            self.clue_text.resize(text_width,max(self.note_scroll.viewport().height(),needed))
            self.clue_text.show()
        else:self.note_scroll.hide();self.clue_text.hide()

    def paper_geometry(self,content,scale):
        return QRectF(content.x()-10,73*scale,content.width()+20,self.height()-80*scale)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing,not self.pixel_style);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,not self.pixel_style);t=self.theme
        radius=7
        rect,portrait_rect,content=self.content_geometry()
        s=min(1.,self.height()/210.)
        border=t.innocent if self.status=='INNOCENT' else t.criminal if self.status=='CRIMINAL' else t.border
        background=t.card_innocent if self.status=='INNOCENT' else t.card_criminal if self.status=='CRIMINAL' else t.card_unknown
        p.setBrush(QColor(background));p.setPen(Qt.PenStyle.NoPen);p.drawRoundedRect(rect,radius,radius)
        path=QPainterPath();path.addRoundedRect(rect,radius,radius);p.setClipPath(path)
        if self.props and not self.props.isNull():
            p.save();p.setOpacity(.45 if self.status else .82)
            available=QRectF(content.left(),rect.top()+60*s,
                max(1.,content.width()+12),max(1.,rect.height()-66*s))
            scene_scale=min(available.width()/self.props.width(),available.height()/self.props.height())
            scene_width=self.props.width()*scene_scale
            scene_height=self.props.height()*scene_scale
            scene=QRectF(available.right()-scene_width,available.bottom()-scene_height,
                scene_width,scene_height)
            p.drawPixmap(scene,self.props,QRectF(self.props.rect()));p.restore()
        p.save();p.setClipRect(portrait_rect,Qt.ClipOperation.IntersectClip)
        frame=self.expression.frame if self.motion else {None:0,'INNOCENT':4,'CRIMINAL':6}[self.status]
        portrait=self.expression_frames[frame] if self.expression_frames else self.portrait
        blink=self.expression.blink_amount if self.motion and self.expression_frames else 0.
        if blink>=.5:
            portrait=self.expression_frames[self.expression.blink_frame]
        if self._frame_bank is not self.expression_frames:
            self._frame_bank=self.expression_frames;self._pose=frame;self._old_pose=None
        if frame!=self._pose:
            self._old_pose=self._pose;self._pose=frame;self._pose_started=self.expression.elapsed
        scale=min(portrait_rect.width()/portrait.width(),portrait_rect.height()/portrait.height())
        w=portrait.width()*scale;h=portrait.height()*scale
        x=portrait_rect.center().x()-w/2
        y=rect.bottom()-h-max(18,25*s)
        destination=QRectF(x,y,w,h)
        mix=min(1.,max(0.,(self.expression.elapsed-self._pose_started)/.12)) if self.motion and self._old_pose is not None else 1.
        if mix<1 and self.expression_frames:
            old=self.expression_frames[self._old_pose]
            p.drawPixmap(destination,old,QRectF(old.rect()))
        p.save();p.setOpacity(mix);p.drawPixmap(destination,portrait,QRectF(portrait.rect()));p.restore()
        if self.status=='CRIMINAL':
            progress=self.expression.bars_progress if self.motion else 1.
            top=portrait_rect.top()-(1-progress)*portrait_rect.height()
            for i in range(1,5):
                bx=portrait_rect.left()+portrait_rect.width()*i/5
                steel=QLinearGradient(bx-3,0,bx+4,0)
                steel.setColorAt(0,QColor('#243333'));steel.setColorAt(.45,QColor('#B1B7A8'));steel.setColorAt(1,QColor('#334341'))
                p.fillRect(QRectF(bx-3,top,7,portrait_rect.height()),steel)
            p.fillRect(QRectF(portrait_rect.left(),top+portrait_rect.height()*.15,portrait_rect.width(),5),QColor('#69766C'))
            p.fillRect(QRectF(portrait_rect.left(),top+portrait_rect.height()*.86,portrait_rect.width(),5),QColor('#69766C'))
        p.restore()
        tx=content.x();tw=content.width()-max(19,33*s)
        name_size=28 if rect.width()>360 else 23 if rect.width()>285 else 19
        name_size=max(15,round(name_size*min(1.,s+.15)))
        name_color={'result':t.selected,'a':t.operand_a,'b':t.operand_b,'anchor':t.anchor}.get(self.name_role,t.text)
        painter_font(p,name_size,True,True);p.setPen(QColor(name_color))
        p.drawText(QRectF(tx,rect.y()+7*s,tw,32*s),self.character.name)
        name_width=p.fontMetrics().horizontalAdvance(self.character.name)
        profession_y=rect.y()+40*s
        badge_size=max(22,30*s)
        badge=QRectF(rect.right()-badge_size-8,rect.y()+8,badge_size,badge_size)
        if self.status:
            mark='check' if self.status=='INNOCENT' else 'mask'
            color=t.innocent if self.status=='INNOCENT' else t.criminal
            p.drawPixmap(badge.toRect(),icon(mark,color).pixmap(QSize(64,64)))
        else:
            p.setBrush(QColor('#F6D39C'));p.setPen(QPen(QColor('#A88858'),2));p.drawEllipse(badge)
            painter_font(p,max(13,round(19*s)),True,True);p.setPen(QColor(t.text))
            p.drawText(badge,Qt.AlignmentFlag.AlignCenter,'?')
        painter_font(p,max(11,round(14*s)));p.setPen(QColor(t.muted))
        p.drawText(QRectF(tx,profession_y,tw,26*s),Qt.TextFlag.TextWordWrap,self.character.profession)
        chip=QRectF(13,10,max(42,48*s),max(25,29*s));p.setBrush(QColor(background));p.setPen(QPen(QColor(t.border),2))
        p.drawRoundedRect(chip,7,7);p.setPen(QColor(t.text));painter_font(p,max(17,round(19*s)),True)
        p.drawText(chip,Qt.AlignmentFlag.AlignCenter,self.character.cell)
        # Replace the existing perimeter, never add nested frames or a surface wash.
        colors=[]
        if not self.is_selected:
            colors=[{'result':t.selected,'a':t.operand_a,'b':t.operand_b}[role] for role in self.region_roles]
        p.setClipping(False)
        p.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if colors:
            # Multiple regions share ONE perimeter, each owning an equal segment.
            # Hover never replaces the other region's color.
            for i,color in enumerate(colors):
                p.setPen(QPen(QColor(color),7,Qt.PenStyle.SolidLine,Qt.PenCapStyle.FlatCap))
                p.drawPath(path if len(colors)==1 else path.trimmed(i/len(colors),(i+1)/len(colors)))
        else:
            p.setPen(QPen(QColor(border),4 if self.status else 3.5))
            p.drawRoundedRect(rect,radius,radius)

