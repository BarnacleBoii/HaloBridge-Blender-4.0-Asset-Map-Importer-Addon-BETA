"""Per-object omissions, used material slots, filter state and shader selection."""
import sys,tempfile
from pathlib import Path
import bpy
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,export_review,geometry_export,shader_choices,blender_ops
from halo_bridge.diagnostics import ValidationError
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
def triangle(name,mat):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(0,0,0),(100,0,0),(0,100,0)],[],[(0,1,2)])
    if mat:mesh.materials.append(mat)
    obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj);return obj
with tempfile.TemporaryDirectory() as tmp:
    tags=Path(tmp)/'tags';tags.mkdir();(tags/'terrain.shader').write_text('synthetic')
    good=bpy.data.materials.new('Halo terrain');good['hb_shader']='terrain'
    unused=bpy.data.materials.new('Unused ordinary material')
    floor=triangle('Valid terrain',good);floor.data.materials.append(unused)
    bad=triangle('Unassigned plane',unused)
    empty=triangle('Missing slot',None)
    bpy.context.view_layer.update()
    cfg={'kit':tmp,'skip_invalid':False}
    issues,used,_=export_review.inspect([floor,bad,empty],cfg)
    assert floor.name not in issues and used[floor.name]==[good]
    assert set(issues)=={bad.name,empty.name}
    try:ui.preparation_warnings(bpy.context,cfg)
    except ValidationError as e:assert 'Unassigned plane' in str(e) and 'Missing slot' in str(e)
    else:raise AssertionError('Invalid objects were not blocked by default')
    cfg['skip_invalid']=True
    warnings=ui.preparation_warnings(bpy.context,cfg)
    assert len([w for w in warnings if w.startswith('WILL NOT EXPORT')])==2
    # Exercise the complete Blender geometry staging route; stub only ASS IO.
    def capture(config,path):
        names=set(config['geometry_names'].values())
        assert names=={'Valid terrain'},names
        assert set(config['skipped_objects'])=={'Unassigned plane','Missing slot'}
        for o in bpy.context.scene.objects:
            assert unused not in list(o.data.materials)
        return []
    with patch.object(blender_ops,'ensure_exporter'),patch.object(blender_ops,'export_scene',side_effect=capture):
        # Temporary material flags belong to the installed exporter.
        import addon_utils;addon_utils.enable('io_scene_halo')
        geometry_export.export(cfg,Path(tmp)/'export.ASS')
    assert floor.name in bpy.context.scene.objects and bad.name in bpy.context.scene.objects
    assert list(floor.data.materials)==[good,unused]
    s=bpy.context.scene.halo_bridge;s.kit=tmp
    assert shader_choices.scan(tmp)==1
    s.shader_choice='terrain';bpy.context.view_layer.objects.active=bad
    ui.HBShader.run(None,bpy.context)
    assert unused['hb_shader']=='terrain' and unused['hb_shader_game']=='halo3'
    # Legacy .map/path casing and saved numeric selection must agree.
    s.assets.clear()
    for level in ['010_jungle','010_JUNGLE.map','levels\\010_jungle','100_citadel']:
        row=s.assets.add();row.level=level;row.category='Structures';row.kind='instance'
    ui._level_items_token=None;s.filter_level='010_jungle'
    assert sum(ui.row_visible(s,a) for a in s.assets)==3
    s.filter_level='__ALL__';assert sum(ui.row_visible(s,a) for a in s.assets)==4
    s.filter_level='010_jungle';assert sum(ui.row_visible(s,a) for a in s.assets)==3
print('PASS: unused slots ignored; invalid objects reviewed and omitted without scene edits; shader dropdown preserves tags; normalized level filter works')
