"""Check x100 import and Halo scenery export conversion without game tools."""
import sys,tempfile
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import blender_ops,catalog,ui
blender_ops.ensure_exporter=lambda:None
captured=[]
class MaterialSettings(bpy.types.PropertyGroup):
    name_override:bpy.props.StringProperty()
    is_bm:bpy.props.BoolProperty()
    render_only:bpy.props.BoolProperty()
bpy.utils.register_class(MaterialSettings)
bpy.types.Material.ass_jms=bpy.props.PointerProperty(type=MaterialSettings)

class FakeASS(bpy.types.Operator):
    bl_idname='export_scene.ass';bl_label='Test exporter'
    filepath:bpy.props.StringProperty()
    game_title:bpy.props.StringProperty()
    scale_enum:bpy.props.StringProperty()
    hidden_geo:bpy.props.BoolProperty()
    nonrender_geo:bpy.props.BoolProperty()
    apply_modifiers:bpy.props.BoolProperty()
    triangulate_faces:bpy.props.BoolProperty()
    edge_split:bpy.props.BoolProperty()
    clean_normalize_weights:bpy.props.BoolProperty()
    def execute(self,context):
        captured.extend((obj.matrix_world.copy(),[v.co.copy() for v in obj.data.vertices]) for obj in context.scene.objects)
        Path(self.filepath).write_text('synthetic exporter')
        return {'FINISHED'}
bpy.utils.register_class(FakeASS)
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'preview.json'
    catalog.write_json(path,dict(materials=[],meshes=[dict(positions=[[0,0,0],[1,0,0],[0,1,0]],uv=[],normals=[],segments=[dict(indices=[0,1,2],material=-1)])]))
    for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
    obj=blender_ops.place(dict(id='fixture',name='scenery',kind='scenery',scenery_tag='fixture'),path,{},location=(200,300,400))
    bpy.context.view_layer.update()
    assert tuple(obj.scale)==(100,100,100)
    placements=blender_ops.export_scene({'kit':tmp},Path(tmp)/'test.ASS')
    assert placements[0]['position']==[2,3,4] and placements[0]['scale']==1
    obj.scale=(200,200,200);bpy.context.view_layer.update()
    placements=blender_ops.export_scene({'kit':tmp},Path(tmp)/'test.ASS')
    assert placements[0]['scale']==2
    # Authored geometry uses the same working units; ASS translations remain
    # in tool units while its linear transform cancels the exporter's x100.
    terrain=bpy.data.objects.new('authored',obj.data.copy());bpy.context.collection.objects.link(terrain)
    terrain.data.vertices[1].co.x=100;terrain.location=(200,0,0)
    terrain.data.materials.append(bpy.data.materials.new('+sky'))
    captured.clear();blender_ops.export_scene({'kit':tmp},Path(tmp)/'test.ASS')
    transform,vertices=captured[0]
    assert abs(transform[0][0]-.01)<1e-6 and transform.translation.x==200
    assert abs((transform@(vertices[1]*100)).x-300)<1e-4
    s=bpy.context.scene.halo_bridge
    for level in ('jungle','high_ground'):
        item=s.assets.add();item.name='Tree';item.level=level;item.category='Vegetation';item.kind='instance'
    s.filter_level='jungle';assert [a.level for a in s.assets if ui.row_visible(s,a)]==['jungle']
    s.filter_level='__ALL__';assert len([a for a in s.assets if ui.row_visible(s,a)])==2
print('PASS: x100 import, scenery position/scale conversion, map filtering')
