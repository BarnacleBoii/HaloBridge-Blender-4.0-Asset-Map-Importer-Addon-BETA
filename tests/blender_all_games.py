"""Assets from every game in a Halo 3 level: which materials convert, recorded-texture fallback,
index sky models, overlapping collision detection and Halo CE / Halo 2 registration (no game data)."""
import json,sys,tempfile
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import cross_game,games,geometry_export,compat
from halo_bridge.catalog import GAME_FOLDERS,MAP_FOLDERS

# Halo CE and Halo 2 import from MCC maps; only Halo 3 / ODST are Sapien destinations.
for key in ('halo1','halo2'):
    assert games.GAMES[key]['import_enabled'] and not games.GAMES[key]['sapien_enabled'] and key in GAME_FOLDERS
assert MAP_FOLDERS['halo2']=='halo2/h2_maps_win64_dx11'
assert {k for k,*_ in games.IMPORT_ITEMS}>={'halo3','odst','reach','halo1','halo2'}
assert {k for k,*_ in games.SAPIEN_ITEMS if 'not available' not in _[0]}=={'halo3','odst'}

for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.mesh.primitive_plane_add(size=100);obj=bpy.context.object
mat=bpy.data.materials.new('fixture');compat.enable_nodes(mat);obj.data.materials.append(mat)

# Every source game other than the destination converts; hand-made materials and assigned kit shaders do not.
for game in ('odst','reach','halo1','halo2'):
    obj['hb_game']=game
    assert games.needs_conversion(obj,mat,'halo3'),game
obj['hb_game']='halo3';assert not games.needs_conversion(obj,mat,'halo3')
assert games.needs_conversion(obj,mat,'odst'), 'Halo 3 assets convert in an ODST level unless the kit has the shader'
del obj['hb_game'];assert not games.needs_conversion(obj,mat,'halo3')
obj['hb_game']='halo2';mat['hb_shader_game']='halo3';assert not games.needs_conversion(obj,mat,'halo3')
del mat['hb_shader_game']
assert games.shares_tags('odst','halo3') and not games.shares_tags('reach','halo3')

with tempfile.TemporaryDirectory() as tmp:
    # ODST shader that already exists in the destination kit is reused, not converted.
    kit=Path(tmp)/'kit';(kit/'tags/levels/shared').mkdir(parents=True)
    (kit/'tags/levels/shared/metal.shader').write_bytes(b'')
    obj['hb_game']='odst';mat['hb_shader']='levels\\shared\\metal'
    assert not cross_game.converts(obj,mat,{'game':'halo3','kit':str(kit)})
    mat['hb_shader']='levels\\atlas\\only_in_odst'
    assert cross_game.converts(obj,mat,{'game':'halo3','kit':str(kit)})
    obj['hb_game']='reach';mat['hb_shader']='levels\\shared\\metal'
    assert cross_game.converts(obj,mat,{'game':'halo3','kit':str(kit)}), 'Reach tag paths are never assumed compatible'

    # Layered previews (unsupported nodes) fall back to the textures recorded at import.
    image=bpy.data.images.new('diffuse',4,4,alpha=True);image.filepath_raw=str(Path(tmp)/'texture_1.png');image.file_format='PNG';image.save()
    normal=bpy.data.images.new('normal',4,4);normal.filepath_raw=str(Path(tmp)/'texture_2.png');normal.file_format='PNG';normal.save()
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    mix=mat.node_tree.nodes.new('ShaderNodeMix');mix.data_type='RGBA'
    mat.node_tree.links.new(mix.outputs['Result'],bsdf.inputs['Base Color'])
    try:cross_game.texture(bsdf.inputs['Base Color']);raise AssertionError('mix node should be unsupported')
    except ValueError:pass
    mat['hb_texture_sources']=json.dumps([{'usage':'diffuse','path':'texture_1.png','tiling':[2,3]},{'usage':'normal','path':'texture_2.png','tiling':[1,1]}])
    mat['hb_texture_directory']=tmp
    base,norm,alpha,_=cross_game.sources(mat)
    assert base[2]==(2.,3.) and base[1] is None and norm[0].colorspace_settings.name=='Non-Color' and alpha is None
    compat.set_alpha(mat,'clip')
    assert cross_game.sources(mat)[2][1]==3, 'cutout alpha uses the diffuse alpha when no transparency map exists'
    result=cross_game.prepare([obj],Path(tmp)/'out',materials={mat.as_pointer():mat})
    entry=result[mat.as_pointer()]
    assert entry['tiling']==(2.,3.) and set(entry['maps'])=={'base_map','normal_map','alpha_map'}

# Sky models placed from an index are omitted like imported skies.
obj['hb_kind']='model';obj['hb_source_tag']='sky\\mp clear afternoon\\mp clear afternoon'
assert geometry_export.is_sky(obj)
obj['hb_source_tag']='scenarios\\skies\\multi\\ascension\\ascension';assert geometry_export.is_sky(obj)
obj['hb_source_tag']='scenery\\rocks\\boulder\\boulder';assert not geometry_export.is_sky(obj)

# Two cubes that touch along an edge weld into edges shared by more than two faces.
cube=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
assert not geometry_export.ambiguous_collision(cube,faces)
shifted=[(x+1,y+1,z) for x,y,z in cube]
assert geometry_export.ambiguous_collision(cube+shifted,faces+[tuple(i+8 for i in f) for f in faces])
# Halo CE / Halo 2 .scenario import: the kit's Tool builds a map; a map already in the kit's output folder is put back.
from halo_bridge import classic_scenario,sky_export,skies,jobs
for key in ('halo1','halo2'):assert games.GAMES[key]['scenario_enabled'] and games.GAMES[key]['classic']
with tempfile.TemporaryDirectory() as tmp:
    kit=Path(tmp)/'H2EK';(kit/'tags/scenarios/multi/test').mkdir(parents=True);(kit/'tags/scenarios/ui/mainmenu').mkdir(parents=True)
    (kit/'tags/scenarios/multi/test/test.scenario').write_bytes(b'v1');(kit/'tags/scenarios/ui/mainmenu/mainmenu.scenario').write_bytes(b'')
    assert classic_scenario.scenarios(kit)==['scenarios\\multi\\test\\test'], 'UI and shared scenarios are not levels'
    out=kit/'h2_maps_win64_dx11';out.mkdir();(out/'test.map').write_bytes(b'users own map')
    calls=[]
    def fake_tool(args,log,cwd=None,cancel=None,**kw):
        calls.append([str(a) for a in args]);(Path(cwd)/'h2_maps_win64_dx11'/'test.map').write_bytes(b'built');return ''
    original=classic_scenario.run_process;classic_scenario.run_process=fake_tool
    (kit/'tool.exe').write_bytes(b'')
    try:
        cfg=dict(game='halo2',kit=str(kit),cache=str(Path(tmp)/'cache'))
        built=classic_scenario.build_map(cfg,'scenarios\\multi\\test\\test')
        assert built.read_bytes()==b'built' and (out/'test.map').read_bytes()==b'users own map'
        assert calls[0][1:]==['-batch','build-cache-file','scenarios\\multi\\test\\test','win64']
        assert classic_scenario.build_map(cfg,'scenarios\\multi\\test\\test')==built and len(calls)==1, 'unchanged tags reuse the built map'
        (kit/'tags/scenarios/multi/test/test.scenario').write_bytes(b'v2 changed')
        classic_scenario.build_map(cfg,'scenarios\\multi\\test\\test');assert len(calls)==2, 'edited tags rebuild the map'
    finally:classic_scenario.run_process=original
    rows=classic_scenario.mark_rows([dict(id='a',level='test',map=str(built))],'scenarios\\multi\\test\\test')
    assert rows[0]['source']=='scenario' and rows[0]['map'], 'kit-built rows list as .scenario assets but extract from their map'

# Skies from any game: sky models are recognised by folder; scenes that never chose a sky game use the destination's kit skies.
assert sky_export.is_sky_asset(dict(kind='model',tag='sky\\sky_timberland\\sky_timberland'))
assert sky_export.is_sky_asset(dict(kind='scenery',tag='levels\\multi\\forge_halo\\sky\\sky'))
assert not sky_export.is_sky_asset(dict(kind='material',tag='sky\\x\\y')) and not sky_export.is_sky_asset(dict(kind='model',tag='scenery\\rocks\\boulder'))
import halo_bridge
halo_bridge.register()
s=bpy.context.scene.halo_bridge
if 'sky_game' in s:del s['sky_game']
s.export_target='odst';s.game='odst'
assert skies.sky_game(s)=='odst' and skies.kit_sky(s)
s.sky_game='halo1';assert skies.sky_game(s)=='halo1' and not skies.kit_sky(s)
s.export_target='halo3';s.game='halo3';s.sky_game='halo3';assert skies.kit_sky(s)
print('PASS every game converts into Halo 3, ODST shader reuse, recorded-texture fallback, index skies, overlapping collision, Halo CE/2 registration')
