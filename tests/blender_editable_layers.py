"""Every terrain shader layer (up to four) gets its own collapsible section and Paint button."""
import json, sys
from pathlib import Path
from types import SimpleNamespace
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui, compat

class Layout:
    def __init__(self, log): self.log = log
    def row(self, **kw): return self
    def box(self): return self
    def label(self, **kw): self.log.append(('label', kw.get('text')))
    def prop(self, *a, **kw): pass
    def template_ID(self, *a, **kw): pass
    def separator(self, **kw): pass
    def operator(self, name, **kw):
        op = SimpleNamespace(); self.log.append(('operator', name, kw.get('text'), op)); return op

sections = []
def section(layout, idname, title, icon='NONE', default_closed=False):
    sections.append((idname, title, default_closed))
    return layout, (None if default_closed else layout)  # header only while collapsed
compat.section = section

mesh = bpy.data.meshes.new('t'); mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)]); mesh.uv_layers.new()
obj = bpy.data.objects.new('t', mesh); bpy.context.collection.objects.link(obj)
mat = bpy.data.materials.new('four layer'); compat.enable_nodes(mat)
for i in range(1, 5):
    node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.name = 'Shader %d' % i; node.label = 'layer_%d_texture' % i
mat['hb_custom_shader'] = 'terrain'; mat['hb_layers'] = json.dumps(['Shader %d' % i for i in range(1, 5)])
mesh.materials.append(mat)
log = []
ui.draw_editable_materials(Layout(log), SimpleNamespace(active_object=obj))
layer_sections = [s for s in sections if s[0].startswith('hb_layer_')]
assert [s[0] for s in layer_sections] == ['hb_layer_0', 'hb_layer_1', 'hb_layer_2', 'hb_layer_3'], layer_sections
assert all(s[2] for s in layer_sections), 'shader layers start collapsed'
assert layer_sections[3][1] == 'Shader 4 — layer_4_texture'
paints = [entry[3].paint_channel for entry in log if entry[0] == 'operator' and entry[1] == 'halo_bridge.custom_paint' and hasattr(entry[3], 'paint_channel')]
assert paints[:4] == [0, 1, 2, 3] and 4 in paints, paints  # 0-3 = shaders 1-4 (4th is white), 4 = original blend
halo_bridge.unregister()
print('PASS four shader layers: four collapsed sections with Paint buttons for channels 0-3 plus original blend')
