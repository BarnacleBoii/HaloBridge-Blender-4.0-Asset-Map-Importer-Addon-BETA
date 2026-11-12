"""Synthetic catalogue/batch regression; no game files or toolchain required."""
import sys,tempfile,time,threading
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,catalog,blender_ops

def wait(error=False):
    deadline=time.monotonic()+10
    while (ui._task or ui._preview_pending) and time.monotonic()<deadline:
        ui.preview_tick();ui.poll();time.sleep(.01)
    assert not ui._task and not ui._preview_pending
    assert bool(ui._error)==error,ui._error
    ui._error=''

with tempfile.TemporaryDirectory() as tmp:
    s=bpy.context.scene.halo_bridge;s.cache=tmp
    assets=[dict(id=str(i),name='Object '+str(i),level='test',category='Structures',kind='instance',game='halo3',tag='fixture',section=i) for i in range(3)]
    assets.append(dict(id='mat',name='Material',level='test',category='Materials',kind='material',game='halo3',tag='fixture',section=-1))
    file=Path(tmp)/'catalogue.json';catalog.write_json(file,dict(version=1,assets=assets))
    preview=Path(tmp)/'preview.json'
    catalog.write_json(preview,dict(materials=[dict(id=0,name='Synthetic',shader='fixture',alpha='opaque',textures=[])],meshes=[dict(positions=[[0,0,0],[1,0,0],[0,1,0]],uv=[],normals=[],segments=[dict(indices=[0,1,2],material=0)])]))
    ui.load_catalogue();blender_ops.ensure_exporter=lambda:None
    ui.jobs.extract=lambda asset,cfg,cancel:preview
    order=[a.asset_id for a in s.assets]
    # Checks apply to the visible tab/filter, not other checked rows.
    s.search='Object';bpy.ops.halo_bridge.check_assets(check=True)
    assert ui.checked_ids(bpy.context)==['0','1','2']
    s.search='Object 1';bpy.ops.halo_bridge.list_action(action='HIDE')
    assert [a['id'] for a in catalog.read_json(file)['assets'] if a.get('hidden')]==['1']
    assert ui.checked_ids(bpy.context)==[]
    s.search='';s.asset_tab='HIDDEN'
    assert [a.asset_id for a in s.assets if ui.row_visible(s,a)]==['1']
    bpy.ops.halo_bridge.check_assets(check=True);bpy.ops.halo_bridge.list_action(action='UNHIDE')
    s.asset_tab='IMPORTED'
    assert [a.asset_id for a in s.assets]==order
    assert not any(a.hidden for a in s.assets)
    # Reindexing and reopening preserve hidden state and list position.
    bpy.ops.halo_bridge.list_action(action='HIDE',asset_id='2')
    data=catalog.read_json(file);catalog.merge_assets(data,[dict(assets[2])])
    assert next(a for a in data['assets'] if a['id']=='2')['hidden']
    ui.load_catalogue();assert next(a for a in s.assets if a.asset_id=='2').hidden
    bpy.ops.halo_bridge.list_action(action='UNHIDE',asset_id='2')
    for a in s.assets:a.checked=a.asset_id in ('0','1')
    before=set(bpy.context.scene.objects)
    bpy.ops.halo_bridge.place();wait()
    added=[a for a in bpy.context.scene.objects if a not in before]
    assert len(added)==2 and len(bpy.context.selected_objects)==2
    assert (added[0].location-added[1].location).length<1e-6
    assert (added[0].location-bpy.context.scene.cursor.location).length<1e-6
    # Replace the viewport object using the highlighted list entry.
    bpy.ops.object.select_all(action="DESELECT")
    old=added[0];old.select_set(True);bpy.context.view_layer.objects.active=old
    old.location=(3,7,9);bpy.context.view_layer.update()
    matrix=old.matrix_world.copy();identity=old['hb_id']
    s.active_index=2
    bpy.ops.halo_bridge.place(replace_selected=True);wait()
    target=bpy.context.object
    assert target['hb_asset_id']=='2' and target['hb_id']==identity
    assert all(abs(target.matrix_world[r][c]-matrix[r][c])<1e-5 for r in range(4) for c in range(4))
    assert 'materials' in ui.replacement_target(bpy.context,assets[3])[1]
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active=None
    assert '3D View' in ui.replacement_target(bpy.context,assets[0])[1]
    target.select_set(True);bpy.context.view_layer.objects.active=target
    # Batch materials load without changing the selected mesh.
    for a in s.assets:a.checked=a.asset_id=='mat'
    old_slots=list(target.data.materials)
    bpy.ops.halo_bridge.place_checked();wait()
    assert list(target.data.materials)==old_slots and bpy.context.object==target
    # Delete from catalogue must never delete existing placements or caches.
    for a in s.assets:a.checked=a.asset_id in ('0','1')
    count=len(bpy.context.scene.objects)
    bpy.ops.halo_bridge.list_action(action='DELETE')
    assert len(bpy.context.scene.objects)==count and preview.is_file()
    assert [a['id'] for a in catalog.read_json(file)['assets']]==['2','mat']
    assert file.with_name('catalogue.before-list-edit.json').is_file()
    # Dedicated list history restores disk, ordering and checks without scene edits.
    bpy.ops.halo_bridge.list_history()
    assert [a.asset_id for a in s.assets]==order
    assert ui.checked_ids(bpy.context)==['0','1']
    assert len(bpy.context.scene.objects)==count
    bpy.ops.halo_bridge.list_history(redo=True)
    assert [a['id'] for a in catalog.read_json(file)['assets']]==['2','mat']
    bpy.ops.halo_bridge.list_history()
    bpy.ops.halo_bridge.list_action(action='HIDE',asset_id='0')
    assert not ui.history_available(True)
    bpy.ops.halo_bridge.list_history()
    assert not any(a.hidden for a in s.assets)
    bpy.ops.halo_bridge.list_history(redo=True)
    assert next(a for a in s.assets if a.asset_id=='0').hidden
    # Import failure after creating objects rolls back the complete batch.
    catalog.write_json(file,dict(version=1,assets=assets));ui.load_catalogue()
    for a in s.assets:a.checked=a.asset_id in ('0','1')
    original=blender_ops.place
    def broken(asset,path,cfg,location=None):
        obj=original(asset,path,cfg,location)
        if asset['id']=='1':raise RuntimeError('Synthetic importer failure')
        return obj
    blender_ops.place=broken
    count=len(bpy.context.scene.objects)
    bpy.ops.halo_bridge.place_checked();wait(error=True)
    assert len(bpy.context.scene.objects)==count
    blender_ops.place=original
    # Cancellation applies no placements, even if an extractor returns a cache hit.
    gate=threading.Event()
    def delayed(asset,cfg,cancel):
        assert gate.wait(5)
        return preview
    ui.jobs.extract=delayed
    bpy.ops.halo_bridge.place_checked();bpy.ops.halo_bridge.cancel();gate.set();wait(error=True)
    assert len(bpy.context.scene.objects)==count
    # Empty tabs do not preview the last row from another tab.
    s.asset_tab='HIDDEN';assert s.active_index==-1
    bpy.ops.halo_bridge.toggle_preview();wait()
    assert not ui.preview_active(bpy.context)
    bpy.ops.halo_bridge.toggle_preview()
    # Independent categories can exclude materials while retaining every model.
    s.asset_tab='IMPORTED';s.show_materials=False
    assert all(a.kind!='material' for a in s.assets if ui.row_visible(s,a))
    assert len([a for a in s.assets if ui.row_visible(s,a)])==3
    s.show_materials=True
    # Missing texture on one entry does not block successful extractions.
    def partial(asset,cfg,cancel):
        if asset['id']=='1':raise RuntimeError('Texture data not found')
        return preview
    ui.jobs.extract=partial
    for a in s.assets:a.checked=a.asset_id in ('0','1')
    count=len(bpy.context.scene.objects)
    bpy.ops.halo_bridge.place();wait(error=True)
    assert len(bpy.context.scene.objects)==count+1
    assert 'Texture data not found' in bpy.data.texts['HaloBridge diagnostics'].as_string()
    # Materials load without a selected receiving mesh.
    ui.jobs.extract=lambda asset,cfg,cancel:preview
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active=None
    for a in s.assets:a.checked=a.asset_id=='mat'
    bpy.ops.halo_bridge.place();wait()
    assert any(m.get('hb_asset_id')=='mat' for m in bpy.data.materials)
    # Template: terrain plane with the supplied shader, a +sky wall and an unexported Master Chief.
    chief_asset=dict(id='chief',name='masterchief',kind='model',tag='objects\\characters\\masterchief\\masterchief',section=-1)
    made=blender_ops.starter_template(bpy.context,ui.config(bpy.context),preview,chief_asset,preview)
    terrain,sky,chief=made['terrain'],made['sky'],made['chief']
    assert terrain.data.materials[0].node_tree and terrain.data.uv_layers.active and len(terrain.data.polygons)==1
    assert sorted(round(v,3) for uv in terrain.data.uv_layers.active.data for v in uv.uv)==[0.0]*4+[1.0]*4
    assert 'hb_template_note' in terrain  # the texture-less fixture cannot become paintable terrain
    assert sky.data.materials[0].name.startswith('+sky') and len(sky.data.polygons)==6
    assert all((p.center.normalized().dot(p.normal))<0 for p in sky.data.polygons), 'sky wall faces inward'
    assert chief.get('hb_ignore') and chief.name.startswith('Master Chief')
    from halo_bridge import geometry_export
    exported=geometry_export.objects(bpy.context.scene)
    assert terrain in exported and chief not in exported
    assert bpy.context.view_layer.objects.active==terrain
    # Placement now commits atomically as one undo transaction after extraction.
    s.search='';s.asset_tab='IMPORTED'
    for a in s.assets:a.checked=a.kind=='instance'
    before_count=len(bpy.context.scene.objects)
    bpy.ops.halo_bridge.place();wait()
    assert len(bpy.context.scene.objects)==before_count+3
print('PASS: filtered checks, hide/unhide/order/persistence, batch models/materials, replacement, catalogue-only deletion, failure rollback and cancellation')
