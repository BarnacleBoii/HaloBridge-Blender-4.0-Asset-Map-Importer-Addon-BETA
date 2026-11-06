"""Editable material bake/export routing regression; synthetic images only."""
import sys,tempfile
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import editable_materials,cross_game,export_review
bpy.ops.mesh.primitive_plane_add();obj=bpy.context.object
base=bpy.data.materials.new('Source');base.use_nodes=True
tex=base.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.new('white',width=4,height=4);tex.image.generated_color=(1,1,1,1)
base.node_tree.links.new(tex.outputs['Color'],base.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);obj.data.materials.append(base)
mat=editable_materials.make(bpy.context,'terrain');mat['hb_bake_size']=512
for name,color in [('Grass',(0,1,0,1)),('Rock',(1,0,0,1)),('Dirt',(0,0,1,1))]:
 image=bpy.data.images.new(name,width=4,height=4);image.generated_color=color;mat.node_tree.nodes[name].image=image
mask=mat.node_tree.nodes['Paint Mask'].image;mask.pixels[:]=[1,0,0,1]*(1024*1024);mask.update()
issues,_,converted=export_review.inspect([obj],{'kit':''});assert not issues,issues
assert mat.as_pointer() in converted
scene=bpy.context.scene
with tempfile.TemporaryDirectory() as folder:
 result=editable_materials.bake(mat,folder)
 image=bpy.data.images.load(result['maps']['base_map']);pixel=image.pixels[:4]
 assert pixel[0]>.9 and pixel[1]<.1 and pixel[2]<.1,pixel
 bpy.data.images.remove(image)
assert bpy.context.scene==scene and obj.active_material==mat
assert base.node_tree.nodes.get('Principled BSDF') is not None
obj.data.uv_layers.active.data[0].uv.x=2
issues,_,_=export_review.inspect([obj],{'kit':''});assert '0-1' in str(issues)
print('PASS painted layer bake, routing without stock shader, original material preserved, scene restored, out-of-tile UV validation')
