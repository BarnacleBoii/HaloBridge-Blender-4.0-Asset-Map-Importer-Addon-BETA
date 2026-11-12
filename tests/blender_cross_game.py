"""Reach material conversion, UV tiling and source-scene preservation (no game data)."""
import sys,tempfile
from pathlib import Path
from unittest.mock import patch
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import cross_game,geometry_export,blender_ops,compat
blender_ops.ensure_exporter()
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.mesh.primitive_plane_add(size=100)
obj=bpy.context.object;obj['hb_id']='fixture';obj['hb_game']='reach';obj['hb_working_units']=100
mat=bpy.data.materials.new('reach fixture');compat.enable_nodes(mat);compat.set_alpha(mat,'clip');mat['hb_shader']='reach/only';obj.data.materials.append(mat)
bsdf=mat.node_tree.nodes.get('Principled BSDF');image=bpy.data.images.new('fixture',4,4,alpha=True)
image.pixels[:]=[.4,.3,.2,.5]*16
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
mapping=mat.node_tree.nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(2,3,1)
mat.node_tree.links.new(mapping.outputs[0],tex.inputs['Vector'])
mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
original_uv=[tuple(l.uv) for l in obj.data.uv_layers.active.data]
with tempfile.TemporaryDirectory() as tmp:
    cfg={'kit':tmp}
    def inspect(config,path):
        entry=config['converted_shaders'][0]
        assert entry['tiling']==(2,3)
        assert set(entry['maps'])=={'base_map','alpha_map'}
        assert all(Path(p).is_file() for p in entry['maps'].values())
        clone=next(o for o in bpy.context.scene.objects if o.name.lstrip('%').startswith('hb_'))
        assert not clone.name.startswith('%'), 'Asset-only scenes need a renderable structure mesh'
        assert clone.data.materials[0]['hb_shader']==entry['name']
        for actual,prior in zip(clone.data.uv_layers.active.data,original_uv):
            assert abs(actual.uv.x-prior[0]*2)<1e-6 and abs(actual.uv.y-prior[1]*3)<1e-6
        return []
    with patch.object(blender_ops,'export_scene',side_effect=inspect):geometry_export.export(cfg,Path(tmp)/'fixture.ASS')
    assert mat['hb_shader']=='reach/only' and [tuple(l.uv) for l in obj.data.uv_layers.active.data]==original_uv
    assert obj.data.materials[0]==mat and tex.image==image
    # Explicitly assigning an H3 shader opts out of conversion, even on Reach geometry.
    mat['hb_shader_game']='halo3';assert not cross_game.reach_materials([obj])
print('PASS Reach texture conversion, alpha, tiled export UVs and unchanged source meshes/materials')

