"""Original-map import tests with synthetic geometry and known world matrices."""
import sys,tempfile,time
from pathlib import Path
import bpy
from mathutils import Matrix,Euler,Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,catalog,map_scene,navigation

def wait(error=False):
    deadline=time.monotonic()+10
    while ui._task and time.monotonic()<deadline:
        ui.poll();time.sleep(.01)
    assert not ui._task
    assert bool(ui._error)==error,ui._error
    ui._error=''

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);manifest=root/'scene.json';mesh=root/'mesh.json'
    catalog.write_json(mesh,dict(materials=[],meshes=[dict(positions=[[0,0,0],[1,0,0],[0,1,0]],normals=[],uv=[],segments=[dict(material=-1,indices=[0,1,2])])]))
    matrix=Matrix.LocRotScale(Vector((12,-7,3)),Euler((.3,.4,.8)).to_quaternion(),Vector((2,2,2)))
    placements=[dict(name='Terrain',mesh='shared',group='Terrain',matrix=[list(row) for row in Matrix.Identity(4)]),
                dict(name='Instance',mesh='shared',group='BSP instances',matrix=[list(row) for row in matrix.transposed()])]
    catalog.write_json(manifest,dict(version=1,kind='halo3_map_scene',matrix_convention='row_vector',scenario='levels/test/test',meshes={'shared':'mesh.json'},placements=placements,
        expected_bsps=1,decoded_bsps=1,counts={'Terrain':1,'BSP instances':1},warnings=['Synthetic omission'],limitations=['Synthetic reference scene']))
    ui.jobs.extract_map_scene=lambda cfg,name,cancel,progress:manifest
    bpy.context.scene.halo_bridge.cache=tmp
    bpy.context.scene.cursor.location=(900,800,700)
    bpy.ops.halo_bridge.import_map_scene();wait()
    bpy.context.view_layer.update()
    refs=[o for o in bpy.context.scene.objects if o.get('hb_map_reference')]
    assert len(refs)==2 and refs[0].data==refs[1].data
    obj=next(o for o in refs if o['hb_map_placement_index']==1)
    expected=Matrix.Scale(100,4)@matrix@Matrix.Translation(Vector((.5,.5,0)))
    assert max(abs(obj.matrix_world[r][c]-expected[r][c]) for r in range(4) for c in range(4))<.001
    for original,vertex in zip(((0,0,0),(1,0,0),(0,1,0)),obj.data.vertices):
        assert (obj.matrix_world@vertex.co-100*(matrix@Vector(original))).length<.001
    for axis in range(3):assert abs(min(v.co[axis] for v in obj.data.vertices)+max(v.co[axis] for v in obj.data.vertices))<1e-6
    assert all(o.get('hb_ignore') for o in refs)
    assert 'Synthetic omission' in bpy.data.texts['HaloBridge map import report'].as_string()
    # The old whole-map invocation must now route to original-layout import.
    bpy.ops.halo_bridge.place_checked(entire_map=True);wait()
    assert len([o for o in bpy.context.scene.objects if o.get('hb_map_reference')])==4
    # New imports reuse centered data without shifting it a second time.
    assert len({o.data.as_pointer() for o in bpy.context.scene.objects if o.get('hb_map_reference')})==1
    old_objects=set(bpy.context.scene.objects);old_collections=set(bpy.data.collections)
    bpy.ops.halo_bridge.import_map_scene()
    ui._task.application_budget=0  # Deliberately pause mid-import to exercise rollback.
    deadline=time.monotonic()+5
    while ui._task and not hasattr(ui._task,'application') and time.monotonic()<deadline:
        ui.poll();time.sleep(.01)
    assert ui._task and hasattr(ui._task,'application')
    bpy.ops.halo_bridge.cancel();wait(error=True)
    assert set(bpy.context.scene.objects)==old_objects and set(bpy.data.collections)==old_collections

    # Repair an old shared mesh without moving either instance or an unrelated user.
    legacy=bpy.data.meshes.new('old map mesh');legacy.from_pydata([(10,20,30),(12,20,30),(10,24,30)],[],[(0,1,2)])
    repairs=[]
    for i in range(3):
        item=bpy.data.objects.new('old instance',legacy);bpy.context.collection.objects.link(item)
        item.matrix_world=matrix@Matrix.Translation((i*5,0,0));item['hb_map_reference']=i<2;repairs.append(item)
    bpy.context.view_layer.update()
    points={o:[o.matrix_world@v.co for v in o.data.vertices] for o in repairs}
    assert map_scene.center_existing_origins(bpy.context)==sum(o.type=='MESH' for o in bpy.context.scene.objects)
    bpy.context.view_layer.update()
    for o in repairs:
        assert all((o.matrix_world@v.co-p).length<1e-4 for v,p in zip(o.data.vertices,points[o]))
    assert repairs[0].data==repairs[1].data and repairs[2].data==legacy
    assert map_scene.center_existing_origins(bpy.context)==sum(o.type=='MESH' for o in bpy.context.scene.objects)
    # Reveal is triggered only on active selection changes; toggle suppresses it.
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    navigation.reveal_active(bpy.context.window)
    calls=[];original_reveal=navigation.reveal_active
    navigation.reveal_active=lambda window:calls.append(window)
    navigation._last.clear();navigation.follow_selection();navigation.follow_selection()
    assert len(calls)==1
    bpy.context.scene.halo_bridge.follow_outliner=False
    bpy.context.view_layer.objects.active=repairs[0];repairs[0].select_set(True)
    navigation.follow_selection();assert len(calls)==1
    bpy.context.scene.halo_bridge.follow_outliner=True
    navigation.follow_selection();assert len(calls)==2
    navigation.reveal_active=original_reveal
print('PASS: map layout matrices, scale/rotation, cursor independence, shared meshes, separate collections, report, legacy routing and cancellation rollback')
