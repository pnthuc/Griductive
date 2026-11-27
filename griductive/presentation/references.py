"""Selection of semantic references, independent of Qt and clue type names."""
import re
from colorsys import hsv_to_rgb
from dataclasses import dataclass
from itertools import count


SELECTED = '#1D4ED8'
OPERAND_A = '#0284C7'
OPERAND_B = '#7C3AED'
ANCHOR = '#D97706'
CLUE_LINK = re.compile(r'<a href="([^"]+)" style="color:([^;]+);[^"]*">(.*?)</a>')


def _distinct_colors(preferred, reserved):
    """Keep the first use of a color and give repeated uses distinct accents."""
    accents = iter(('#0F766E', '#BE185D', '#9A3412', '#4D7C0F', '#4338CA'))
    hues = count()
    colors = {}
    used = set()
    for key, color in preferred.items():
        if color.lower() in used:
            color = next((accent for accent in accents if accent.lower() not in reserved), None)
            while color is None or color.lower() in used | reserved:
                rgb = hsv_to_rgb(next(hues) * 0.618034 % 1, 0.83, 0.54)
                color = '#' + ''.join(f'{round(channel * 255):02x}' for channel in rgb)
        colors[key] = color
        used.add(color.lower())

    return colors


@dataclass(frozen=True)
class ReferenceFocus:
    counted: frozenset
    anchors: frozenset
    focused: frozenset
    visible: tuple
    named: dict
    preview: object
    region_colors: dict

    def colors_for(self, cell):
        return tuple(dict.fromkeys(
            self.region_colors[part.key] for part in self.visible
            if part.is_region and cell in part.cells
        ))

    def preview_role(self, cell):
        p = self.preview
        return p.role if p and p.role in ('a','b') and cell in p.cells else None


def inspect_references(markup, parts, theme, source=None, pinned=None, preview=None):
    """Resolve clue markup, region border colors, and focused cells."""
    role_colors = {'result': theme.gold, 'a': theme.operand_a,
                   'b': theme.operand_b, 'anchor': theme.anchor}
    links = CLUE_LINK.findall(markup)
    preferred = {key: color for key, color, _ in links if key in parts and parts[key].is_region}
    regions = [part for part in parts.values() if part.is_region]
    operands = [part for part in regions if part.role in ('a', 'b')]
    default_regions = [parts[key] for key in preferred] or operands or regions
    if not preferred:
        preferred = {part.key: role_colors[part.role] for part in default_regions}
    reserved = {color.lower() for color in preferred.values()}
    reserved.update(color.lower() for _, color, _ in links)
    region_colors = _distinct_colors(preferred, reserved)

    def recolor(match):
        key, original, _ = match.groups()
        return match[0].replace(f'color:{original};', f'color:{region_colors.get(key, original)};', 1)

    root = parts.get('result')
    counted = root.cells if root else frozenset()
    anchors = root.anchors if root else frozenset()
    visible = (parts[pinned],) if pinned else tuple(default_regions)
    focused = set().union(*(p.cells for p in visible)) if visible else set(counted)
    if not pinned:
        focused.update(anchors)
    if source:
        focused.add(source)
    named = {}
    for part in parts.values():
        color = region_colors.get(part.key, role_colors[part.role])
        if part.is_region:
            region_colors.setdefault(part.key, color)
        for cell in part.named_cells:
            named.setdefault(cell, color)
    focus = ReferenceFocus(counted, anchors, frozenset(focused), visible,
                           named, parts.get(preview), region_colors)
    return CLUE_LINK.sub(recolor, markup), focus
