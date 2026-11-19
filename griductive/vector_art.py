"""Flat SVG artwork drawn from shared character and profession shapes.

Generates mathematical SVG strings with zero external dependencies, shared 1:1
by Desktop (PySide6 QtSvg) and Web (Dash SVG). Strictly avoids CSS rgba() or
nested clipPaths so QtSvg Tiny 1.2 and modern browsers render identically.
"""
from functools import lru_cache

# Vibrant full-color skin ramps: (base, right_shadow, chin_cast)
SKIN_TONES = {
    'deep': ('#7D5340', '#674231', '#4F3022'),
    'sienna': ('#A87256', '#8E5C42', '#70452F'),
    'tan': ('#D69A76', '#BC805E', '#9B6345'),
    'warm': ('#EAAC86', '#D1916C', '#B07351'),
    'ivory': ('#F4BE9C', '#DC9F7C', '#BA7F5E'),
}

# Cool Ice-Blue Mystery Silhouette ramp for unopened & unselected suspects
ICE_SKIN = ('#A9CBEB', '#93B9DF', '#7CA6D1')
ICE_DARK = '#79A3CC'
ICE_MID = '#8EB6DD'
ICE_LIGHT = '#F2F8FF'
ICE_ACCENT = '#6994BF'

# Portrait IDs matching assets/characters/characters.json.
# (skin, face, hair_style, hair_color, outfit, garment_a, garment_b, eyewear, beard, prop_head)
CHARACTER_SPECS = (
    # 0 Ada - Bác sĩ
    ('deep', 'soft', 'wavy_bob', '#263244', 'labcoat', '#F5F9FF', '#22B8CF', None, None, 'head_mirror'),
    # 1 Ben - Họa sĩ
    ('warm', 'angular', 'beret', '#1E9E5A', 'crew', '#9BE14F', '#27965B', None, 'goatee', None),
    # 2 Cara - Nhà báo
    ('ivory', 'soft', 'fedora_bob', '#3B232A', 'trench', '#D62F49', '#8E1D30', None, None, 'red_fedora'),
    # 3 Dara - Luật sư
    ('sienna', 'soft', 'sleek_bob', '#233042', 'blazer', '#334E6E', '#F5F9FF', 'cat_eye', None, None),
    # 4 Eli - Giáo sư
    ('warm', 'broad', 'scholar', '#DCE6F2', 'bowtie', '#5A6878', '#1D4ED8', 'rect', 'mustache_white', None),
    # 5 Finn - Đầu bếp
    ('tan', 'angular', 'chef_toque', '#F5F9FF', 'chef', '#F5F9FF', '#E11D48', None, None, None),
    # 6 Gwen - Thủ thư
    ('ivory', 'soft', 'bob_bangs', '#2E2320', 'turtleneck', '#134E4A', '#0F766E', 'round', None, None),
    # 7 Hugo - Thợ máy
    ('sienna', 'broad', 'cap', '#2563EB', 'overalls', '#60A5FA', '#1E40AF', 'cap_goggles', 'stubble', None),
    # 8 Isla - Làm vườn
    ('tan', 'soft', 'sunhat', '#FBBF24', 'overalls', '#DCFCE7', '#16A34A', None, None, 'leaf_badge'),
    # 9 Jasper - Nhiếp ảnh gia
    ('warm', 'angular', 'quiff', '#422B23', 'vest', '#334155', '#FACC15', None, 'goatee', None),
    # 10 Kira - Kiến trúc sư
    ('deep', 'soft', 'blunt_bob', '#1E293B', 'turtleneck', '#E11D48', '#881337', 'rect', None, None),
    # 11 Leon - Thợ đồng hồ
    ('ivory', 'broad', 'silver_part', '#CBD5E1', 'bowtie', '#3B495E', '#E11D48', 'round', 'mustache_white', None),
    # 12 Mina - Nhạc công
    ('warm', 'soft', 'long_wave', '#2D1E2F', 'concert', '#7C3AED', '#DDD6FE', None, None, None),
    # 13 Nolan - Lính cứu hỏa
    ('sienna', 'broad', 'fire_helmet', '#EF4444', 'turnout', '#1E293B', '#FACC15', None, 'stubble', None),
    # 14 Opal - Người bán hoa
    ('ivory', 'soft', 'braid_bun', '#854D2E', 'apron', '#FCE7F3', '#EC4899', None, None, None),
    # 15 Pavel - Thợ may
    ('warm', 'angular', 'side_part', '#312520', 'vest', '#475569', '#F59E0B', None, 'mustache', None),
    # 16 Quinn - Phi công
    ('sienna', 'angular', 'aviator', '#6B4226', 'flight', '#78350F', '#FEF3C7', 'cap_goggles', None, None),
    # 17 Rosa - Thợ bánh
    ('tan', 'soft', 'baker_beret', '#FEF3C7', 'scarf', '#FFFBEB', '#F43F5E', None, None, None),
    # 18 Silas - Thám tử
    ('warm', 'angular', 'trilby', '#1E3A5F', 'trench', '#2563EB', '#FBBF24', None, None, None),
    # 19 Tessa - Kỹ sư
    ('ivory', 'soft', 'ponytail', '#5B3726', 'workshirt', '#0284C7', '#FACC15', 'cap_goggles', None, None),
    # 20 Umar - Người bán sách
    ('deep', 'angular', 'curly', '#1E293B', 'suit_tie', '#0F766E', '#F59E0B', 'round', None, None),
    # 21 Vera - Y tá
    ('ivory', 'soft', 'nurse_updo', '#6D422E', 'scrubs', '#06B6D4', '#F8FAFC', None, None, None),
    # 22 Wade - Thủy thủ
    ('tan', 'broad', 'captain_cap', '#1E3A8A', 'peacoat', '#1E3A8A', '#FBBF24', None, 'full', None),
    # 23 Xenia - Giáo viên âm nhạc
    ('warm', 'soft', 'chignon', '#94A3B8', 'peterpan', '#6D28D9', '#F8FAFC', 'round', None, None),
    # 24 Yuri - Nhà thực vật học
    ('tan', 'angular', 'tousled', '#3F2B20', 'overalls', '#FEF9C3', '#15803D', None, None, 'leaf_badge'),
)

PORTRAIT_COUNT = len(CHARACTER_SPECS)


def _head_paths(face):
    if face == 'broad':
        full = 'M84,96 C84,61 103,50 128,50 C153,50 172,61 172,96 L169,125 C167,141 149,155 128,156 C107,155 89,141 87,125 Z'
        right = 'M128,50 C153,50 172,61 172,96 L169,125 C167,141 149,155 128,156 Z'
        return full, right
    if face == 'angular':
        full = 'M86,95 C86,62 105,51 128,51 C151,51 170,62 170,95 L166,123 C163,139 146,153 128,155 C110,153 93,139 90,123 Z'
        right = 'M128,51 C151,51 170,62 170,95 L166,123 C163,139 146,153 128,155 Z'
        return full, right
    full = 'M88,96 C88,63 106,52 128,52 C150,52 168,63 168,96 C168,122 155,145 128,153 C101,145 88,122 88,96 Z'
    right = 'M128,52 C150,52 168,63 168,96 C168,122 155,145 128,153 Z'
    return full, right


def _hair_back(style, color, silhouette=False):
    if style == 'wavy_bob':
        return (
            f'<path d="M72,100 C68,64 94,40 128,40 C162,40 188,64 184,100 '
            f'C188,126 178,150 162,156 L94,156 C78,150 68,126 72,100 Z" fill="{color}"/>'
        )
    if style in ('sleek_bob', 'blunt_bob', 'bob_bangs'):
        return (
            f'<path d="M76,96 C76,56 98,40 128,40 C158,40 180,56 180,96 '
            f'L176,152 L80,152 Z" fill="{color}"/>'
        )
    if style == 'fedora_bob':
        return (
            f'<path d="M83,78 Q128,55 173,78 L180,133 Q183,155 162,160 '
            f'L94,160 Q73,155 76,133 Z" fill="{color}"/>'
        )
    if style == 'sunhat':
        locks = ICE_ACCENT if silhouette else '#5D3A29'
        return (
            f'<ellipse cx="128" cy="86" rx="74" ry="25" fill="{color}"/>'
            f'<path d="M82,98 C76,126 80,152 94,160 L162,160 C176,152 180,126 174,98 Z" fill="{locks}"/>'
        )
    if style == 'long_wave':
        return (
            f'<path d="M74,94 C74,54 98,40 128,40 C158,40 182,54 182,94 '
            f'C186,130 180,166 168,178 L88,178 C76,166 70,130 74,94 Z" fill="{color}"/>'
        )
    if style == 'ponytail':
        return f'<path d="M152,62 C180,64 192,90 184,130 C180,148 168,156 158,154 Z" fill="{color}"/>'
    if style in ('high_bun', 'chignon'):
        bun_y = 35 if style == 'high_bun' else 44
        return f'<circle cx="128" cy="{bun_y}" r="20" fill="{color}"/>'
    return ''


def _outfit_svg(outfit, ga, gb, prop_head, silhouette):
    base = (
        f'<path d="M40,244 C44,200 68,181 102,175 L154,175 C188,181 212,200 216,244 Z" fill="{ga}"/>'
        '<path d="M128,175 L154,175 C188,181 212,200 216,244 L128,244 Z" fill="#0F2942" fill-opacity="0.11"/>'
    )
    details = ''
    if outfit == 'labcoat':
        details = (
            f'<polygon points="104,175 128,226 152,175" fill="{gb}"/>'
            '<polygon points="90,178 80,208 108,218 128,228 104,175" fill="#FFFFFF"/>'
            '<polygon points="166,178 176,208 148,218 128,228 152,175" fill="#E6F0FA"/>'
            f'<path d="M96,192 V226 C96,236 114,236 114,226 V214 M160,192 V224" '
            f'fill="none" stroke="{gb}" stroke-width="4.5" stroke-linecap="round"/>'
            f'<circle cx="160" cy="228" r="6" fill="{gb}"/>'
        )
    elif outfit == 'blazer':
        details = (
            f'<polygon points="102,175 128,236 154,175" fill="{gb}"/>'
            '<polygon points="90,178 80,208 106,216 128,236 102,175" fill="#0F2942" fill-opacity="0.18"/>'
            '<polygon points="166,178 176,208 150,216 128,236 154,175" fill="#0F2942" fill-opacity="0.26"/>'
        )
    elif outfit == 'suit_tie':
        shirt = ICE_LIGHT if silhouette else '#F8FAFC'
        details = (
            f'<polygon points="104,175 128,236 152,175" fill="{shirt}"/>'
            f'<polygon points="122,190 134,190 138,236 128,244 118,236" fill="{gb}"/>'
        )
    elif outfit == 'bowtie':
        shirt = ICE_LIGHT if silhouette else '#F8FAFC'
        details = (
            f'<polygon points="102,175 128,240 154,175" fill="{shirt}"/>'
            '<polygon points="90,178 82,210 108,220 128,240 102,175" fill="#0F2942" fill-opacity="0.16"/>'
            '<polygon points="166,178 174,210 148,220 128,240 154,175" fill="#0F2942" fill-opacity="0.24"/>'
            f'<polygon points="112,188 128,195 112,202" fill="{gb}"/>'
            f'<polygon points="144,188 128,195 144,202" fill="{gb}"/>'
            f'<circle cx="128" cy="195" r="4" fill="{gb}"/>'
        )
    elif outfit == 'vest':
        shirt = ICE_LIGHT if silhouette else '#F8FAFC'
        details = (
            f'<polygon points="98,175 128,226 158,175" fill="{shirt}"/>'
            f'<polygon points="123,190 133,190 135,226 121,226" fill="{gb}"/>'
        )
    elif outfit == 'chef':
        details = (
            '<rect x="104" y="175" width="48" height="69" fill="#0F2942" fill-opacity="0.06"/>'
            f'<circle cx="116" cy="202" r="4" fill="{gb}"/><circle cx="140" cy="202" r="4" fill="{gb}"/>'
            f'<circle cx="116" cy="224" r="4" fill="{gb}"/><circle cx="140" cy="224" r="4" fill="{gb}"/>'
        )
    elif outfit == 'turtleneck':
        details = f'<rect x="104" y="164" width="48" height="22" rx="6" fill="{gb}"/>'
    elif outfit == 'peterpan':
        details = f'<path d="M100,175 C98,198 118,204 128,190 C138,204 158,198 156,175 Z" fill="{gb}"/>'
    elif outfit == 'workshirt':
        details = f'<polygon points="102,175 116,204 128,190 140,204 154,175" fill="{gb}"/>'
    elif outfit == 'overalls':
        details = (
            f'<rect x="90" y="204" width="76" height="40" rx="3" fill="{gb}"/>'
            f'<rect x="92" y="176" width="12" height="32" fill="{gb}"/>'
            f'<rect x="152" y="176" width="12" height="32" fill="{gb}"/>'
            '<circle cx="98" cy="212" r="3.5" fill="#F8FAFC"/><circle cx="158" cy="212" r="3.5" fill="#F8FAFC"/>'
        )
    elif outfit == 'trench':
        inner = ICE_LIGHT if silhouette else '#FFF2E7'
        details = (
            f'<polygon points="106,175 128,224 150,175" fill="{inner}"/>'
            f'<polygon points="84,178 72,208 108,220 128,232 104,175" fill="{gb}"/>'
            f'<polygon points="172,178 184,208 148,220 128,232 152,175" fill="{gb}"/>'
        )
    elif outfit == 'turnout':
        details = (
            '<rect x="104" y="168" width="48" height="18" rx="4" fill="#0F172A" fill-opacity="0.5"/>'
            f'<rect x="52" y="218" width="152" height="11" fill="{gb}"/>'
        )
    elif outfit == 'flight':
        details = f'<path d="M88,174 C86,204 112,212 128,204 C144,212 170,204 168,174 Z" fill="{gb}"/>'
    elif outfit == 'scarf':
        details = (
            f'<path d="M98,175 Q128,198 158,175 Q146,198 128,198 Q110,198 98,175 Z" fill="{gb}"/>'
            f'<polygon points="122,194 134,194 140,224 128,218 116,224" fill="{gb}"/>'
        )
    elif outfit == 'scrubs':
        details = f'<polygon points="104,175 128,214 152,175" fill="{gb}"/>'
    elif outfit == 'peacoat':
        details = (
            f'<circle cx="112" cy="214" r="4.5" fill="{gb}"/><circle cx="144" cy="214" r="4.5" fill="{gb}"/>'
            f'<circle cx="112" cy="232" r="4.5" fill="{gb}"/><circle cx="144" cy="232" r="4.5" fill="{gb}"/>'
        )
    elif outfit == 'apron':
        details = (
            f'<rect x="94" y="196" width="68" height="48" rx="3" fill="{gb}"/>'
            f'<rect x="98" y="176" width="10" height="24" fill="{gb}"/>'
            f'<rect x="148" y="176" width="10" height="24" fill="{gb}"/>'
        )
    elif outfit == 'concert':
        details = f'<polygon points="102,175 128,218 154,175" fill="{gb}"/>'
    else:  # crew
        details = f'<path d="M100,175 Q128,194 156,175 L152,184 Q128,202 104,184 Z" fill="{gb}"/>'

    if prop_head == 'leaf_badge':
        leaf_c = ICE_ACCENT if silhouette else '#15803D'
        vein_c = ICE_LIGHT if silhouette else '#86EFAC'
        details += (
            f'<path d="M178,192 C154,194 144,212 146,236 C170,234 182,216 178,192 Z" fill="{leaf_c}"/>'
            f'<path d="M148,234 L172,200" stroke="{vein_c}" stroke-width="2.5" stroke-linecap="round"/>'
        )
    return base + details


def _hair_front_and_hat(style, color, prop_head, silhouette):
    if style == 'wavy_bob':
        headband = ''
        if prop_head == 'head_mirror':
            band_c = ICE_ACCENT if silhouette else '#475569'
            disc_c = ICE_LIGHT if silhouette else '#F8FAFC'
            hole_c = ICE_DARK if silhouette else '#38BDF8'
            headband = (
                f'<path d="M86,74 Q128,62 170,74" fill="none" stroke="{band_c}" stroke-width="6"/>'
                f'<circle cx="136" cy="64" r="13" fill="{disc_c}"/>'
                f'<circle cx="136" cy="64" r="5" fill="{hole_c}"/>'
            )
        return (
            f'<path d="M84,92 C86,60 108,46 132,48 C154,50 172,64 172,92 '
            f'C160,74 142,68 124,72 C106,76 92,82 84,92 Z" fill="{color}"/>'
            + headband
        )
    if style == 'beret':
        brim = ICE_ACCENT if silhouette else '#167944'
        return (
            f'<path d="M88,82 C94,68 156,66 168,82 C156,74 104,74 88,82 Z" fill="{brim}"/>'
            f'<path d="M72,78 C70,46 116,32 158,40 C180,45 186,64 168,76 C142,68 102,70 72,78 Z" fill="{color}"/>'
            f'<rect x="126" y="28" width="6" height="10" rx="3" fill="{color}"/>'
        )
    if style == 'fedora_bob':
        hat_c = ICE_DARK if silhouette else '#BF2848'
        fold_c = ICE_MID if silhouette else '#E1495C'
        band_c = ICE_ACCENT if silhouette else '#392338'
        return (
            f'<path d="M84,68 L96,35 Q99,27 107,29 L127,36 L143,27 Q151,24 156,32 '
            f'L172,62 Z" fill="{hat_c}"/>'
            f'<path d="M96,35 Q99,27 107,29 L127,36 L120,66 L84,68 Z" fill="{fold_c}"/>'
            f'<path d="M88,57 Q128,61 166,50 L172,62 Q130,74 84,68 Z" fill="{band_c}"/>'
            f'<path d="M49,77 Q89,65 127,65 Q169,61 204,62 Q177,82 126,84 '
            f'Q81,89 49,77 Z" fill="{hat_c}"/>'
        )
    if style == 'sleek_bob':
        return (
            f'<path d="M86,94 C86,58 108,44 136,46 C158,48 172,64 170,92 '
            f'C154,70 134,64 112,76 C98,84 90,88 86,94 Z" fill="{color}"/>'
        )
    if style in ('blunt_bob', 'bob_bangs'):
        return f'<path d="M84,86 C86,54 106,44 128,44 C150,44 170,54 172,86 Z" fill="{color}"/>'
    if style == 'scholar':
        return (
            f'<path d="M84,94 C82,58 102,44 128,44 C154,44 174,58 172,94 '
            f'C166,70 152,60 128,60 C104,60 90,70 84,94 Z" fill="{color}"/>'
        )
    if style == 'chef_toque':
        band = '#DDEAF8' if silhouette else '#E2E8F0'
        return (
            f'<path d="M88,62 C68,54 72,24 102,28 C112,18 144,18 154,28 C184,24 188,54 168,62 L166,82 L90,82 Z" fill="{color}"/>'
            f'<rect x="90" y="68" width="76" height="14" rx="2" fill="{band}"/>'
        )
    if style in ('high_bun', 'chignon', 'braid_bun'):
        return (
            f'<path d="M86,96 C84,60 104,46 128,46 C152,46 172,60 170,96 '
            f'C156,74 140,68 128,74 C116,68 100,74 86,96 Z" fill="{color}"/>'
        )
    if style == 'cap':
        brim = ICE_ACCENT if silhouette else '#1D4ED8'
        return (
            f'<path d="M84,78 C84,46 104,36 128,36 C152,36 172,46 172,78 Z" fill="{color}"/>'
            f'<path d="M80,78 Q128,66 176,78 Q128,85 80,78 Z" fill="{brim}"/>'
        )
    if style == 'sunhat':
        band = ICE_ACCENT if silhouette else '#16A34A'
        return (
            f'<path d="M88,74 C90,46 106,38 128,38 C150,38 166,46 168,74 Z" fill="{color}"/>'
            f'<rect x="89" y="64" width="78" height="8" fill="{band}"/>'
            f'<path d="M52,76 Q128,64 204,76 Q128,84 52,76 Z" fill="{color}"/>'
        )
    if style == 'quiff':
        return (
            f'<path d="M84,92 C82,56 102,38 136,40 C162,42 176,58 170,90 '
            f'C158,68 136,62 108,68 C94,72 88,82 84,92 Z" fill="{color}"/>'
        )
    if style in ('silver_part', 'side_part'):
        return (
            f'<path d="M84,92 C84,58 104,44 130,44 C156,44 172,60 172,92 '
            f'C160,72 142,64 114,66 C98,68 90,78 84,92 Z" fill="{color}"/>'
        )
    if style == 'long_wave':
        return (
            f'<path d="M86,94 C86,58 106,46 130,46 C154,46 170,60 170,94 '
            f'C156,72 138,66 118,74 C102,80 92,86 86,94 Z" fill="{color}"/>'
        )
    if style == 'fire_helmet':
        crest = ICE_LIGHT if silhouette else '#FACC15'
        return (
            f'<path d="M82,78 C84,44 104,34 128,34 C152,34 172,44 174,78 Z" fill="{color}"/>'
            f'<polygon points="118,44 138,44 134,66 122,66" fill="{crest}"/>'
            f'<path d="M66,78 Q128,70 190,78 Q128,86 66,78 Z" fill="{color}"/>'
        )
    if style == 'aviator':
        return (
            f'<path d="M80,98 C78,56 100,40 128,40 C156,40 178,56 176,98 '
            f'L170,122 L164,92 C152,74 104,74 92,92 L86,122 Z" fill="{color}"/>'
        )
    if style == 'baker_beret':
        return f'<path d="M76,80 C70,46 102,32 134,34 C166,36 184,54 176,80 C156,70 100,70 76,80 Z" fill="{color}"/>'
    if style == 'trilby':
        band = ICE_ACCENT if silhouette else '#0F172A'
        return (
            f'<path d="M88,76 L98,40 Q128,33 158,40 L168,76 Z" fill="{color}"/>'
            f'<rect x="91" y="64" width="74" height="8" fill="{band}"/>'
            f'<path d="M66,76 Q128,68 190,76 Q128,84 66,76 Z" fill="{color}"/>'
        )
    if style == 'ponytail':
        return f'<path d="M86,92 C86,58 106,46 128,46 C150,46 170,58 170,92 C156,72 100,72 86,92 Z" fill="{color}"/>'
    if style == 'curly':
        return (
            f'<path d="M78,92 C72,68 86,46 106,42 C118,34 138,34 150,42 C170,46 184,68 178,92 '
            f'C164,72 92,72 78,92 Z" fill="{color}"/>'
        )
    if style == 'nurse_updo':
        cap = ICE_LIGHT if silhouette else '#FFFFFF'
        cross = ICE_ACCENT if silhouette else '#EF4444'
        return (
            f'<path d="M86,92 C86,58 106,46 128,46 C150,46 170,58 170,92 C156,72 100,72 86,92 Z" fill="{color}"/>'
            f'<polygon points="96,48 160,48 152,30 104,30" fill="{cap}"/>'
            f'<rect x="125" y="34" width="6" height="11" fill="{cross}"/>'
            f'<rect x="122.5" y="36.5" width="11" height="6" fill="{cross}"/>'
        )
    if style == 'captain_cap':
        top = ICE_LIGHT if silhouette else '#FFFFFF'
        stripe = ICE_ACCENT if silhouette else '#FBBF24'
        return (
            f'<path d="M82,66 L74,42 Q128,28 182,42 L174,66 Z" fill="{top}"/>'
            f'<rect x="84" y="64" width="88" height="12" fill="{color}"/>'
            f'<rect x="86" y="63" width="84" height="3.5" fill="{stripe}"/>'
            f'<path d="M80,76 Q128,86 176,76 Z" fill="{color}"/>'
        )
    return (
        f'<path d="M82,92 C80,58 100,42 128,42 C156,42 176,58 174,92 '
        f'L164,74 L152,80 L138,66 L122,76 L108,66 L94,78 Z" fill="{color}"/>'
    )


def _facial_hair(beard, hair_color, silhouette):
    if not beard:
        return ''
    if silhouette:
        c = ICE_LIGHT if beard == 'mustache_white' else ICE_ACCENT
    else:
        c = '#F8FAFC' if beard == 'mustache_white' else (
            '#3A2A22' if hair_color[:2] in ('#F', '#E', '#D', '#C') else hair_color
        )
    if beard == 'full':
        return (
            f'<path d="M89,114 C90,142 108,158 128,160 C148,158 166,142 167,114 '
            f'L160,114 C156,128 146,136 128,136 C110,136 100,128 96,114 Z" fill="{c}"/>'
            f'<path d="M110,129 Q128,122 146,129 Q138,136 128,133 Q118,136 110,129 Z" fill="{c}"/>'
        )
    if beard == 'goatee':
        return f'<path d="M118,143 Q128,153 138,143 Q134,154 128,155 Q122,154 118,143 Z" fill="{c}"/>'
    if beard in ('mustache', 'mustache_white'):
        return f'<path d="M110,128 Q120,120 128,126 Q136,120 146,128 Q136,135 128,131 Q120,135 110,128 Z" fill="{c}"/>'
    if beard == 'stubble':
        return '<path d="M94,122 C96,142 110,152 128,154 C146,152 160,142 162,122 C152,136 104,136 94,122 Z" fill="#0F2942" fill-opacity="0.14"/>'
    return ''


def _eyewear_svg(eyewear, silhouette):
    c = ICE_ACCENT if silhouette else '#1E293B'
    lens = ICE_LIGHT if silhouette else '#FFFFFF'
    if eyewear == 'round':
        return (
            f'<circle cx="110" cy="102" r="12" fill="{lens}" fill-opacity="0.25" stroke="{c}" stroke-width="3.2"/>'
            f'<circle cx="146" cy="102" r="12" fill="{lens}" fill-opacity="0.25" stroke="{c}" stroke-width="3.2"/>'
            f'<path d="M122,101 Q128,98 134,101 M88,99 L98,101 M158,101 L168,99" fill="none" stroke="{c}" stroke-width="2.8"/>'
        )
    if eyewear in ('rect', 'cat_eye'):
        return (
            f'<rect x="96" y="93" width="26" height="17" rx="4" fill="{lens}" fill-opacity="0.25" stroke="{c}" stroke-width="3.4"/>'
            f'<rect x="134" y="93" width="26" height="17" rx="4" fill="{lens}" fill-opacity="0.25" stroke="{c}" stroke-width="3.4"/>'
            f'<path d="M122,99 H134 M88,97 L96,98 M160,98 L168,97" fill="none" stroke="{c}" stroke-width="3"/>'
        )
    if eyewear == 'cap_goggles':
        g_fill = ICE_LIGHT if silhouette else '#BAE6FD'
        return (
            f'<circle cx="112" cy="58" r="10" fill="{g_fill}" stroke="{c}" stroke-width="3.5"/>'
            f'<circle cx="144" cy="58" r="10" fill="{g_fill}" stroke="{c}" stroke-width="3.5"/>'
            f'<rect x="122" y="56" width="12" height="4" fill="{c}"/>'
        )
    return ''


def _expression_svg(slot, feature_c, lip_c, silhouette):
    if silhouette:
        if slot == 1:  # subtle blink on unopened silhouette
            return (
                f'<path d="M101,91 Q110,88 119,90 M137,90 Q146,88 155,91" fill="none" stroke="{feature_c}" stroke-width="3" stroke-linecap="round"/>'
                f'<path d="M103,103 Q110,107 117,103 M139,103 Q146,107 153,103" fill="none" stroke="{feature_c}" stroke-width="2.8" stroke-linecap="round"/>'
                f'<path d="M120,133 Q128,136 136,133" fill="none" stroke="{feature_c}" stroke-width="2.6" stroke-linecap="round"/>'
            )
        if slot == 2:  # subtle click reaction
            return (
                f'<path d="M101,87 Q110,82 119,87 M137,87 Q146,82 155,87" fill="none" stroke="{feature_c}" stroke-width="3" stroke-linecap="round"/>'
                f'<circle cx="110" cy="102" r="3.9" fill="{feature_c}"/><circle cx="146" cy="102" r="3.9" fill="{feature_c}"/>'
                f'<ellipse cx="128" cy="134" rx="4.5" ry="3.2" fill="{feature_c}"/>'
            )
        return (
            f'<path d="M101,91 Q110,88 119,90 M137,90 Q146,88 155,91" fill="none" stroke="{feature_c}" stroke-width="3" stroke-linecap="round"/>'
            f'<circle cx="110" cy="102" r="3.3" fill="{feature_c}"/><circle cx="146" cy="102" r="3.3" fill="{feature_c}"/>'
            f'<path d="M120,133 Q128,136 136,133" fill="none" stroke="{feature_c}" stroke-width="2.6" stroke-linecap="round"/>'
        )
    if slot == 1:  # blink
        return (
            f'<path d="M100,91 Q110,87 120,90 M136,90 Q146,87 156,91" fill="none" stroke="{feature_c}" stroke-width="3.2" stroke-linecap="round"/>'
            f'<path d="M102,103 Q110,108 118,103 M138,103 Q146,108 154,103" fill="none" stroke="{feature_c}" stroke-width="3" stroke-linecap="round"/>'
            f'<path d="M118,133 Q128,136 138,133" fill="none" stroke="{lip_c}" stroke-width="3" stroke-linecap="round"/>'
        )
    if slot == 2:  # surprised
        return (
            f'<path d="M100,86 Q110,80 120,86 M136,86 Q146,80 156,86" fill="none" stroke="{feature_c}" stroke-width="3.2" stroke-linecap="round"/>'
            f'<circle cx="110" cy="102" r="4.2" fill="{feature_c}"/><circle cx="146" cy="102" r="4.2" fill="{feature_c}"/>'
            f'<ellipse cx="128" cy="134" rx="5.5" ry="4" fill="{lip_c}"/>'
        )
    if slot == 3:  # relief / happy blink (INNOCENT)
        return (
            f'<path d="M100,88 Q110,84 120,88 M136,88 Q146,84 156,88" fill="none" stroke="{feature_c}" stroke-width="3.2" stroke-linecap="round"/>'
            f'<path d="M102,103 Q110,98 118,103 M138,103 Q146,98 154,103" fill="none" stroke="{feature_c}" stroke-width="3" stroke-linecap="round"/>'
            f'<path d="M116,131 Q128,140 140,131 Z" fill="#FFFFFF"/>'
            f'<path d="M116,131 Q128,140 140,131" fill="none" stroke="{lip_c}" stroke-width="2.6" stroke-linecap="round"/>'
        )
    if slot == 4:  # smile (INNOCENT)
        return (
            f'<path d="M100,88 Q110,84 120,88 M136,88 Q146,84 156,88" fill="none" stroke="{feature_c}" stroke-width="3.2" stroke-linecap="round"/>'
            f'<circle cx="110" cy="102" r="3.6" fill="{feature_c}"/><circle cx="146" cy="102" r="3.6" fill="{feature_c}"/>'
            f'<path d="M116,131 Q128,140 140,131 Z" fill="#FFFFFF"/>'
            f'<path d="M116,131 Q128,140 140,131" fill="none" stroke="{lip_c}" stroke-width="2.6" stroke-linecap="round"/>'
        )
    if slot == 5:  # caught
        return (
            f'<path d="M100,87 L120,93 M156,87 L136,93" fill="none" stroke="{feature_c}" stroke-width="3.4" stroke-linecap="round"/>'
            f'<circle cx="111" cy="103" r="3.6" fill="{feature_c}"/><circle cx="145" cy="103" r="3.6" fill="{feature_c}"/>'
            f'<path d="M118,136 Q128,130 138,136" fill="none" stroke="{lip_c}" stroke-width="3" stroke-linecap="round"/>'
        )
    if slot == 6:  # downcast resting pose
        return (
            f'<path d="M100,91 L120,94 M156,91 L136,94" fill="none" stroke="{feature_c}" stroke-width="3.2" stroke-linecap="round"/>'
            f'<path d="M102,103 Q110,109 118,105 M138,105 Q146,109 154,103" fill="none" stroke="{feature_c}" stroke-width="3" stroke-linecap="round"/>'
            f'<path d="M118,136 Q128,131 138,136" fill="none" stroke="{lip_c}" stroke-width="3" stroke-linecap="round"/>'
        )
    # 0 neutral
    return (
        f'<path d="M100,90 Q110,86 120,89 M136,89 Q146,86 156,90" fill="none" stroke="{feature_c}" stroke-width="3.2" stroke-linecap="round"/>'
        f'<circle cx="110" cy="102" r="3.6" fill="{feature_c}"/><circle cx="146" cy="102" r="3.6" fill="{feature_c}"/>'
        f'<path d="M118,133 Q128,137 138,133" fill="none" stroke="{lip_c}" stroke-width="3" stroke-linecap="round"/>'
    )


@lru_cache(maxsize=512)
def portrait_svg(portrait_id: int, slot: int = 0, silhouette: bool = False) -> str:
    """Return a 256x256 lineless paper-cut flat-vector portrait SVG."""
    spec = CHARACTER_SPECS[portrait_id % PORTRAIT_COUNT]
    skin_key, face, hair_style, hair_color, outfit, ga, gb, eyewear, beard, prop_head = spec

    if silhouette:
        skin, skin_shadow, skin_cast = ICE_SKIN
        h_col = ICE_DARK if hair_color != '#F5F9FF' else ICE_LIGHT
        out_a = ICE_LIGHT if ga.startswith('#F') else ICE_DARK
        out_b = ICE_ACCENT if not gb.startswith('#F') else ICE_LIGHT
        feat_c = ICE_ACCENT
        lip_c = ICE_ACCENT
    else:
        skin, skin_shadow, skin_cast = SKIN_TONES[skin_key]
        h_col = hair_color
        out_a, out_b = ga, gb
        feat_c = '#231F20'
        lip_c = '#B84A39'

    head_d, right_d = _head_paths(face)
    hair_front = _hair_front_and_hat(hair_style, h_col, prop_head, silhouette)
    eyewear_svg = _eyewear_svg(eyewear, silhouette)
    if eyewear == 'cap_goggles':
        # Goggles sit on top of the hat or hair, unlike glasses worn on the face.
        hair_front += eyewear_svg
        eyewear_svg = ''

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">'
        '<g transform="translate(0 12)">'
        f'{_hair_back(hair_style, h_col, silhouette)}'
        f'<path d="M108,140 L108,184 Q128,196 148,184 L148,140 Z" fill="{skin}"/>'
        f'<path d="M128,140 L148,140 L148,184 Q138,190 128,190 Z" fill="{skin_shadow}"/>'
        f'<path d="M108,144 Q128,166 148,150 L148,140 L108,140 Z" fill="{skin_cast}"/>'
        f'{_outfit_svg(outfit, out_a, out_b, prop_head, silhouette)}'
        f'<path d="M88,98 C80,98 79,116 88,117 Z" fill="{skin}"/>'
        f'<path d="M168,98 C176,98 177,116 168,117 Z" fill="{skin_shadow}"/>'
        f'<path d="{head_d}" fill="{skin}"/>'
        f'<path d="{right_d}" fill="{skin_shadow}"/>'
        f'<polygon points="128,94 135,117 125,119" fill="{skin_cast}"/>'
        f'{_facial_hair(beard, h_col, silhouette)}'
        f'{_expression_svg(slot, feat_c, lip_c, silhouette)}'
        f'{eyewear_svg}'
        f'{hair_front}'
        '</g></svg>'
    )


@lru_cache(maxsize=1)
def backdrop_svg() -> str:
    """Alto's Odyssey x Gamma 5 flat-vector sky, peaks, meadow hills & coral poppies."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" preserveAspectRatio="none">'
        '<defs>'
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#1E7AE6"/>'
        '<stop offset="58%" stop-color="#53A9F8"/>'
        '<stop offset="100%" stop-color="#8FD2FF"/>'
        '</linearGradient>'
        '</defs>'
        '<rect width="1600" height="900" fill="url(#sky)"/>'
        # Distant angular flat-vector mountain peaks along scenic side margins
        '<polygon points="-50,865 115,515 315,865" fill="#2B86E3"/>'
        '<polygon points="115,515 215,865 315,865" fill="#1F71CA"/>'
        '<polygon points="1285,865 1495,495 1665,865" fill="#2B86E3"/>'
        '<polygon points="1495,495 1580,865 1665,865" fill="#1F71CA"/>'
        # Midground rolling hills
        '<path d="M-20,900 L-20,792 Q340,735 790,822 T1620,782 L1620,900 Z" fill="#2FA866"/>'
        # Foreground sunlit spring meadow
        '<path d="M-20,900 L-20,836 Q420,792 860,848 T1620,824 L1620,900 Z" fill="#52CC7A"/>'
        '<path d="M-20,900 L-20,868 Q480,842 980,874 T1620,858 L1620,900 Z" fill="#6EE089"/>'
        # Crisp flat-vector coral poppies tucked cleanly into outer margins & foreground rim
        '<g stroke="#1E7E48" stroke-width="2.4" stroke-linecap="round" fill="none">'
        '<path d="M22,900 Q24,884 19,872"/><path d="M44,900 Q41,888 46,879"/>'
        '<path d="M138,900 L140,890"/><path d="M1462,900 L1459,890"/>'
        '<path d="M1556,900 Q1559,886 1553,876"/><path d="M1580,900 Q1577,883 1583,870"/>'
        '</g>'
        '<g fill="#FF4D5E">'
        '<circle cx="19" cy="870" r="6.8"/><circle cx="46" cy="877" r="5.4"/>'
        '<circle cx="140" cy="889" r="5.2"/><circle cx="1459" cy="889" r="5.2"/>'
        '<circle cx="1553" cy="874" r="5.8"/><circle cx="1583" cy="868" r="6.8"/>'
        '</g>'
        '<g fill="#FACC15">'
        '<circle cx="19" cy="870" r="2.2"/><circle cx="46" cy="877" r="1.8"/>'
        '<circle cx="140" cy="889" r="1.7"/><circle cx="1459" cy="889" r="1.7"/>'
        '<circle cx="1553" cy="874" r="1.9"/><circle cx="1583" cy="868" r="2.2"/>'
        '</g>'
        '</svg>'
    )


_PROFESSION_PATHS = {
    'medical': (
        '<path d="M26,20 V42 C26,56 50,56 50,42 V20 M22,20 H30 M46,20 H54" '
        'fill="none" stroke="{c}" stroke-width="5.5" stroke-linecap="round"/>'
        '<path d="M38,53 V68 C38,80 68,80 68,64 V52" fill="none" stroke="{c}" stroke-width="5.5" stroke-linecap="round"/>'
        '<circle cx="68" cy="46" r="8" fill="none" stroke="{c}" stroke-width="5.5"/>'
    ),
    'painting': (
        '<path d="M48,16 C26,16 14,32 16,52 C18,70 34,80 52,78 C62,77 66,70 60,62 '
        'C56,56 60,50 68,50 C78,50 82,42 80,32 C76,20 62,16 48,16 Z" fill="{c}"/>'
        '<circle cx="34" cy="36" r="4.5" fill="{bg}"/><circle cx="48" cy="30" r="4.5" fill="{bg}"/>'
        '<circle cx="62" cy="36" r="4.5" fill="{bg}"/><circle cx="32" cy="52" r="4.5" fill="{bg}"/>'
    ),
    'journalism': (
        '<rect x="16" y="28" width="64" height="46" rx="7" fill="{c}"/>'
        '<path d="M34,28 L40,18 H56 L62,28 Z" fill="{c}"/>'
        '<circle cx="48" cy="51" r="13" fill="{bg}"/><circle cx="48" cy="51" r="7" fill="{c}"/>'
    ),
    'law': (
        '<line x1="48" y1="16" x2="48" y2="78" stroke="{c}" stroke-width="5.5" stroke-linecap="round"/>'
        '<line x1="20" y1="28" x2="76" y2="28" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
        '<line x1="32" y1="78" x2="64" y2="78" stroke="{c}" stroke-width="6" stroke-linecap="round"/>'
        '<path d="M22,28 L13,50 H31 Z M74,28 L65,50 H83 Z" fill="none" stroke="{c}" stroke-width="3.5" stroke-linejoin="round"/>'
        '<path d="M11,50 Q22,60 33,50 Z M63,50 Q74,60 85,50 Z" fill="{c}"/>'
    ),
    'academic': (
        '<polygon points="48,18 14,34 48,50 82,34" fill="{c}"/>'
        '<path d="M26,42 V60 C26,68 70,68 70,60 V42 Z" fill="{c}" fill-opacity="0.85"/>'
        '<line x1="78" y1="36" x2="78" y2="62" stroke="{c}" stroke-width="4.5" stroke-linecap="round"/>'
    ),
    'cooking': (
        '<path d="M18,62 C18,40 32,28 48,28 C64,28 78,40 78,62 Z" fill="{c}"/>'
        '<circle cx="48" cy="23" r="5" fill="{c}"/>'
        '<rect x="12" y="65" width="72" height="7" rx="3.5" fill="{c}"/>'
    ),
    'library': (
        '<path d="M16,26 Q32,22 48,30 Q64,22 80,26 V70 Q64,66 48,74 Q32,66 16,70 Z" '
        'fill="none" stroke="{c}" stroke-width="5.5" stroke-linejoin="round"/>'
        '<line x1="48" y1="30" x2="48" y2="74" stroke="{c}" stroke-width="4.5"/>'
    ),
    'mechanics': (
        '<path d="M68,20 C58,18 50,26 52,36 L20,68 C16,72 16,78 20,82 C24,86 30,86 34,82 '
        'L66,50 C76,52 84,44 82,34 L71,43 L62,40 L59,31 Z" fill="{c}"/>'
        '<path d="M20,20 L28,16 L38,28 L34,34 L62,62 L72,62 L82,74 L74,82 L62,72 L62,62 L34,34 L28,38 Z" fill="{c}"/>'
    ),
    'gardening': (
        '<rect x="28" y="40" width="36" height="34" rx="5" fill="{c}"/>'
        '<path d="M28,48 L12,34 M10,30 L16,38" stroke="{c}" stroke-width="5.5" stroke-linecap="round"/>'
        '<path d="M64,44 C78,44 78,68 64,68" fill="none" stroke="{c}" stroke-width="5.5"/>'
        '<path d="M36,40 C36,26 56,26 56,40" fill="none" stroke="{c}" stroke-width="5"/>'
    ),
    'photography': (
        '<rect x="16" y="30" width="64" height="44" rx="6" fill="none" stroke="{c}" stroke-width="5.5"/>'
        '<circle cx="48" cy="52" r="12" fill="none" stroke="{c}" stroke-width="5"/>'
        '<rect x="58" y="20" width="14" height="10" rx="2" fill="{c}"/>'
    ),
    'architecture': (
        '<polygon points="20,76 74,76 20,22" fill="none" stroke="{c}" stroke-width="5.5" stroke-linejoin="round"/>'
        '<line x1="56" y1="18" x2="42" y2="76" stroke="{c}" stroke-width="4.5" stroke-linecap="round"/>'
        '<line x1="56" y1="18" x2="70" y2="76" stroke="{c}" stroke-width="4.5" stroke-linecap="round"/>'
    ),
    'watchmaking': (
        '<circle cx="48" cy="52" r="24" fill="none" stroke="{c}" stroke-width="5.5"/>'
        '<rect x="42" y="18" width="12" height="8" rx="2" fill="{c}"/>'
        '<path d="M48,38 V52 L58,58" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
    ),
    'musician': (
        '<circle cx="32" cy="68" r="10" fill="{c}"/><circle cx="66" cy="62" r="10" fill="{c}"/>'
        '<path d="M40,68 V26 L74,20 V62" fill="none" stroke="{c}" stroke-width="5.5" stroke-linejoin="round"/>'
    ),
    'firefighting': (
        '<path d="M48,16 C48,16 72,38 72,58 C72,72 61,80 48,80 C35,80 24,72 24,58 C24,44 36,34 48,16 Z" fill="{c}"/>'
        '<path d="M48,46 C54,54 56,60 56,65 C56,70 52,74 48,74 C44,74 40,70 40,65 C40,60 42,54 48,46 Z" fill="{bg}"/>'
    ),
    'floristry': (
        '<path d="M48,54 V80 M48,68 Q34,64 30,54 M48,72 Q62,68 66,58" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
        '<path d="M32,26 C32,46 64,46 64,26 L56,34 L48,22 L40,34 Z" fill="{c}"/>'
    ),
    'tailoring': (
        '<circle cx="30" cy="68" r="10" fill="none" stroke="{c}" stroke-width="5"/>'
        '<circle cx="66" cy="68" r="10" fill="none" stroke="{c}" stroke-width="5"/>'
        '<path d="M37,61 L68,20 M59,61 L28,20" stroke="{c}" stroke-width="5.5" stroke-linecap="round"/>'
    ),
    'aviation': (
        '<path d="M48,16 L54,42 L82,52 L82,60 L54,54 L53,72 L64,78 V83 L48,79 L32,83 V78 L43,72 L42,54 L14,60 L14,52 L42,42 Z" fill="{c}"/>'
    ),
    'baking': (
        '<path d="M18,58 C18,36 34,26 48,26 C62,26 78,36 78,58 C70,66 26,66 18,58 Z" fill="{c}"/>'
        '<path d="M36,30 L32,58 M48,26 L48,60 M60,30 L64,58" stroke="{bg}" stroke-width="3.5"/>'
    ),
    'detective': (
        '<circle cx="42" cy="42" r="20" fill="none" stroke="{c}" stroke-width="6"/>'
        '<line x1="57" y1="57" x2="78" y2="78" stroke="{c}" stroke-width="7" stroke-linecap="round"/>'
    ),
    'engineering': (
        '<circle cx="48" cy="48" r="16" fill="none" stroke="{c}" stroke-width="8"/>'
        '<path d="M48,18 V28 M48,68 V78 M18,48 H28 M68,48 H78 M27,27 L34,34 M62,62 L69,69 M69,27 L62,34 M34,62 L27,69" '
        'stroke="{c}" stroke-width="7" stroke-linecap="round"/>'
    ),
    'bookselling': (
        '<rect x="20" y="22" width="56" height="15" rx="3" fill="{c}"/>'
        '<rect x="24" y="42" width="52" height="15" rx="3" fill="{c}" fill-opacity="0.82"/>'
        '<rect x="18" y="62" width="58" height="15" rx="3" fill="{c}"/>'
    ),
    'nursing': (
        '<rect x="38" y="20" width="20" height="56" rx="4" fill="{c}"/>'
        '<rect x="20" y="38" width="56" height="20" rx="4" fill="{c}"/>'
    ),
    'sailing': (
        '<line x1="48" y1="22" x2="48" y2="76" stroke="{c}" stroke-width="5.5" stroke-linecap="round"/>'
        '<circle cx="48" cy="20" r="6" fill="none" stroke="{c}" stroke-width="4.5"/>'
        '<line x1="34" y1="36" x2="62" y2="36" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
        '<path d="M22,54 C24,72 36,78 48,78 C60,78 72,72 74,54" fill="none" stroke="{c}" stroke-width="5.5" stroke-linecap="round"/>'
    ),
    'music_teaching': (
        '<polygon points="30,78 66,78 56,18 40,18" fill="none" stroke="{c}" stroke-width="5.5" stroke-linejoin="round"/>'
        '<line x1="48" y1="70" x2="68" y2="28" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
    ),
    'botany': (
        '<path d="M48,80 V38" stroke="{c}" stroke-width="5.5" stroke-linecap="round"/>'
        '<path d="M48,58 C26,58 20,38 24,26 C40,26 48,40 48,58 Z" fill="{c}"/>'
        '<path d="M48,46 C70,46 76,26 72,16 C56,16 48,30 48,46 Z" fill="{c}"/>'
    ),
}


@lru_cache(maxsize=64)
def profession_svg(category: str, color: str = '#C4DDF5', card_bg: str = '#FFFFFF') -> str:
    body = _PROFESSION_PATHS.get(category, _PROFESSION_PATHS['detective']).format(c=color, bg=card_bg)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" width="96" height="96">{body}</svg>'
