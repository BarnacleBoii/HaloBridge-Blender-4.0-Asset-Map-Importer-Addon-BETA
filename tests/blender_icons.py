"""Every icon name HaloBridge draws must exist in this Blender.

An unknown icon raises inside Panel.draw, and Blender silently stops drawing the
rest of the panel (Blender 5.x renamed SEQUENCE_COLOR_* to STRIP_COLOR_*, which
hid everything below Preview Mode, including Prepare for Sapien). Mock layouts in
the other UI tests accept any icon, so this check uses Blender's real icon list.
"""
import re, sys
from pathlib import Path
import bpy
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from halo_bridge import compat
valid = {item.identifier for item in bpy.types.UILayout.bl_rna.functions['label'].parameters['icon'].enum_items}
pattern = re.compile(r"""icon\s*=\s*['"]([A-Z0-9_]+)['"]|['"]([A-Z][A-Z0-9_]{2,})['"]\s+if\s|else\s+['"]([A-Z][A-Z0-9_]{2,})['"]""")
missing = []
for path in sorted((root / 'halo_bridge').rglob('*.py')):
    if 'vendor' in path.parts:
        continue
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if 'icon' not in line or 'compat.icon(' in line:
            continue
        for match in pattern.finditer(line):
            name = next(g for g in match.groups() if g)
            if name not in valid:
                missing.append('%s:%d %s' % (path.name, number, name))
assert not missing, 'Icons unknown to Blender %s: %s' % (bpy.app.version_string, missing)
# template_list with an unknown UIList type draws an error box instead of the list.
import halo_bridge
halo_bridge.register()
lists = re.compile(r"""template_list\(\s*['"]([A-Za-z0-9_]+)['"]""")
unknown = ['%s:%d %s' % (path.name, number, m.group(1))
           for path in sorted((root / 'halo_bridge').rglob('*.py')) if 'vendor' not in path.parts
           for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1)
           for m in lists.finditer(line) if not hasattr(bpy.types, m.group(1))]
halo_bridge.unregister()
assert not unknown, 'UIList types unknown to Blender: %s' % unknown
assert compat.icon('NOT_AN_ICON', 'INFO') == 'INFO' and compat.icon('NOT_AN_ICON') == 'NONE'
assert compat.icon('STRIP_COLOR_04', 'SEQUENCE_COLOR_04') in valid
print('PASS all HaloBridge icon and UIList names exist in Blender', bpy.app.version_string)
