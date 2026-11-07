"""Selection of semantic references, independent of Qt and clue type names."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceFocus:
    counted: frozenset
    anchors: frozenset
    focused: frozenset
    visible: tuple
    named: dict
    preview: object

    def roles(self, cell):
        return tuple(role for role in ('result','a','b')
                     if any(p.is_region and p.role==role and cell in p.cells for p in self.visible))

    def preview_role(self, cell):
        p=self.preview
        return p.role if p and p.role in ('a','b') and cell in p.cells else None


def reference_focus(parts, source=None, pinned=None, preview=None):
    root=parts.get('result')
    counted=root.cells if root else frozenset()
    anchors=root.anchors if root else frozenset()
    regions=[p for p in parts.values() if p.is_region]
    operands=[p for p in regions if p.role in ('a','b')]
    visible=(parts[pinned],) if pinned else tuple(operands or regions)
    focused=set().union(*(p.cells for p in visible)) if visible else set(counted)
    if not pinned:
        focused.update(anchors)
    if source:
        focused.add(source)
    named={}
    for part in parts.values():
        for cell in part.named_cells:
            named.setdefault(cell,part.role)
    return ReferenceFocus(counted,anchors,frozenset(focused),visible,named,parts.get(preview))
