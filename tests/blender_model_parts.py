"""Region toggles preserve coordinates and separate into independent meshes."""
import sys,json,tempfile
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import model_parts,blender_ops
with tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'parts.json'
 parts=[]
 for i,choice in enumerate(('0:0','0:1','1:0')):
  parts.append(dict(name='part'+str(i),source_mesh=i,region='hull' if i<2 else 'hat',permutation='base' if i!=1 else 'damaged',choice=choice,positions=[[i,0,0],[i+1,0,0],[i,1,0]],uv=[[0,0],[1,0],[0,1]],normals=[[0,0,1]]*3,segments=[dict(material=0,indices=[0,1,2])]))
 data=dict(materials=[dict(id=0,name='test',shader='',textures=[],alpha='opaque')],meshes=parts)
 path.write_text(json.dumps(data))
 mesh=blender_ops.mesh_from_preview(path,'fixture',dict(data,meshes=[parts[0],parts[2]]))
 obj=bpy.data.objects.new('fixture',mesh);bpy.context.collection.objects.link(obj);obj['hb_parts_path']=str(path);obj['hb_parts_enabled']=json.dumps(['0:0','1:0']);obj['hb_parts_signature']=blender_ops.mesh_signature(mesh)
 obj.matrix_world=Matrix.Translation((10,20,30));matrix=obj.matrix_world.copy()
 model_parts.apply(obj,set());assert len(obj.data.polygons)==0
 model_parts.apply(obj,{'0:1','1:0'});assert len(obj.data.polygons)==2;assert obj.matrix_world==matrix
 model_parts.apply(obj,{'0:0','1:0'})
 expected=sorted(tuple(matrix@v.co) for v in obj.data.vertices)
 result=model_parts.separate(bpy.context,obj)
 actual=sorted(tuple(p.matrix_world@v.co) for p in result for v in p.data.vertices)
 assert actual==expected
 before=result[1].matrix_world.copy();result[0].location.x+=50;bpy.context.view_layer.update();assert result[1].matrix_world==before
 print('PASS: empty/all selection, variant switch, coordinate preservation, independently selectable pieces')

 mesh=blender_ops.mesh_from_preview(path,'all_fixture',dict(data,meshes=[parts[0]]))
 obj=bpy.data.objects.new('all_fixture',mesh);bpy.context.collection.objects.link(obj)
 obj['hb_parts_path']=str(path);obj['hb_parts_enabled']=json.dumps(['0:0']);obj['hb_parts_signature']=blender_ops.mesh_signature(mesh)
 obj.matrix_world=Matrix.Translation((40,50,60));matrix=obj.matrix_world.copy()
 result=model_parts.separate(bpy.context,obj,all_variants=True)
 assert len(result)==3
 assert len({p.data.as_pointer() for p in result})==3
 assert len(bpy.context.selected_objects)==1
 assert {p['hb_permutation'] for p in result}=={'base','damaged'}
 assert all(p.matrix_world==matrix for p in result)
 before=result[1].data.vertices[0].co.copy();result[0].data.vertices[0].co.x+=20
 assert result[1].data.vertices[0].co==before
 print('PASS: disabled variants included, independent mesh editing, preserved transforms, only one selected')
