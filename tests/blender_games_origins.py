"""Scene-wide native origins and persistent, isolated game profiles."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,map_scene
for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
mesh=bpy.data.meshes.new('offset')
mesh.from_pydata([(0,0,0),(6,0,0),(0,3,0)],[],[(0,1,2)])
mesh['hb_origin_center']=[0,0,0] # Already centered metadata must not skip edits.
a=bpy.data.objects.new('authored',mesh);bpy.context.collection.objects.link(a)
b=bpy.data.objects.new('shared_hidden',mesh);bpy.context.collection.objects.link(b)
b.location=(20,0,0);b.hide_set(True)
a.select_set(True);bpy.context.view_layer.objects.active=a
bpy.context.view_layer.update()
world={o.name:[o.matrix_world@v.co for v in o.data.vertices] for o in (a,b)}
assert map_scene.center_existing_origins(bpy.context)==2
bpy.context.view_layer.update()
for o in (a,b):
    for v,expected in zip(o.data.vertices,world[o.name]):assert (o.matrix_world@v.co-expected).length<1e-5,(o.name,'geometry moved')
    center=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
    assert center.length<1e-5,(o.name,'not median geometry origin',center)
assert bpy.context.active_object==a and a.select_get() and b.hide_get()
s=bpy.context.scene.halo_bridge
import tempfile
from unittest.mock import patch
with tempfile.TemporaryDirectory() as temp:
    s.kit='original_h3_kit';s.maps='original_h3_maps';s.cache=temp;s.map_name='custom.map'
    with patch.object(ui,'detect_paths',return_value=dict(kit='fixture/HREK',maps='fixture/haloreach/maps',cache=temp+'/reach')):
        s.game='reach'
    assert s.kit.endswith('HREK') and 'haloreach' in s.maps
    assert s.cache!=temp and not s.assets
    s.map_name='reach_custom.map'
    s.game='halo3'
    assert (s.kit,s.maps,s.cache,s.map_name)==('original_h3_kit','original_h3_maps',temp,'custom.map')
    s.game='reach';assert s.map_name=='reach_custom.map'
print('PASS all-mesh median origins, shared/hidden meshes, world positions and game folder round trip')
