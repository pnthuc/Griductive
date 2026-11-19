"""Desktop glyphs rasterized on a 16-pixel grid."""
from functools import lru_cache
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QColor,QIcon,QPainter,QPainterPath,QPen,QPixmap


@lru_cache(maxsize=128)
def icon(name,color):
    image=QPixmap(16,16);image.fill(Qt.GlobalColor.transparent)
    p=QPainter(image);p.scale(.5,.5)
    pen=QPen(QColor(color),1.6);pen.setCapStyle(Qt.PenCapStyle.RoundCap);pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen);p.setBrush(Qt.BrushStyle.NoBrush)
    if name=='folder':
        path=QPainterPath();path.moveTo(4,9);path.lineTo(12,9);path.lineTo(15,12);path.lineTo(28,12)
        path.lineTo(26,25);path.lineTo(4,25);path.closeSubpath();p.drawPath(path)
        p.drawLine(4,12,4,7);p.drawLine(4,7,12,7)
    elif name=='restart':
        p.drawArc(QRectF(6,6,20,20),45*16,290*16)
        p.drawLine(25,5,25,12);p.drawLine(25,12,18,12)
    elif name=='sun':
        p.drawEllipse(QRectF(11,11,10,10))
        for a,b,c,d in [(16,3,16,6),(16,26,16,29),(3,16,6,16),(26,16,29,16),
                        (7,7,9,9),(23,23,25,25),(7,25,9,23),(23,9,25,7)]:p.drawLine(a,b,c,d)
    elif name=='moon':
        path=QPainterPath();path.moveTo(22,5);path.cubicTo(3,0,0,27,18,27)
        path.cubicTo(25,27,29,22,28,19);path.cubicTo(15,24,11,10,22,5);p.drawPath(path)
    elif name=='hint':
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(color))
        bulb=QPainterPath()
        bulb.addEllipse(QRectF(8.5,3.5,15,14.5))
        p.drawPath(bulb)
        neck=QPainterPath()
        neck.moveTo(11,15);neck.lineTo(21,15);neck.lineTo(19.5,22.5);neck.lineTo(12.5,22.5);neck.closeSubpath()
        p.drawPath(neck)
        p.drawRoundedRect(QRectF(12.5,24.2,7,2.4),1.2,1.2)
        p.drawRoundedRect(QRectF(13.8,27.5,4.4,2.2),1.1,1.1)
    elif name=='play':
        p.setBrush(QColor(color));p.setPen(Qt.PenStyle.NoPen)
        path=QPainterPath();path.moveTo(11,6);path.lineTo(26,16);path.lineTo(11,26);path.closeSubpath();p.drawPath(path)
    elif name=='pause':
        p.setBrush(QColor(color));p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(8,6,5,20),1,1);p.drawRoundedRect(QRectF(19,6,5,20),1,1)
    elif name=='step':
        p.setBrush(QColor(color));p.setPen(Qt.PenStyle.NoPen)
        path=QPainterPath();path.moveTo(6,7);path.lineTo(20,16);path.lineTo(6,25);path.closeSubpath();p.drawPath(path)
        p.drawRoundedRect(QRectF(23,7,3,18),1,1)
    elif name=='export':
        pen.setWidthF(2.2);p.setPen(pen)
        p.drawLine(16,4,16,20);p.drawLine(10,14,16,20);p.drawLine(16,20,22,14)
        p.drawLine(5,22,5,28);p.drawLine(5,28,27,28);p.drawLine(27,28,27,22)
    elif name=='innocent':
        path=QPainterPath();path.moveTo(16,3);path.lineTo(27,7);path.lineTo(26,18)
        path.cubicTo(25,24,20,28,16,30);path.cubicTo(12,28,7,24,6,18);path.lineTo(5,7);path.closeSubpath();p.drawPath(path)
        p.drawLine(10,15,14,19);p.drawLine(14,19,22,11)
    elif name=='check':
        pen.setWidthF(3.2);p.setPen(pen)
        p.drawLine(6,16.5,13,23.5);p.drawLine(13,23.5,26.5,8.5)
    elif name=='mask':
        path=QPainterPath();path.moveTo(3,10);path.quadTo(16,6,29,10)
        path.lineTo(27,19);path.quadTo(23,26,16,20)
        path.quadTo(9,26,5,19);path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(color));p.drawPath(path)
        p.setBrush(QColor('#FFFCF5'))
        p.drawEllipse(QRectF(7,12,7,5));p.drawEllipse(QRectF(18,12,7,5))
    elif name=='cross':
        pen.setWidthF(2.9);p.setPen(pen)
        p.drawLine(8.5,8.5,23.5,23.5);p.drawLine(23.5,8.5,8.5,23.5)
    elif name=='warning':
        path=QPainterPath();path.moveTo(16,4);path.lineTo(29,27);path.lineTo(3,27);path.closeSubpath();p.drawPath(path)
        p.drawLine(16,11,16,18);p.drawPoint(16,23)
    elif name=='criminal':
        p.save();p.translate(16,14);p.rotate(-40)
        p.drawRoundedRect(QRectF(-8,-6,16,9),2,2);p.drawLine(0,3,0,17);p.restore()
        p.drawLine(4,28,15,28)
    elif name=='journal':
        p.drawRoundedRect(QRectF(6,4,20,24),2.5,2.5)
        p.drawLine(10,4,10,28)
        for y in (10,15,20):p.drawLine(14,y,22,y)
    elif name=='home':
        p.save()
        p.resetTransform()
        tiles = ('......oo......','.....orro.oo..','....orrrrooo..','...orrrrrroo..',
                 '..orrrrrrrro..','.orrrrrrrrrro.','oooooooooloooo','..owwwwwwwwo..',
                 '..owllwwddwo..','..owllwwddwo..','..owwwwwddwo..','..oooooooooo..')
        colors = {'o': color, 'r': '#B95D46', 'w': '#FFF1CD', 'l': '#669B9E', 'd': '#906742'}
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if tile in colors:
                    p.fillRect(x+1, y+2, 1, 1, QColor(colors[tile]))
        p.restore()
    elif name=='menu':
        pen.setWidthF(2.5);p.setPen(pen)
        for y in (9,16,23):p.drawLine(6,y,26,y)
    elif name=='chevron':
        pen.setWidthF(2.4);p.setPen(pen)
        p.drawLine(9,13,16,20);p.drawLine(16,20,23,13)
    elif name in ('motion','still'):
        for offset in (0,7,14):
            path=QPainterPath();path.moveTo(4,9+offset);path.cubicTo(10,2+offset,20,16+offset,28,9+offset);p.drawPath(path)
        if name=='still':p.drawLine(5,27,27,5)
    p.end()
    result = QIcon()
    for size in (16, 24, 32, 64, 128):
        scaled = image.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        result.addPixmap(scaled)
        result.addPixmap(scaled,QIcon.Mode.Disabled)
    return result
