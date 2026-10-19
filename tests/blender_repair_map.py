"""Repair a partial import while retaining edits and intentional deletions."""
import sys,tempfile
from pathlib import Path
import bpy
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import map_scene,catalog
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);mesh=dict(materials=[],meshes=[dict(positions=[[0,0,0],[1,0,0],[0,1,0]],normals=[],uv=[],segments=[dict(material=-1,indices=[0,1,2])])])
    rows=[dict(name=name,mesh='shared',group='Terrain',source_tag='fixture',matrix=[list(r) for r in Matrix.Identity(4)]) for name in ('edited','deleted','recovered')]
    for folder,count,decoded in [('old',2,1),('new',3,2)]:
        catalog.write_json(root/folder/'mesh.json',mesh)
        catalog.write_json(root/folder/'scene.json',dict(kind='halo3_map_scene',matrix_convention='row_vector',scenario='fixture',meshes={'shared':'mesh.json'},placements=rows[:count],decoded_bsps=decoded,expected_bsps=2))
    for _ in map_scene.import_scene(bpy.context,root/'old/scene.json'):pass
    edited=bpy.data.objects['edited'];edited.data.vertices[0].co.x=9;edited.location.x+=100
    bpy.data.objects.remove(bpy.data.objects['deleted'],do_unlink=True)
    for _ in map_scene.repair_scene(bpy.context,root/'new/scene.json'):pass
    assert bpy.data.objects.get('deleted') is None
    assert bpy.data.objects.get('recovered') is not None
    assert edited.data.vertices[0].co.x==9 and edited.location.x==150
    assert edited['hb_map_manifest']==str(root/'new/scene.json')
print('PASS repair adds newly recovered rows while retaining edits and deletions')
