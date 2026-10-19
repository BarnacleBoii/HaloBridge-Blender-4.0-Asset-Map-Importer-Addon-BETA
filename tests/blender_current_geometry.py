"""Current geometry export keeps edits/modifiers and leaves source objects untouched."""
import sys,tempfile
from pathlib import Path
from unittest.mock import patch
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import geometry_export,blender_ops
blender_ops.ensure_exporter()
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);shader=root/'tags/test/ground.shader';shader.parent.mkdir(parents=True);shader.write_bytes(b'test')
    bpy.ops.mesh.primitive_cube_add(size=2,location=(200,300,0));source=bpy.context.object
    source['hb_map_reference']=True;source['hb_ignore']=True;source['hb_working_units']=100
    source.scale=(300,200,50);source.data.vertices[0].co.x=-1.25
    material=bpy.data.materials.new('ground');material['hb_shader']='test/ground';source.data.materials.append(material)
    other=source.copy();other.data=source.data;bpy.context.collection.objects.link(other);other.location=(500,300,0)
    removed=source.copy();removed.data=source.data;bpy.context.collection.objects.link(removed);bpy.data.objects.remove(removed,do_unlink=True)
    modifier=other.modifiers.new('Actual edit','BEVEL');modifier.width=.1;modifier.segments=1
    bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-3000))
    underground=bpy.context.object;underground['hb_working_units']=100;underground.data.materials.append(material)
    bpy.context.view_layer.update();before=source.matrix_world.copy();original_vertices=len(source.data.vertices)
    bpy.context.scene.cursor.location=(200,300,0)
    cfg={'kit':tmp}
    def inspect(config,path):
        objects=list(bpy.context.scene.objects);meshes=[o for o in objects if o.name.lstrip('%').startswith('hb_')]
        assert len(meshes)==3 and len(objects)==4
        assert len([o for o in meshes if not o.name.startswith('%')])==1
        assert config['structure_source'] in {source.name,other.name,underground.name}
        assert all(tuple(o.scale)==(1,1,1) for o in objects)
        assert abs(min(v.co.x for v in meshes[0].data.vertices)+3.75)<1e-5
        assert tuple(meshes[0].location)==(2,3,0)
        assert len(meshes[1].data.vertices)>original_vertices
        assert all(not o.get('hb_map_reference') for o in objects)
        assert config['shader_aliases']['test\\ground']['source']==str(shader)
        return []
    # Shader paths written by extraction are canonical backslashes.
    material['hb_shader']='test\\ground'
    messages=[]
    with patch.object(blender_ops,'export_scene',side_effect=inspect):geometry_export.export(cfg,root/'test.ass',progress=messages.append)
    assert any('Preparing asset 3/3:' in message for message in messages)
    assert any(source.name in message for message in messages)
    assert 'Writing geometry file' in messages[-1]
    assert source.matrix_world==before and len(source.data.vertices)==original_vertices
    assert source.data.vertices[0].co.x==-1.25
    assert len(bpy.context.scene.objects)==3
    assert cfg['spawn_position'][2]>0
print('PASS edited/deleted meshes, evaluated modifiers, normalized collision units and source preservation')
