"""Readable names retain material reuse, shader references, files and conversion identity."""
import sys,tempfile,hashlib
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import blender_ops,source_names
from halo_bridge.catalog import stable_id,write_json
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);path=folder/'texture_42.png'
    image=bpy.data.images.new('texture_42.png',width=2,height=2);image.filepath_raw=str(path);image.file_format='PNG';image.save()
    bpy.data.images.remove(image)
    meta=dict(id=3,name='round_cover_metal',shader=r'levels\solo\070_waste\shaders\round_cover_metal',alpha='opaque',textures=[dict(name=r'levels\solo\070_waste\bitmaps\round_cover_diffuse',usage='diffuse',path=path.name,tiling=[1,1])])
    mat=blender_ops.material(meta,folder)
    assert mat.name=='round_cover_metal'
    tex=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE');image=tex.image
    assert image.name=='round_cover_diffuse' and Path(image.filepath)==path
    assert blender_ops.material(meta,folder)==mat
    # Simulate an old saved blend with hash and numeric names, then migrate in place.
    key='hb_'+stable_id(meta['shader'],str(folder),meta['id'])
    mat.name=key;del mat['hb_material_key'];del mat['hb_conversion_id']
    image.name='texture_42.png';del image['hb_source_texture']
    write_json(folder/'texture_names.json',dict(textures={'42':r'levels\solo\070_waste\bitmaps\round_cover_diffuse'}))
    before=hashlib.sha256((mat.name+'|'+mat['hb_shader']).encode()).hexdigest()
    count,_=source_names.restore()
    assert count==2 and mat.name=='round_cover_metal' and tex.image==image
    assert mat['hb_shader']==meta['shader'] and image.name=='round_cover_diffuse'
    assert hashlib.sha256((mat['hb_conversion_id']+'|'+mat['hb_shader']).encode()).hexdigest()==before
    assert blender_ops.material(meta,folder)==mat
    # Same readable name, different source: distinct datablock, no accidental merging.
    other=blender_ops.material(dict(meta,id=4,shader='another/source'),folder)
    assert other!=mat and other.name.startswith('round_cover_metal.')
    mat.name='My custom name';source_names.restore();assert mat.name=='My custom name'
print('PASS source names, old blend migration, shared material reuse, name collisions and shader/cache/conversion identity')
